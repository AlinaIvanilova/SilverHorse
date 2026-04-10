# userspace/views/competitions.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Count, F
from ..models import Horse, Competition, CompetitionRegistration
import random


@login_required
def competition_list_for_horse(request, horse_id):
    """Сторінка зі списком змагань для конкретного коня."""
    horse = get_object_or_404(Horse, id=horse_id)

    # Перевірка прав доступу (тільки власник або адмін)
    if horse.owner != request.user and not request.user.is_staff:
        messages.error(request, "Ви не можете переглядати змагання для цього коня.")
        return redirect('horse_detail', horse_id=horse.id)

    # Обробка завершених змагань
    finished_comps = Competition.objects.filter(
        is_active=True,
        start_time__lte=timezone.now()
    ).exclude(
        registrations__status='finished'
    )
    for comp in finished_comps:
        comp.process_results()

    # Отримуємо активні змагання, які ще не почалися
    now = timezone.now()
    available_competitions = Competition.objects.filter(
        is_active=True,
        start_time__gte=now,  # майбутні
    ).annotate(
        registered_count=Count('registrations')
    ).filter(
        registered_count__lt=F('max_participants')
    ).order_by('start_time')

    # Фільтрація за типом, якщо передано параметр
    comp_type = request.GET.get('type')
    if comp_type:
        available_competitions = available_competitions.filter(competition_type=comp_type)

    # Реєстрації цього коня на будь-які змагання
    my_registrations = CompetitionRegistration.objects.filter(
        horse=horse
    ).select_related('competition').order_by('-registered_at')

    # Для кожної доступної змагання перевіряємо, чи кінь вже зареєстрований
    registered_comp_ids = my_registrations.values_list('competition_id', flat=True)

    context = {
        'horse': horse,
        'available_competitions': available_competitions,
        'my_registrations': my_registrations,
        'registered_comp_ids': registered_comp_ids,
        'comp_types': Competition.COMPETITION_TYPES,
        'selected_type': comp_type,
        'now': now,
    }
    return render(request, 'userspace/competitions/competition_list.html', context)

@login_required
def register_for_competition(request, horse_id, competition_id):
    """Реєстрація коня на змагання."""
    horse = get_object_or_404(Horse, id=horse_id)
    competition = get_object_or_404(Competition, id=competition_id)

    # Перевірки
    if horse.owner != request.user:
        messages.error(request, "Ви не можете реєструвати цього коня.")
        return redirect('horse_detail', horse_id=horse.id)

    if horse.status != 'user':
        messages.error(request, "Кінь повинен бути у вашій стайні.")
        return redirect('horse_detail', horse_id=horse.id)

    if competition.start_time < timezone.now():
        messages.error(request, "Змагання вже почалося.")
        return redirect('competition_list', horse_id=horse.id)

    # Перевірка кількості учасників
    current_count = competition.registrations.filter(status='registered').count()
    if current_count >= competition.max_participants:
        messages.error(request, "Всі місця на змагання вже зайняті.")
        return redirect('competition_list', horse_id=horse.id)

    # Перевірка, чи кінь вже зареєстрований
    if CompetitionRegistration.objects.filter(horse=horse, competition=competition).exists():
        messages.warning(request, f"{horse.name} вже зареєстрований на це змагання.")
        return redirect('competition_list', horse_id=horse.id)

    # Перевірка енергії
    if horse.energy < competition.energy_cost:
        messages.error(request, f"У {horse.name} недостатньо енергії. Потрібно {competition.energy_cost}, є {horse.energy}.")
        return redirect('competition_list', horse_id=horse.id)

    # Створюємо реєстрацію та знімаємо енергію
    with transaction.atomic():
        horse.energy -= competition.energy_cost
        horse.save()
        CompetitionRegistration.objects.create(
            horse=horse,
            competition=competition,
            status='registered'
        )

    messages.success(request, f"{horse.name} зареєстровано на {competition.get_competition_type_display()}!")
    return redirect('competition_list', horse_id=horse.id)


@login_required
def cancel_registration(request, registration_id):
    """Скасування реєстрації (повернення енергії частково)."""
    registration = get_object_or_404(CompetitionRegistration, id=registration_id)
    if registration.horse.owner != request.user:
        messages.error(request, "Ви не можете скасувати цю реєстрацію.")
        return redirect('horse_detail', horse_id=registration.horse.id)

    if registration.status != 'registered':
        messages.error(request, "Можна скасувати лише активну реєстрацію.")
        return redirect('competition_list', horse_id=registration.horse.id)

    if registration.competition.start_time < timezone.now():
        messages.error(request, "Змагання вже почалося, скасування неможливе.")
        return redirect('competition_list', horse_id=registration.horse.id)

    # Повертаємо половину енергії
    refund = registration.competition.energy_cost // 2
    with transaction.atomic():
        registration.horse.energy = min(100, registration.horse.energy + refund)
        registration.horse.save()
        registration.delete()

    messages.success(request, f"Реєстрацію скасовано. Повернено {refund} енергії.")
    return redirect('competition_list', horse_id=registration.horse.id)


@login_required
def my_competitions(request):
    """Список усіх реєстрацій користувача."""
    user_horses = Horse.objects.filter(owner=request.user, status='user')
    registrations = CompetitionRegistration.objects.filter(
        horse__in=user_horses
    ).select_related('horse', 'competition').order_by('-registered_at')

    # ✅ Виправлено: додано "userspace/"
    return render(request, 'userspace/competitions/my_competitions.html', {
        'registrations': registrations,
        'now': timezone.now(),
    })