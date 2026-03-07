from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from .horse_models import Horse   # якщо Horse знаходиться в тому ж пакеті

class Auction(models.Model):
    horse = models.OneToOneField(Horse, on_delete=models.CASCADE, related_name='auction')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='auctions_selling')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField()
    starting_price = models.PositiveIntegerField()
    current_bid = models.PositiveIntegerField()
    current_bidder = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='auctions_bidding'
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Аукціон: {self.horse.name} (до {self.end_time})"

    def time_left(self):
        now = timezone.now()
        if now > self.end_time:
            return "Завершився"
        delta = self.end_time - now
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        seconds = delta.seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"