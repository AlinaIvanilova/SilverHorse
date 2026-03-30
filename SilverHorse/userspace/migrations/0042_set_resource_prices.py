from django.db import migrations

def set_prices(apps, schema_editor):
    Resource = apps.get_model('userspace', 'Resource')
    prices = {
        'Фураж': 5,
        'Морква': 10,
        'Яблуко': 15,
        'Дерево': 20,
        'Залізо': 20,
    }
    for name, price in prices.items():
        Resource.objects.filter(name=name).update(price=price)

class Migration(migrations.Migration):
    dependencies = [
        ('userspace', '0041_horse_dressage_horse_for_sale_resource_price'),  # замініть на останню міграцію
    ]
    operations = [
        migrations.RunPython(set_prices),
    ]