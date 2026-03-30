from django.db import migrations

def create_initial_resources(apps, schema_editor):
    Resource = apps.get_model('userspace', 'Resource')
    resources = [
        ('Фураж', 'food', 5),
        ('Морква', 'food', 10),
        ('Яблуко', 'food', 15),
        ('Дерево', 'building', 20),
        ('Залізо', 'building', 20),
    ]
    for name, res_type, price in resources:
        Resource.objects.get_or_create(name=name, type=res_type, defaults={'price': price})

class Migration(migrations.Migration):
    dependencies = [
        ('userspace', '0039_resource_horse_dressage_horse_for_sale_and_more'),
    ]
    operations = [
        migrations.RunPython(create_initial_resources),
    ]