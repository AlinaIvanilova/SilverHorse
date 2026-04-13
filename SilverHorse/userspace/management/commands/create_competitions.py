from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from userspace.models import Competition  # абсолютний імпорт

class Command(BaseCommand):
    help = 'Create initial competitions'

    def handle(self, *args, **options):
        now = timezone.now()
        comps = [
            {
                'competition_type': 'barrel_racing',
                'name': 'Весняний баррель-рейсінг',
                'description': 'Швидкісні перегони на арені, де кінь має обігнути три бочки за схемою «клеверного листа» (правий бік – лівий бік – пряма). Головне – різкі повороти та миттєвий розгін після них.',
                'primary_skill': 'speed',
                'secondary_skill': 'gallop',
                'energy_cost': 20,
                'max_participants': 8,
                'start_time': now + timedelta(days=1),
            },
            {
                'competition_type': 'cutting',
                'name': 'Каттинг чемпіонат',
                'description': 'Конкурс роботи з худобою: кінь і вершник мають відокремити одну корову від череди та не дати їй повернутися назад протягом 2–3 хвилин. Потрібна неймовірна спритність і реакція коня.',
                'primary_skill': 'dressage',
                'secondary_skill': 'endurance',
                'energy_cost': 25,
                'max_participants': 6,
                'start_time': now + timedelta(days=2),
            },
            {
                'competition_type': 'trail',
                'name': 'Трейл-аджиліті',
                'description': 'Кінь проходить смугу перешкод, що імітують природні та фермерські об’єкти: містки, ворота, водні калюжі, перекладини, гумові завіси. Завдання – подолати всі перешкоди спокійно та без помилок.',
                'primary_skill': 'trot',
                'secondary_skill': 'endurance',
                'energy_cost': 20,
                'max_participants': 10,
                'start_time': now + timedelta(days=3),
            },
            {
                'competition_type': 'reining',
                'name': 'Рейнінг класик',
                'description': 'Західне змагання, де кінь виконує точну послідовність манежних фігур: спіни (обертання на місці), слайди (ковзні зупинки), розвороти на задніх ногах. Оцінюють чіткість, стиль і «бажання» коня працювати.',
                'primary_skill': 'dressage',
                'secondary_skill': 'gallop',
                'energy_cost': 30,
                'max_participants': 8,
                'start_time': now + timedelta(days=4),
            },
            {
                'competition_type': 'grand_prix',
                'name': 'Гран-Прі з конкуру',
                'description': 'Елітний клас змагань з дуже високими перешкодами (до 160 см). Маршрут з 12–14 перешкод. Головне – подолання високих бар’єрів, швидкість та витривалість до фінішу.',
                'primary_skill': 'jumping',
                'secondary_skill': 'speed',
                'energy_cost': 35,
                'max_participants': 12,
                'start_time': now + timedelta(days=5),
            },
            {
                'competition_type': 'western_pleasure',
                'name': 'Вестерн плежер шоу',
                'description': 'Спокійне, елегантне змагання в західному стилі. Кінь повинен рухатися м’яким, неквапливим кроком або риссю, виконувати прості переходи між алюрами. Перемагає той, хто виглядає найбільш розслабленим і слухняним.',
                'primary_skill': 'trot',
                'secondary_skill': 'dressage',
                'energy_cost': 15,
                'max_participants': 10,
                'start_time': now + timedelta(days=6),
            },
        ]

        for data in comps:
            comp, created = Competition.objects.get_or_create(
                competition_type=data['competition_type'],
                start_time=data['start_time'],
                defaults={
                    'name': data['name'],
                    'description': data['description'],
                    'primary_skill': data['primary_skill'],
                    'secondary_skill': data['secondary_skill'],
                    'energy_cost': data['energy_cost'],
                    'max_participants': data['max_participants'],
                    'end_time': data['start_time'] + timedelta(hours=2),
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created competition: {comp}'))
            else:
                self.stdout.write(f'Competition already exists: {comp}')