def currency_context(request):
    if request.user.is_authenticated:
        profile = request.user.profile
        return {
            'user_horseshoes': profile.horseshoes,
            'user_silver_wings': profile.silver_wings
        }
    return {'user_horseshoes': 0, 'user_silver_wings': 0}


# userspace/context_processors.py
from .models import Profile

def currency_context(request):
    profile = None
    if request.user.is_authenticated:
        profile, created = Profile.objects.get_or_create(user=request.user)
    return {'profile': profile}
