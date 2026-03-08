from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from .horse_models import Horse

class Auction(models.Model):
    CURRENCY_CHOICES = [
        ('horseshoes', 'Срібні Підкови'),
        ('silver_wings', 'Срібні Пір\'я'),
    ]

    horse = models.OneToOneField(Horse, on_delete=models.CASCADE, related_name='auction')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='auctions_selling')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField()  # оновлюється при кожній ставці
    starting_price = models.PositiveIntegerField()
    current_bid = models.PositiveIntegerField()
    current_bidder = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='auctions_bidding'
    )
    currency = models.CharField(max_length=20, choices=CURRENCY_CHOICES, default='horseshoes')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Аукціон: {self.horse.name} ({self.get_currency_display()})"

    def time_left(self):
        now = timezone.now()
        if not self.is_active or now > self.end_time:
            return "Завершився"
        delta = self.end_time - now
        total_seconds = int(delta.total_seconds())
        if total_seconds <= 0:
            return "Завершився"
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"