from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ..models import Horse

@login_required
def market_view(request):
    horses = Horse.objects.filter(status='market')
    # Отримуємо унікальні породи, відсортовані за алфавітом
    breeds = Horse.objects.filter(status='market') \
                .values_list('breed', flat=True) \
                .distinct() \
                .order_by('breed')
    # Передаємо список типів коней для фільтра
    horse_types = Horse.TYPE_CHOICES
    return render(request, 'userspace/market/trade.html', {
        'horses': horses,
        'breeds': breeds,
        'horse_types': horse_types,
    })