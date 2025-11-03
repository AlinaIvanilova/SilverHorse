from django.apps import AppConfig


class UserspaceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'userspace'

def ready(self):
    import userspace.signals
