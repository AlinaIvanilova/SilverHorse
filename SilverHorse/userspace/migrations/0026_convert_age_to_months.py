from django.db import migrations

def convert_age_to_months(apps, schema_editor):
    Horse = apps.get_model('userspace', 'Horse')
    for horse in Horse.objects.all():
        horse.age = horse.age * 12
        horse.save()

class Migration(migrations.Migration):
    dependencies = [
        ('userspace', '0025_auction_currency_profile_reserved_silver_wings'),
    ]
    operations = [
        migrations.RunPython(convert_age_to_months),
    ]