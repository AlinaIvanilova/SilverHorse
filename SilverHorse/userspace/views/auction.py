from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from ..models import Horse, Auction
from django.contrib.auth.models import User


@login_required
def auction_list(request):
    # Показуємо тільки активні аукціони, що не закінчились
    active_auctions = Auction.objects.filter(
        is_active=True,
        end_time__gt=timezone.now()
    ).order_by('end_time')

    # Отримуємо унікальні породи з коней, що на аукціоні
    breeds = Horse.objects.filter(
        auction__in=active_auctions
    ).values_list('breed', flat=True).distinct().order_by('breed')

    horse_types = Horse.TYPE_CHOICES

    return render(request, 'userspace/auction_list.html', {
        'auctions': active_auctions,
        'breeds': breeds,
        'horse_types': horse_types,
    })

@login_required
def auction_detail(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)

    # Якщо аукціон закінчився, але ще активний – завершити
    if auction.is_active and timezone.now() > auction.end_time:
        finalize_auction(auction)
        messages.info(request, 'Аукціон завершено.')
        return redirect('auction_list')  # Перенаправляємо на список, оскільки аукціон видалено

    return render(request, 'userspace/auction_detail.html', {
        'auction': auction
    })

@login_required
def create_auction(request):
    user_horses = Horse.objects.filter(owner=request.user, status='user')

    if request.method == 'POST':
        horse_id = request.POST.get('horse')
        starting_price = int(request.POST.get('starting_price'))
        currency = request.POST.get('currency')

        horse = get_object_or_404(Horse, id=horse_id, owner=request.user)

        # Видаляємо будь-який існуючий аукціон для цього коня (на випадок "завислих" записів)
        Auction.objects.filter(horse=horse).delete()

        # Встановлюємо початковий час завершення – 50 годин
        end_time = timezone.now() + timezone.timedelta(hours=50)

        with transaction.atomic():
            auction = Auction.objects.create(
                horse=horse,
                seller=request.user,
                end_time=end_time,
                starting_price=starting_price,
                current_bid=starting_price,
                current_bidder=None,
                currency=currency,
                is_active=True
            )
            horse.status = 'auction'
            horse.save()

        messages.success(request, f'Аукціон для коня {horse.name} створено!')
        return redirect('auction_detail', auction_id=auction.id)

    return render(request, 'userspace/create_auction.html', {
        'user_horses': user_horses
    })

@login_required
def place_bid(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id, is_active=True)

    # Перевірка закінчення часу
    if timezone.now() > auction.end_time:
        finalize_auction(auction)
        messages.warning(request, 'Аукціон вже завершено.')
        return redirect('auction_list')  # Перенаправляємо на список

    # Власник не може ставити
    if request.user == auction.seller:
        messages.error(request, 'Ви не можете робити ставку на власного коня.')
        return redirect('auction_detail', auction_id=auction.id)

    if request.method == 'POST':
        bid_amount = int(request.POST.get('bid_amount'))
        profile = request.user.profile

        # Ставка має бути вищою
        if bid_amount <= auction.current_bid:
            messages.error(request, 'Ставка має бути вищою за поточну.')
            return redirect('auction_detail', auction_id=auction.id)

        # Перевірка доступного балансу у відповідній валюті
        if auction.currency == 'horseshoes':
            available = profile.horseshoes - profile.reserved_horseshoes
        else:  # silver_wings
            available = profile.silver_wings - profile.reserved_silver_wings

        if available < bid_amount:
            messages.error(request, f'Недостатньо вільних {auction.get_currency_display()}.')
            return redirect('auction_detail', auction_id=auction.id)

        with transaction.atomic():
            # Звільняємо резерв попереднього лідера
            if auction.current_bidder:
                prev_profile = auction.current_bidder.profile
                if auction.currency == 'horseshoes':
                    prev_profile.reserved_horseshoes -= auction.current_bid
                else:
                    prev_profile.reserved_silver_wings -= auction.current_bid
                prev_profile.save()

            # Резервуємо нову ставку
            if auction.currency == 'horseshoes':
                profile.reserved_horseshoes += bid_amount
            else:
                profile.reserved_silver_wings += bid_amount
            profile.save()

            # Оновлюємо аукціон: нова ставка, новий лідер, час подовжується на 15 хв
            auction.current_bid = bid_amount
            auction.current_bidder = request.user
            auction.end_time = timezone.now() + timezone.timedelta(minutes=15)
            auction.save()

        messages.success(request, 'Ваша ставка прийнята!')
        return redirect('auction_detail', auction_id=auction.id)

    return redirect('auction_detail', auction_id=auction.id)

@login_required
def cancel_auction(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id, is_active=True)

    # Тільки продавець може скасувати
    if request.user != auction.seller:
        messages.error(request, 'Ви не можете скасувати цей аукціон.')
        return redirect('auction_detail', auction_id=auction.id)

    with transaction.atomic():
        # Повертаємо резерв поточному лідеру (якщо є)
        if auction.current_bidder:
            bidder_profile = auction.current_bidder.profile
            if auction.currency == 'horseshoes':
                bidder_profile.reserved_horseshoes -= auction.current_bid
            else:
                bidder_profile.reserved_silver_wings -= auction.current_bid
            bidder_profile.save()

        # Повертаємо коня власнику
        horse = auction.horse
        horse.status = 'user'
        horse.save()

        # Видаляємо запис аукціону
        auction.delete()

    messages.success(request, 'Аукціон скасовано. Кінь повернутий до вашої стайні.')
    return redirect('horses_page')

def finalize_auction(auction):
    if not auction.is_active:
        return

    with transaction.atomic():
        horse = auction.horse
        currency = auction.currency

        if auction.current_bidder:
            winner = auction.current_bidder
            winner_profile = winner.profile
            seller_profile = auction.seller.profile

            if currency == 'horseshoes':
                winner_profile.horseshoes -= auction.current_bid
                winner_profile.reserved_horseshoes -= auction.current_bid
                seller_profile.horseshoes += auction.current_bid
            else:  # silver_wings
                winner_profile.silver_wings -= auction.current_bid
                winner_profile.reserved_silver_wings -= auction.current_bid
                seller_profile.silver_wings += auction.current_bid

            winner_profile.save()
            seller_profile.save()

            # Передача коня
            horse.owner = winner
            horse.status = 'user'
            horse.save()
        else:
            # Ставок не було – повертаємо коня власнику
            horse.status = 'user'
            horse.save()

        # Видаляємо запис аукціону
        auction.delete()