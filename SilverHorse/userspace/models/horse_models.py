from django.db import models
from django.contrib.auth.models import User
from django.contrib.staticfiles.storage import staticfiles_storage
from ..horse_images import get_horse_image   # переконайтеся, що шлях правильний

class Horse(models.Model):
    gender_choices = [('M', 'Жеребець'), ('F', 'Кобила')]
    status_choices = [('market', 'На ринку'), ('user', 'У користувача'), ('shelter', 'У притулку')]

    name = models.CharField(max_length=100)
    breed = models.CharField(max_length=50)
    age = models.IntegerField()
    gender = models.CharField(max_length=1, choices=gender_choices)
    coat_color = models.CharField(max_length=50)
    speed = models.IntegerField(default=50)
    endurance = models.IntegerField(default=50)
    strength = models.IntegerField(default=50)
    health = models.IntegerField(default=100)
    energy = models.IntegerField(default=100)
    mood = models.IntegerField(default=100)
    photo = models.ImageField(upload_to='horses/', null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    price = models.IntegerField(default=0)
    status = models.CharField(max_length=10, choices=status_choices, default='market')
    wins = models.PositiveIntegerField(default=0, verbose_name="Перемоги")

    TYPE_CHOICES = [
        ('riding', 'Верховий кінь'),
        ('pony', 'Поні'),
        ('unicorn', 'Єдиноріг'),
        ('pegasus', 'Пегас'),
    ]
    horse_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='riding',
        verbose_name='Тип коня'
    )

    def adjust_stat(self, stat_name, delta):
        if not hasattr(self, stat_name):
            return
        current = getattr(self, stat_name)
        new = max(0, min(100, current + delta))
        setattr(self, stat_name, new)
        self.save()

    def save(self, *args, **kwargs):
        # Автоматично встановлюємо тип "Поні" для Шетландських поні
        if self.breed == "Шетландський поні":
            self.horse_type = 'pony'
        # Якщо потрібно, можна додати інші правила для інших порід
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.breed}) - {self.wins}"

    def get_description(self):
        return (f"Ім'я: {self.name}\nПорода: {self.breed}\nТип: {self.get_horse_type_display()}\nВік: {self.age} рік(років)\n"
                f"Стать: {self.get_gender_display()}\nКолір шерсті: {self.coat_color}\n"
                f"Швидкість: {self.speed}\nВитривалість: {self.endurance}\nСила: {self.strength}\n"
                f"Здоров'я: {self.health}\nЦіна: {self.price}\n"
                f"Статус: {self.get_status_display()}\n"
                f"Власник: {self.owner.username if self.owner else 'На ринку'}")

    def get_photo_url(self):
        if self.photo:
            return self.photo.url
        image_path = get_horse_image(self.breed, self.coat_color, self.age, self.horse_type)
        try:
            return staticfiles_storage.url(image_path)
        except:
            return staticfiles_storage.url('img/horses/default_horse.png')

    def get_photo_alt(self):
        return f"{self.breed} {self.coat_color} - {self.name}"



class HorsePet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='horse_pets')
    horse = models.ForeignKey('Horse', on_delete=models.CASCADE, related_name='pets')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'horse')  # один користувач може погладити коня лише один раз
        verbose_name = "Погладжування коня"
        verbose_name_plural = "Погладжування коней"