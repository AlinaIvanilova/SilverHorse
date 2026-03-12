# Імпортуємо моделі з відповідних файлів
from .messaging_models import Message, BlockedUser, SystemMessage
from .note_models import Note
from .user_models import Profile, Notification, EquestrianComplex, ComplexRating
from .horse_models import Horse, HorsePet, BreedingOffer
from .auction_models import Auction

# Якщо ви залишили сигнал створення профілю в цьому файлі – він теж має бути тут
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


