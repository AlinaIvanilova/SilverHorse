from django.db import migrations
import random


def set_initial_skills(apps, schema_editor):
    Horse = apps.get_model('userspace', 'Horse')
    for horse in Horse.objects.all():
        # Базове значення: середнє від speed, endurance, strength
        base = (horse.speed + horse.endurance + horse.strength) / 3.0
        # Враховуємо вік: чим старший кінь, тим більше досвіду (але не менше 1)
        age_factor = max(1, horse.age / 12)  # вік у роках

        # Додаємо випадковість ±20%
        def randomize(val):
            return val * random.uniform(0.8, 1.2)

        horse.dressage = randomize(base * age_factor * 10)  # *10 щоб отримати числа порядку тисяч
        horse.gallop = randomize(base * age_factor * 10)
        horse.trot = randomize(base * age_factor * 10)
        horse.jumping = randomize(base * age_factor * 10)
        horse.save()


class Migration(migrations.Migration):
    dependencies = [
        ('userspace', '0035_horse_dressage_horse_for_sale_horse_gallop_and_more'),  # вкажіть попередню міграцію
    ]
    operations = [
        migrations.RunPython(set_initial_skills),
    ]