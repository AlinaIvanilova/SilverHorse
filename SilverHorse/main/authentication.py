from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

UserModel = get_user_model()

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Дозволяє аутентифікацію за email або username.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        # Спробуємо знайти користувача за email або username
        try:
            user = UserModel.objects.get(Q(username=username) | Q(email=username))
        except UserModel.DoesNotExist:
            # Запускаємо стандартний перевір пароля, але він все одно не спрацює
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None