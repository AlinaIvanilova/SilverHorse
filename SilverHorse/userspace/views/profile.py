from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.db.models import Sum
from ..models import Horse, EquestrianComplex, ComplexResource, Auction, BreedingOffer


@login_required
def account_page(request):
    user = request.user

    # Обробка зміни email
    if request.method == 'POST' and 'change_email' in request.POST:
        new_email = request.POST.get('email', '').strip()
        if new_email and new_email != user.email:
            if User.objects.filter(email=new_email).exists():
                messages.error(request, "Цей email вже використовується іншим користувачем.")
            else:
                user.email = new_email
                user.save()
                messages.success(request, "Email успішно змінено.")
        else:
            messages.error(request, "Новий email не може бути порожнім або таким самим.")
        return redirect('account_page')

    # Обробка зміни пароля
    password_form = PasswordChangeForm(user)
    if request.method == 'POST' and 'change_password' in request.POST:
        password_form = PasswordChangeForm(user, request.POST)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Пароль успішно змінено.")
            return redirect('account_page')
        else:
            messages.error(request, "Будь ласка, виправте помилки у формі.")

    context = {
        'user': user,
        'password_form': password_form,
    }
    return render(request, 'userspace/user/account.html', context)


@login_required
def profile_page(request):
    user = request.user
    profile = user.profile

    # ---- Коні ----
    user_horses = Horse.objects.filter(owner=user, status='user')
    horses_count = user_horses.count()
    total_wins = user_horses.aggregate(total=Sum('wins'))['total'] or 0

    # Найкращий кінь за перемогами
    best_horse = user_horses.order_by('-wins').first()
    if best_horse:
        best_horse_name = best_horse.name
        best_horse_wins = best_horse.wins
    else:
        best_horse_name = "—"
        best_horse_wins = 0

    # ---- Комплекс ----
    complex_obj = EquestrianComplex.objects.filter(owner=user).first()
    if complex_obj:
        complex_name = complex_obj.name
        complex_location = complex_obj.get_location_display()
        complex_prestige = complex_obj.prestige
        total_resources = ComplexResource.objects.filter(complex=complex_obj).aggregate(
            total=Sum('quantity')
        )['total'] or 0
        resource_types_count = ComplexResource.objects.filter(complex=complex_obj).count()
    else:
        complex_name = "Не створено"
        complex_location = "—"
        complex_prestige = 0
        total_resources = 0
        resource_types_count = 0

    # ---- Активність ----
    active_auctions = Auction.objects.filter(seller=user, is_active=True).count()
    active_breeding_offers = BreedingOffer.objects.filter(owner=user, is_active=True).count()

    # ---- Дата реєстрації ----
    registered_since = profile.created_at

    context = {
        'user': user,
        'profile': profile,
        'horses_count': horses_count,
        'total_wins': total_wins,
        'best_horse_name': best_horse_name,
        'best_horse_wins': best_horse_wins,
        'complex_name': complex_name,
        'complex_location': complex_location,
        'complex_prestige': complex_prestige,
        'total_resources': total_resources,
        'resource_types_count': resource_types_count,
        'active_auctions': active_auctions,
        'active_breeding_offers': active_breeding_offers,
        'registered_since': registered_since,
    }
    return render(request, 'userspace/user/profile.html', context)