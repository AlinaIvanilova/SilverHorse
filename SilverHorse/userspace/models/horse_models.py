from django.db import models
from django.contrib.auth.models import User
from django.contrib.staticfiles.storage import staticfiles_storage
from django.utils import timezone
from ..horse_images import get_horse_image


class Horse(models.Model):
    gender_choices = [('M', 'Жеребець'), ('F', 'Кобила')]
    status_choices = [('market', 'На ринку'), ('user', 'У користувача'), ('shelter', 'У притулку'),
                      ('auction', 'На аукціоні')]

    name = models.CharField(max_length=100)
    breed = models.CharField(max_length=50)
    age = models.IntegerField()  # вік у місяцях
    gender = models.CharField(max_length=1, choices=gender_choices)
    coat_color = models.CharField(max_length=50)
    # Змінено на FloatField для підтримки десяткових значень
    speed = models.FloatField(default=50.0)
    endurance = models.FloatField(default=50.0)
    strength = models.IntegerField(default=50)  # залишено IntegerField, якщо не потрібні десяткові
    health = models.IntegerField(default=100)
    energy = models.IntegerField(default=100)
    mood = models.IntegerField(default=100)
    photo = models.ImageField(upload_to='horses/', null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='horses')
    price = models.IntegerField(default=0)
    status = models.CharField(max_length=10, choices=status_choices, default='market')
    wins = models.PositiveIntegerField(default=0, verbose_name="Перемоги")
    for_sale = models.BooleanField(default=False)

    # Поля для механіки сну (лише один раз!)
    last_sleep = models.DateTimeField(null=True, blank=True, verbose_name="Останній сон")
    last_sleep_processed = models.DateField(null=True, blank=True, verbose_name="Дата застосування ефектів сну")
    energy_at_sleep = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Енергія на момент сну")
    pending_health_loss = models.IntegerField(default=0, verbose_name="Відкладена втрата здоров'я")

    # Нові поля навичок (FloatField – з десятковими)
    dressage = models.FloatField(default=0.0, verbose_name="Виїздка")
    gallop = models.FloatField(default=0.0, verbose_name="Галоп")
    trot = models.FloatField(default=0.0, verbose_name="Рись")
    jumping = models.FloatField(default=0.0, verbose_name="Стрибки")

    # Поля для вагітності
    is_pregnant = models.BooleanField(default=False, verbose_name="Вагітна")
    pregnancy_due_age = models.IntegerField(null=True, blank=True, verbose_name="Вік пологів (міс.)")
    sire = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='offspring',
                             verbose_name="Батько")

    # NEW: поле для матері
    dam = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='offspring_dam',
                            verbose_name="Мати")

    # Первинний власник
    original_owner = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='original_horses', verbose_name="Первинний власник"
    )

    # Прапор зміни імені
    name_customized = models.BooleanField(default=False, verbose_name="Ім'я змінено")

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
                f"Власник: {self.owner.username if self.owner else 'На ринку'}"
                f"{' (вагітна)' if self.is_pregnant else ''}")

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


class BreedingOffer(models.Model):
    CURRENCY_CHOICES = [
        ('horseshoes', 'Підкови'),
        ('silver_wings', 'Срібні пір\'їни'),
    ]
    horse = models.ForeignKey(Horse, on_delete=models.CASCADE, related_name='breeding_offers')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='breeding_offers')
    price = models.IntegerField()
    currency = models.CharField(max_length=20, choices=CURRENCY_CHOICES, default='horseshoes')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    max_uses = models.PositiveIntegerField(null=True, blank=True, verbose_name="Максимальна кількість використань")
    remaining_uses = models.PositiveIntegerField(null=True, blank=True, verbose_name="Залишилось використань")

    def __str__(self):
        return f"{self.horse.name} – {self.price} {self.get_currency_display()}"

# Додати в кінець файлу models.py

class Competition(models.Model):
    COMPETITION_TYPES = [
        ('barrel_racing', 'Перегони навколо бочок'),
        ('cutting', 'Каттинг'),
        ('trail', 'Трейл'),
        ('reining', 'Рейнінг'),
        ('grand_prix', 'Гран-Прі'),
        ('western_pleasure', 'Вестерн плежер'),
    ]

    name = models.CharField(max_length=100)
    competition_type = models.CharField(max_length=30, choices=COMPETITION_TYPES)
    description = models.TextField(blank=True)
    # Вимоги до навичок (наприклад, які навички найважливіші)
    primary_skill = models.CharField(max_length=20, choices=[
        ('speed', 'Швидкість'),
        ('endurance', 'Витривалість'),
        ('dressage', 'Виїздка'),
        ('gallop', 'Галоп'),
        ('trot', 'Рись'),
        ('jumping', 'Стрибки'),
    ])
    secondary_skill = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('speed', 'Швидкість'),
        ('endurance', 'Витривалість'),
        ('dressage', 'Виїздка'),
        ('gallop', 'Галоп'),
        ('trot', 'Рись'),
        ('jumping', 'Стрибки'),
    ])
    energy_cost = models.PositiveSmallIntegerField(default=20)  # витрати енергії
    max_participants = models.PositiveSmallIntegerField(default=8)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Змагання"
        verbose_name_plural = "Змагання"
        ordering = ['start_time']

    def __str__(self):
        return f"{self.get_competition_type_display()} - {self.start_time.strftime('%d.%m.%Y %H:%M')}"

    def get_skill_weight(self, skill_name):
        """Повертає вагу навички для цього типу змагань (1.0 для primary, 0.7 для secondary, 0.3 для інших)."""
        if skill_name == self.primary_skill:
            return 1.0
        elif skill_name == self.secondary_skill:
            return 0.7
        return 0.3

    def calculate_horse_score(self, horse):
        """Обчислює зважений бал коня для цього змагання."""
        skills = ['speed', 'endurance', 'dressage', 'gallop', 'trot', 'jumping']
        total = 0
        for skill in skills:
            weight = self.get_skill_weight(skill)
            total += getattr(horse, skill) * weight
        # Додаємо випадковий фактор ±10%
        import random
        random_factor = 1 + random.uniform(-0.1, 0.1)
        return round(total * random_factor, 2)

    # Додати в кінець класу Competition (перед класом CompetitionRegistration)
    def process_results(self):
        from django.utils import timezone
        from ..models import SystemMessage  # імпорт всередині, щоб уникнути циклічних імпортів
        if self.start_time > timezone.now():
            return  # ще не час
        if self.registrations.filter(status='finished').exists():
            return  # вже оброблено

        registrations = self.registrations.filter(status='registered').select_related('horse', 'horse__owner')
        if not registrations.exists():
            return

        # Обчислюємо бали
        scores = []
        for reg in registrations:
            score = self.calculate_horse_score(reg.horse)
            scores.append((reg, score))
        scores.sort(key=lambda x: x[1], reverse=True)

        # Призначаємо місця та нагороди
        for place, (reg, score) in enumerate(scores, start=1):
            reg.result_place = place
            reg.score = score
            if place == 1:
                reward = 500
            elif place == 2:
                reward = 300
            elif place == 3:
                reward = 200
            else:
                reward = 100
            reg.reward_horseshoes = reward
            reg.status = 'finished'
            reg.save()

            # Нарахування власнику
            if reg.horse.owner:
                profile = reg.horse.owner.profile
                profile.horseshoes += reward
                profile.save()

                # Створення системного повідомлення
                SystemMessage.objects.create(
                    user=reg.horse.owner,
                    title=f"Результати змагання «{self.name}»",
                    content=(
                        f"Ваш кінь {reg.horse.name} взяв участь у змаганні «{self.name}».\n"
                        f"Тип: {self.get_competition_type_display()}.\n"
                        f"Місце: {place}.\n"
                        f"Зароблено: {reward} підков."
                    )
                )


class CompetitionRegistration(models.Model):
    STATUS_CHOICES = [
        ('registered', 'Зареєстровано'),
        ('finished', 'Завершено'),
        ('cancelled', 'Скасовано'),
    ]

    horse = models.ForeignKey('Horse', on_delete=models.CASCADE, related_name='competition_registrations')
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='registrations')
    registered_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='registered')
    result_place = models.PositiveSmallIntegerField(null=True, blank=True)  # місце
    score = models.FloatField(null=True, blank=True)  # набраний бал
    reward_horseshoes = models.PositiveIntegerField(default=0)
    reward_experience = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Реєстрація на змагання"
        verbose_name_plural = "Реєстрації на змагання"
        unique_together = ['horse', 'competition']  # один кінь не може бути зареєстрований двічі на те саме змагання

    def __str__(self):
        return f"{self.horse.name} -> {self.competition}"