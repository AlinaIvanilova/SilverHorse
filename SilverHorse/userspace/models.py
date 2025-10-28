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
