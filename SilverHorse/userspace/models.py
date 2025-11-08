from django.db import models
from django.contrib.auth.models import User

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
# Профіль користувача (валюта, інше)
# -------------------------
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    horseshoes = models.IntegerField(default=0, verbose_name="Срібні Підкови")
    silver_wings = models.IntegerField(default=0, verbose_name="Срібні Пір'я")

    def __str__(self):
        return f"Профіль {self.user.username}"




class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Повідомлення для {self.user.username}: {self.text[:20]}"


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
    health = models.IntegerField(default=100)  # Здоров'я

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

    # Для зручного відображення в адмінці або в консолі
    def __str__(self):
        return f"{self.name} ({self.breed})"

