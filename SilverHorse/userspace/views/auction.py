from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from ..models import Horse, Auction
from django.contrib.auth.models import User

@login_required
def auction_list(request):
    # Активні аукціони, що ще не закінчились
    active_auctions = Auction.objects.filter(
        is_active=True,
        end_time__gt=timezone.now()
    ).order_by('end_time')
    return render(request, 'userspace/auction_list.html', {
        'auctions': active_auctions
    })

@login_required
def auction_detail(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)

    # Якщо аукціон закінчився, але ще активний – завершити його
    if auction.is_active and timezone.now() > auction.end_time:
        finalize_auction(auction)

    return render(request, 'userspace/auction_detail.html', {
        'auction': auction
    })

@login_required
def create_auction(request):
    # Користувач може виставити тільки своїх коней зі статусом 'user'
    user_horses = Horse.objects.filter(owner=request.user, status='user')

    if request.method == 'POST':
        horse_id = request.POST.get('horse')
        duration = int(request.POST.get('duration'))  # хвилини
        starting_price = int(request.POST.get('starting_price'))

        horse = get_object_or_404(Horse, id=horse_id, owner=request.user)

        # Перевірка, чи кінь вже не на аукціоні
        if hasattr(horse, 'auction') and horse.auction.is_active:
            messages.error(request, 'Цей кінь вже на аукціоні.')
            return redirect('create_auction')

        # Розрахунок часу завершення
        end_time = timezone.now() + timezone.timedelta(minutes=duration)

        # Створення аукціону
        with transaction.atomic():
            auction = Auction.objects.create(
                horse=horse,
                seller=request.user,
                end_time=end_time,
                starting_price=starting_price,
                current_bid=starting_price,
                current_bidder=None,
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

    # Перевірка, чи не закінчився час
    if timezone.now() > auction.end_time:
        finalize_auction(auction)
        messages.warning(request, 'Аукціон вже завершено.')
        return redirect('auction_detail', auction_id=auction.id)

    if request.method == 'POST':
        bid_amount = int(request.POST.get('bid_amount'))
        profile = request.user.profile

        # Перевірка, чи ставка вища за поточну
        if bid_amount <= auction.current_bid:
            messages.error(request, 'Ставка має бути вищою за поточну.')
            return redirect('auction_detail', auction_id=auction.id)

        # Перевірка доступних коштів (з урахуванням зарезервованих)
        available = profile.horseshoes - profile.reserved_horseshoes
        if available < bid_amount:
            messages.error(request, 'Недостатньо вільних Срібних Підков.')
            return redirect('auction_detail', auction_id=auction.id)

        with transaction.atomic():
            # Якщо був попередній лідер – звільнити його резерв
            if auction.current_bidder:
                prev_bidder_profile = auction.current_bidder.profile
                prev_bidder_profile.reserved_horseshoes -= auction.current_bid
                prev_bidder_profile.save()

            # Резервуємо нову ставку
            profile.reserved_horseshoes += bid_amount
            profile.save()

            # Оновлюємо аукціон
            auction.current_bid = bid_amount
            auction.current_bidder = request.user
            auction.save()

        messages.success(request, 'Ваша ставка прийнята!')
        return redirect('auction_detail', auction_id=auction.id)

    return redirect('auction_detail', auction_id=auction.id)

# Допоміжна функція завершення аукціону
def finalize_auction(auction):
    if not auction.is_active:
        return

    with transaction.atomic():
        auction.is_active = False
        auction.save()

        horse = auction.horse

        if auction.current_bidder:
            # Переможець
            winner = auction.current_bidder
            winner_profile = winner.profile
            seller_profile = auction.seller.profile

            # Знімаємо з резерву переможця і списуємо кошти
            winner_profile.horseshoes -= auction.current_bid
            winner_profile.reserved_horseshoes -= auction.current_bid
            winner_profile.save()

            # Додаємо кошти продавцю
            seller_profile.horseshoes += auction.current_bid
            seller_profile.save()

            # Передаємо коня
            horse.owner = winner
            horse.status = 'user'
            horse.save()

            # Можна додати повідомлення переможцю (наприклад, через notifications)
        else:
            # Ставок не було – повертаємо коня власнику
            horse.status = 'user'
            horse.save()