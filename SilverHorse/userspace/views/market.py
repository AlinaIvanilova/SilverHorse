from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ..models import Horse

@login_required
def market_view(request):
    horses = Horse.objects.filter(status='market')
    return render(request, 'userspace/trade.html', {'horses': horses})