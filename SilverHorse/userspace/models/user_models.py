from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    horseshoes = models.PositiveIntegerField(default=0, verbose_name="Срібні Підкови")
    silver_wings = models.PositiveIntegerField(default=0, verbose_name="Срібні Пір'я")
    reserved_horseshoes = models.PositiveIntegerField(default=0, verbose_name="Зарезервовано на аукціоні")  # нове поле
    reserved_silver_wings = models.PositiveIntegerField(default=0, verbose_name="Зарезервовано Пір'я")
    is_new_user = models.BooleanField(default=True, verbose_name="Новий користувач")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення профілю")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Останнє оновлення")

    def __str__(self):
        return f"Профіль {self.user.username}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    text = models.TextField(verbose_name="Текст повідомлення")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")

    def __str__(self):
        return f"Повідомлення для {self.user.username}"

class EquestrianComplex(models.Model):
    LOCATION_CHOICES = [('forest', 'Ліс'), ('mountains', 'Гори')]
    owner = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, default="Мій комплекс")
    location = models.CharField(max_length=20, choices=LOCATION_CHOICES, default='forest')
    prestige = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name} ({self.owner.username})"

class ComplexRating(models.Model):
    complex = models.ForeignKey(EquestrianComplex, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=0)

    class Meta:
        unique_together = ('complex', 'user')