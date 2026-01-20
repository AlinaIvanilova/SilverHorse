# generate_horses.py

import sys
import os
import random

# =========================
# 🌟 Підключення Django
# =========================

# Додаємо корінь проекту в sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Вказуємо налаштування Django і запускаємо
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SilverHorse.settings")
import django
django.setup()

# =========================
# 🌟 Імпорт моделей
# =========================
from userspace.models import Horse

# =========================
# 🌟 Дані для генерації коней
# =========================
breeds = ['Ахелтекинець']
colors = ['світло-сірий']

# =========================
# 🌟 Генерація коней
# =========================
for i in range(2):
    horse = Horse.objects.create(
        name=f"Кінь{i}",
        breed=random.choice(breeds),
        gender=random.choice(['M', 'F']),
        coat_color=random.choice(colors),
        age=random.randint(2, 15),  # <- додано
        speed=random.randint(40, 100),
        endurance=random.randint(40, 100),
        strength=random.randint(40, 100),
        owner=None,
        status='market',
        price=random.randint(100, 1000)
    )