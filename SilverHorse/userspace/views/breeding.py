from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from ..models import Horse, BreedingOffer
import random

@login_required
def breeding_market(request):
    offers = BreedingOffer.objects.filter(is_active=True).select_related('horse', 'owner')
    # Filtering (similar to market)
    breeds = Horse.objects.filter(breeding_offers__is_active=True).values_list('breed', flat=True).distinct().order_by('breed')
    horse_types = Horse.TYPE_CHOICES
    return render(request, 'userspace/market/breeding_market.html', {
        'offers': offers,
        'breeds': breeds,
        'horse_types': horse_types,
    })

@login_required
def create_breeding_offer(request):
    # Get user's horses that are eligible for breeding (age >= 36, status='user', not pregnant if female)
    user_horses = Horse.objects.filter(owner=request.user, status='user', age__gte=36)
    # Exclude pregnant mares
    user_horses = user_horses.exclude(gender='F', is_pregnant=True)
    # Exclude horses already on active offer
    active_offers = BreedingOffer.objects.filter(owner=request.user, is_active=True).values_list('horse_id', flat=True)
    user_horses = user_horses.exclude(id__in=active_offers)

    if request.method == 'POST':
        horse_id = request.POST.get('horse')
        price = int(request.POST.get('price', 0))
        currency = request.POST.get('currency', 'horseshoes')
        max_uses = request.POST.get('max_uses')
        if max_uses:
            try:
                max_uses = int(max_uses)
                if max_uses <= 0:
                    messages.error(request, "Кількість використань має бути більше 0.")
                    return redirect('create_breeding_offer')
            except ValueError:
                messages.error(request, "Невірне значення кількості використань.")
                return redirect('create_breeding_offer')
        else:
            max_uses = None

        horse = get_object_or_404(Horse, id=horse_id, owner=request.user)

        # Validation
        if horse.age < 36:
            messages.error(request, "Кінь занадто молодий для парування.")
            return redirect('create_breeding_offer')
        if horse.gender == 'F' and horse.is_pregnant:
            messages.error(request, "Вагітна кобила не може бути виставлена для парування.")
            return redirect('create_breeding_offer')
        if BreedingOffer.objects.filter(horse=horse, is_active=True).exists():
            messages.error(request, "Цей кінь вже виставлений на парування.")
            return redirect('create_breeding_offer')
        if price <= 0:
            messages.error(request, "Ціна має бути більше 0.")
            return redirect('create_breeding_offer')

        BreedingOffer.objects.create(
            horse=horse,
            owner=request.user,
            price=price,
            currency=currency,
            is_active=True,
            max_uses=max_uses,
            remaining_uses=max_uses
        )
        messages.success(request, f"{horse.name} виставлений для парування.")
        return redirect('breeding_market')

    return render(request, 'userspace/market/create_breeding_offer.html', {
        'user_horses': user_horses,
    })

@login_required
def purchase_breeding(request, offer_id):
    offer = get_object_or_404(BreedingOffer, id=offer_id, is_active=True)
    # Ensure buyer is not the owner
    if offer.owner == request.user:
        messages.error(request, "Ви не можете купити парування у самого себе.")
        return redirect('breeding_market')

    # Get buyer's eligible horses (opposite gender, age>=36, not pregnant if mare)
    opposite_gender = 'F' if offer.horse.gender == 'M' else 'M'
    buyer_horses = Horse.objects.filter(
        owner=request.user,
        status='user',
        gender=opposite_gender,
        age__gte=36
    )
    if opposite_gender == 'F':
        buyer_horses = buyer_horses.exclude(is_pregnant=True)

    if request.method == 'POST':
        buyer_horse_id = request.POST.get('buyer_horse')
        buyer_horse = get_object_or_404(Horse, id=buyer_horse_id, owner=request.user)

        # Check eligibility again
        if buyer_horse.gender != opposite_gender:
            messages.error(request, "Неправильна стать коня.")
            return redirect('purchase_breeding', offer_id=offer.id)
        if buyer_horse.age < 36:
            messages.error(request, "Ваш кінь занадто молодий для розмноження.")
            return redirect('purchase_breeding', offer_id=offer.id)
        if buyer_horse.gender == 'F' and buyer_horse.is_pregnant:
            messages.error(request, "Ваша кобила вагітна.")
            return redirect('purchase_breeding', offer_id=offer.id)

        # Payment
        buyer_profile = request.user.profile
        seller_profile = offer.owner.profile
        if offer.currency == 'horseshoes':
            if buyer_profile.horseshoes < offer.price:
                messages.error(request, "Недостатньо підков.")
                return redirect('purchase_breeding', offer_id=offer.id)
            buyer_profile.horseshoes -= offer.price
            seller_profile.horseshoes += offer.price
        else:  # silver_wings
            if buyer_profile.silver_wings < offer.price:
                messages.error(request, "Недостатньо срібних пір'їн.")
                return redirect('purchase_breeding', offer_id=offer.id)
            buyer_profile.silver_wings -= offer.price
            seller_profile.silver_wings += offer.price
        buyer_profile.save()
        seller_profile.save()

        # Determine mother and father for inheritance
        mother = buyer_horse if buyer_horse.gender == 'F' else offer.horse
        father = offer.horse if mother == buyer_horse else buyer_horse

        # Check that mother is not already pregnant (should be already filtered, but just in case)
        if mother.is_pregnant:
            messages.error(request, "Мати вже вагітна.")
            return redirect('purchase_breeding', offer_id=offer.id)

        # Set pregnancy for the mother
        mother.is_pregnant = True
        mother.sire = father
        mother.pregnancy_due_age = mother.age + 12  # foal will be born after 12 months
        mother.save()

        # Update the breeding offer (decrement remaining uses if limited)
        if offer.remaining_uses is not None:
            offer.remaining_uses -= 1
            if offer.remaining_uses <= 0:
                offer.is_active = False
        # For unlimited, leave as active
        offer.save()

        messages.success(request, f"Кобила {mother.name} запліднена! Вона народить лоша через 12 місяців.")
        return redirect('horse_detail', horse_id=mother.id)

    return render(request, 'userspace/market/purchase_breeding.html', {
        'offer': offer,
        'buyer_horses': buyer_horses,
    })

@login_required
def cancel_breeding_offer(request, offer_id):
    offer = get_object_or_404(BreedingOffer, id=offer_id, owner=request.user, is_active=True)
    if request.method == 'POST':
        offer.is_active = False
        offer.save()
        messages.success(request, "Пропозицію скасовано.")
    return redirect('breeding_market')