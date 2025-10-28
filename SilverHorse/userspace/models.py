# userspace/models.py

from django.db import models
from django.contrib.auth.models import User

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender} -> {self.receiver}: {self.text[:20]}"

class Note(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notes')
    title = models.CharField(max_length=100, blank=True, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Текст")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or f"Нотатка від {self.created_at.strftime('%d.%m.%Y')}"

class BlockedUser(models.Model):
    blocker = models.ForeignKey(User, related_name='blocked_users', on_delete=models.CASCADE)
    blocked = models.ForeignKey(User, related_name='blocked_by', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('blocker', 'blocked')  # щоб не дублювати записи

    def __str__(self):
        return f"{self.blocker.username} заблокував {self.blocked.username}"
