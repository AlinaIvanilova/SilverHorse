def currency_context(request):
    if request.user.is_authenticated:
        profile = request.user.profile
        return {
            'user_coins': profile.coins,
            'user_gems': profile.gems
        }
    return {'user_coins': 0, 'user_gems': 0}
