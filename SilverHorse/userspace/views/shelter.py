# userspace/views/shelter.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Exists, OuterRef
from django.utils import timezone
from datetime import timedelta
from ..models import Horse, HorsePet

# Константа для винагороди – змінюйте тут або винесіть у settings.py
PET_REWARD = 10


@login_required
def shelter_view(request):
    # Додаємо анотацію, чи гладив поточний користувач цього коня (за всі часи – для кнопки "Вже гладили")
    horses = Horse.objects.filter(status='shelter').annotate(
        user_petted=Exists(
            HorsePet.objects.filter(user=request.user, horse=OuterRef('pk'))
        )
    )
    breeds = Horse.objects.filter(status='shelter') \
        .values_list('breed', flat=True) \
        .distinct() \
        .order_by('breed')
    horse_types = Horse.TYPE_CHOICES
    return render(request, 'userspace/shelter.html', {
        'horses': horses,
        'breeds': breeds,
        'horse_types': horse_types,
    })


@login_required
def send_to_shelter(request, horse_id):
    horse = get_object_or_404(Horse, id=horse_id, owner=request.user, status='user')
    profile = request.user.profile
    profile.horseshoes += 500
    profile.save()
    horse.status = 'shelter'
    horse.owner = None
    horse.save()
    messages.success(request, f"Ви відправили коня {horse.name} до притулку та отримали 500 підков.")
    return redirect('horses_page')


@login_required
def pet_horse(request, horse_id):
    horse = get_object_or_404(Horse, id=horse_id, status='shelter')

    # Перевірка, чи було погладжування за останні 24 години
    one_day_ago = timezone.now() - timedelta(hours=24)
    if HorsePet.objects.filter(user=request.user, horse=horse, timestamp__gte=one_day_ago).exists():
        messages.error(request, f"Ви вже гладили {horse.name} сьогодні. Завтра зможете знову!")
    else:
        # Створюємо новий запис
        HorsePet.objects.create(user=request.user, horse=horse)
        profile = request.user.profile
        profile.horseshoes += PET_REWARD
        profile.save()
        messages.success(request, f"Ви погладили {horse.name} і отримали {PET_REWARD} Срібних Підков!")

    # Повернення на попередню сторінку (або на сторінку коня)
    next_url = request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('horse_detail', horse_id=horse.id)