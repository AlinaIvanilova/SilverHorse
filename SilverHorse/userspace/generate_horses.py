# generate_horses.py

import sys
import os
import random
from datetime import datetime

# Налаштування Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SilverHorse.settings")
import django
django.setup()

from userspace.models import Horse

# Дані для генерації
breeds = ['Ахалтекінець', 'Фризька', 'Шетландський поні']  # додано породу поні
colors = ['Чорний', 'Гнідий', 'Рудий', 'Сірий', 'Білий']
genders = ['M', 'F']

# Генерація 5 коней
for i in range(5):
    # Генеруємо випадкові значення
    name = f"Молодий_кінь_{i+1}"
    breed = random.choice(breeds)
    age = random.randint(0, 5)
    gender = random.choice(genders)
    coat_color = random.choice(colors)
    speed = random.randint(40, 100)
    endurance = random.randint(40, 100)
    strength = random.randint(40, 100)
    health = random.randint(50, 100)
    energy = random.randint(50, 100)
    mood = random.randint(50, 100)
    price = random.randint(100, 1000)
    status = 'market'  # усі нові коні з'являються на ринку
    wins = 0

    # Створюємо об'єкт Horse — метод save() автоматично встановить horse_type
    # на основі породи (для "Шетландський поні" буде 'pony')
    horse = Horse(
        name=name,
        breed=breed,
        age=age,
        gender=gender,
        coat_color=coat_color,
        speed=speed,
        endurance=endurance,
        strength=strength,
        health=health,
        energy=energy,
        mood=mood,
        price=price,
        status=status,
        wins=wins,
        # owner і photo залишаємо None (за замовчуванням)
    )
    horse.save()

    print(f"Створено коня: {horse.name}, порода: {horse.breed}, тип: {horse.get_horse_type_display()}")

print("Генерацію завершено.")