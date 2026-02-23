from .models import Profile

def currency_context(request):
    """
    Додає в контекст шаблонів кількість срібних підков та пір'їн поточного користувача.
    Якщо користувач не авторизований – повертає нулі.
    """
    if request.user.is_authenticated:
        # get_or_create гарантує, що профіль існує (навіть якщо сигнал чомусь не спрацював)
        profile, _ = Profile.objects.get_or_create(user=request.user)
        return {
            'user_horseshoes': profile.horseshoes,
            'user_silver_wings': profile.silver_wings,
        }
    return {
        'user_horseshoes': 0,
        'user_silver_wings': 0,
    }