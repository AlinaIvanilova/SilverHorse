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
    return render(request, 'userspace/trade.html', {
        'horses': horses,
        'breeds': breeds,
    })