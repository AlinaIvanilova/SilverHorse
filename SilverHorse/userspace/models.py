from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.staticfiles.storage import staticfiles_storage  # Додайте цей імпорт
from .horse_images import get_horse_image


# -------------------------
# Повідомлення між користувачами
# -------------------------
class Message(models.Model):
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_messages'
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)  # <- додати сюди

    def __str__(self):
        return f"{self.sender.username} -> {self.receiver.username}: {self.text[:20]}"


# -------------------------
# Нотатки користувача
# -------------------------
class Note(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notes'
    )
    title = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Заголовок"
    )
    content = models.TextField(verbose_name="Текст")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or f"Нотатка від {self.created_at.strftime('%d.%m.%Y')}"


# -------------------------
# Чорний список користувачів
# -------------------------
class BlockedUser(models.Model):
    blocker = models.ForeignKey(
        User,
        related_name='blocked_users',
        on_delete=models.CASCADE
    )
    blocked = models.ForeignKey(
        User,
        related_name='blocked_by',
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('blocker', 'blocked')  # не дозволяє дублікати

    def __str__(self):
        return f"{self.blocker.username} заблокував {self.blocked.username}"


# -------------------------
# Системні повідомлення
# -------------------------
class SystemMessage(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='system_messages',
        null=True, blank=True  # дозволяє створювати масові повідомлення
    )
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)  # "прочитано/непрочитано"

    def __str__(self):
        return f"{self.title} для {self.user.username if self.user else 'всіх'}"


# -------------------------
# Профіль користувача
# -------------------------
class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    #  Валюта
    horseshoes = models.PositiveIntegerField(
        default=0,
        verbose_name="Срібні Підкови"
    )
    silver_wings = models.PositiveIntegerField(
        default=0,
        verbose_name="Срібні Пір'я"
    )

    #  Онбординг
    is_new_user = models.BooleanField(
        default=True,
        verbose_name="Новий користувач"
    )

    # Метадані
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата створення профілю"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Останнє оновлення"
    )

    def __str__(self):
        return f"Профіль {self.user.username}"



class Notification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    text = models.TextField(verbose_name="Текст повідомлення")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата створення"
    )

    def __str__(self):
        return f"Повідомлення для {self.user.username}"

# -------------------------
# Модель "кінь" для зберігання інформації про кожного коня
# -------------------------

class Horse(models.Model):
    # Основні атрибути коня
    name = models.CharField(max_length=100)  # Ім'я коня
    breed = models.CharField(max_length=50)  # Порода коня
    age = models.IntegerField()  # Вік коня (в роках)

    # Стать коня: M - Жеребець, F - Кобила
    gender_choices = [('M', 'Жеребець'), ('F', 'Кобила')]
    gender = models.CharField(max_length=1, choices=gender_choices)

    coat_color = models.CharField(max_length=50)  # Колір шерсті коня

    # Ігрові характеристики (для гри)
    speed = models.IntegerField(default=50)  # Швидкість
    endurance = models.IntegerField(default=50)  # Витривалість
    strength = models.IntegerField(default=50)  # Сила

    # Ігрові атрибути коня
    health = models.IntegerField(default=100)  # Здоров'я
    energy = models.IntegerField(default=100)  # Енергія
    mood = models.IntegerField(default=100)    # Настрій (0–100)

    # Фото коня
    photo = models.ImageField(upload_to='horses/', null=True, blank=True)  # Фото коня

    # Власник та ринок
    owner = models.ForeignKey(
        User,  # Кожен кінь може мати власника
        on_delete=models.SET_NULL,  # Якщо користувач видалений, власник стає NULL
        null=True,  # Поле може бути порожнім (для коней на ринку)
        blank=True  # Поле необов'язкове для форми
    )
    price = models.IntegerField(default=0)  # Ціна коня (для ринку)

    # Статус коня: чи він на ринку, чи у користувача
    status_choices = [('market', 'На ринку'), ('user', 'У користувача')]
    status = models.CharField(max_length=10, choices=status_choices, default='market')

    wins = models.PositiveIntegerField(default=0, verbose_name="Перемоги")  # нове поле


    def adjust_stat(self, stat_name, delta):
        """
        Змінює характеристику коня на delta і обмежує від 0 до 100.
        stat_name: 'health', 'energy', 'mood'
        delta: число (може бути негативне)
        """
        if not hasattr(self, stat_name):
            return  # неправильна характеристика

        current_value = getattr(self, stat_name)
        new_value = max(0, min(100, current_value + delta))
        setattr(self, stat_name, new_value)
        self.save()


    # Для зручного відображення в адмінці або в консолі
    def __str__(self):
        return f"{self.name} ({self.breed}) - {self.wins}"

    # Метод для повного опису коня
    def get_description(self):
        return (
            f"Ім'я: {self.name}\n"
            f"Порода: {self.breed}\n"
            f"Вік: {self.age} рік(років)\n"
            f"Стать: {self.get_gender_display()}\n"
            f"Колір шерсті: {self.coat_color}\n"
            f"Швидкість: {self.speed}\n"
            f"Витривалість: {self.endurance}\n"
            f"Сила: {self.strength}\n"
            f"Здоров'я: {self.health}\n"
            f"Ціна: {self.price}\n"
            f"Статус: {self.get_status_display()}\n"
            f"Власник: {self.owner.username if self.owner else 'На ринку'}"
        )

    def get_photo_url(self):
        """
        Повертає URL фото коня.
        Якщо є кастомне фото - використовує його,
        інакше - генерує на основі породи та забарвлення
        """
        if self.photo:
            return self.photo.url
        else:
            # Генеруємо фото на основі породи та забарвлення
            image_path = get_horse_image(self.breed, self.coat_color)
            try:
                return staticfiles_storage.url(image_path)
            except:
                # Якщо щось пішло не так, повертаємо фото за замовчуванням
                return staticfiles_storage.url('img/horses/default_horse.png')

    def get_photo_alt(self):
        """Генерує alt текст для фото"""
        return f"{self.breed} {self.coat_color} - {self.name}"




@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

def currency_context(request):
    profile = None
    if request.user.is_authenticated:
        # Підстрахуємося на випадок, якщо профіль не створений
        profile, created = Profile.objects.get_or_create(user=request.user)
    return {'profile': profile}




class EquestrianComplex(models.Model):
    LOCATION_CHOICES = [
        ('forest', 'Ліс'),
        ('mountains', 'Гори'),
    ]

    owner = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, default="Мій комплекс")  # нове поле — назва комплексу
    location = models.CharField(max_length=20, choices=LOCATION_CHOICES, default='forest')
    prestige = models.IntegerField(default=0)  # показуємо, але не редагуємо користувачем

    def __str__(self):
        return f"{self.name} ({self.owner.username})"


class ComplexRating(models.Model):
    complex = models.ForeignKey(EquestrianComplex, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=0)  # від 1 до 5

    class Meta:
        unique_together = ('complex', 'user')  # один користувач — одна оцінка
