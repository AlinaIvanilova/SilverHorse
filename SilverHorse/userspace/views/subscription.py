from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ..models import Notification


PROMO_CODES = {
    'WELCOME100': {'horseshoes': 10000, 'silver_wings': 0},
    'ONE': {'horseshoes': 1000, 'silver_wings': 0, 'once': True},
}

USED_PROMO_CODES = set()



@login_required
def subscription_page(request):
    user = request.user
    promo_message = None
    promo_used = False

    if request.method == "POST" and 'promo_code' in request.POST:
        code = request.POST.get('promo_code', '').upper()

        if code in PROMO_CODES:
            if code in USED_PROMO_CODES:
                promo_message = f"Промокод {code} вже використаний!"
                promo_used = True
            else:
                # Додаємо валюту
                horseshoes_added = PROMO_CODES[code]['horseshoes']
                wings_added = PROMO_CODES[code]['silver_wings']
                user.profile.horseshoes += horseshoes_added
                user.profile.silver_wings += wings_added
                user.profile.save()

                promo_message = f"Промокод {code} активовано! Ви отримали валюту."

                # Створюємо сповіщення
                Notification.objects.create(
                    user=user,
                    text=f"Ви активували промокод {code}! Вам зараховано "
                         f"{horseshoes_added} Срібних Підков і {wings_added} Срібних Пір'їв."
                )

                # Якщо код одноразовий
                if PROMO_CODES[code].get('once', False):
                    USED_PROMO_CODES.add(code)
        else:
            promo_message = "Невірний промокод."

    # Отримуємо сповіщення для вкладки
    notifications = Notification.objects.filter(user=user).order_by('-created_at')

    context = {
        'promo_message': promo_message,
        'promo_used': promo_used,
        'notifications': notifications,
    }
    return render(request, 'userspace/user/subscription.html', context)