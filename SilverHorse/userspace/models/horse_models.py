from django.db import models
from django.contrib.auth.models import User
from django.contrib.staticfiles.storage import staticfiles_storage
from django.utils import timezone
from ..horse_images import get_horse_image   # переконайтеся, що шлях правильний

class Horse(models.Model):
    gender_choices = [('M', 'Жеребець'), ('F', 'Кобила')]
    status_choices = [('market', 'На ринку'), ('user', 'У користувача'), ('shelter', 'У притулку'), ('auction', 'На аукціоні')]

    name = models.CharField(max_length=100)
    breed = models.CharField(max_length=50)
    age = models.IntegerField()  # вік у місяцях
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
    for_sale = models.BooleanField(default=False)
    last_sleep = models.DateTimeField(null=True, blank=True, verbose_name="Останній сон")  # нове поле

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
        if self.breed == "Шетландський поні":
            self.horse_type = 'pony'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.breed}) - {self.wins}"

    def get_description(self):
        return (f"Ім'я: {self.name}\nПорода: {self.breed}\nТип: {self.get_horse_type_display()}\n"
                f"Вік: {self.get_age_display()}\nСтать: {self.get_gender_display()}\n"
                f"Колір шерсті: {self.coat_color}\nШвидкість: {self.speed}\n"
                f"Витривалість: {self.endurance}\nСила: {self.strength}\nЗдоров'я: {self.health}\n"
                f"Ціна: {self.price}\nСтатус: {self.get_status_display()}\n"
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

    def get_age_display(self):
        if self.age == 0:
            return "Декілька годин"
        years = self.age // 12
        months = self.age % 12

        def pluralize(number, forms):
            if number % 10 == 1 and number % 100 != 11:
                return forms[0]
            elif 2 <= number % 10 <= 4 and (number % 100 < 10 or number % 100 >= 20):
                return forms[1]
            else:
                return forms[2]

        year_str = f"{years} {pluralize(years, ('рік', 'роки', 'років'))}"
        if months == 0:
            return year_str
        month_str = f"{months} {pluralize(months, ('місяць', 'місяці', 'місяців'))}"
        return f"{year_str} {month_str}"


class HorsePet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='horse_pets')
    horse = models.ForeignKey('Horse', on_delete=models.CASCADE, related_name='pets')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Погладжування коня"
        verbose_name_plural = "Погладжування коней"