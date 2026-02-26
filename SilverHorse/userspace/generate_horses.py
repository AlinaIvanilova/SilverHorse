# generate_horses.py

import sys
import os
import random
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SilverHorse.settings")
import django
django.setup()

from django.db import connection
from userspace.models import Horse  # імпортуємо для отримання назви таблиці

# Дані для генерації
breeds = ['Ахалтекінець', 'Фризька']
colors = ['Чорний']

# Назва таблиці (зазвичай userspace_horse)
table_name = Horse._meta.db_table

# Генерація 5 коней
for i in range(5):
    # Генеруємо випадкові значення для всіх полів
    name = f"Молодий_кінь_{i+1}"
    breed = random.choice(breeds)
    age = random.randint(0, 1)
    gender = random.choice(['M', 'F'])
    coat_color = random.choice(colors)
    speed = random.randint(40, 100)
    endurance = random.randint(40, 100)
    strength = random.randint(40, 100)
    health = random.randint(50, 100)
    energy = random.randint(50, 100)
    mood = random.randint(50, 100)
    photo = ''  # або None, якщо поле допускає NULL
    owner_id = None  # зовнішній ключ може бути NULL
    price = random.randint(100, 1000)
    status = 'market'
    wins = 0
    for_sale = 1  # 1 = True, 0 = False (для MySQL)

    # SQL-запит
    with connection.cursor() as cursor:
        cursor.execute(f"""
            INSERT INTO {table_name} 
            (name, breed, age, gender, coat_color, speed, endurance, strength, health, energy, mood, photo, owner_id, price, status, wins, for_sale)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, [name, breed, age, gender, coat_color, speed, endurance, strength, health, energy, mood, photo, owner_id, price, status, wins, for_sale])

    print(f"Створено коня: {name}, порода: {breed}, вік: {age}")

print("Генерацію завершено.")