# userspace/horse_images.py

HORSE_IMAGES = {
    # Формат: (порода, забарвлення): 'шлях/до/фото.png'
    ('ахалтекінець', 'вогняно-гнідий'): 'img/horses/ahaltekin_fire_chestnut.png',
    ('ахалтекінець', 'вороний'): 'img/horses/ahaltekin_full_black.png',
    ('ахалтекінець', 'мишасто-сірий'): 'img/horses/ahaltekin_light_gray.png',
    ('Шетландський поні', 'рудий'): 'img/horses/pony_red.png',

    # Тут ви зможете додавати нові фото в майбутньому
    # ('арабська', 'сірий'): 'img/horses/arabian_gray.png',
    # ('фризька', 'чорний'): 'img/horses/friesian_black.png',
}

# Шляхи для типів за замовчуванням
DEFAULT_HORSE_IMAGES = {
    'riding': 'img/horses/default_horse.png',          # дорослий верховий
    'pony': 'img/horses/default_pony_adult.png',       # дорослий поні
    'unicorn': 'img/horses/default_unicorn.png',       # єдиноріг
    'pegasus': 'img/horses/default_pegasus.png',       # пегас
}

DEFAULT_LITTLE_HORSE_IMAGES = {
    'riding': 'img/horses/default_little_horse.png',
    'pony': 'img/horses/default_little_pony.png',
    'unicorn': 'img/horses/default_little_unicorn.png',
    'pegasus': 'img/horses/default_little_pegasus.png',
}

def get_horse_image(breed, coat_color, age=None, horse_type='riding'):
    """
    Повертає шлях до зображення коня.
    Спочатку перевіряє вік (для малят), потім тип, потім породу+забарвлення.
    Вік передається в місяцях.
    """
    # Перевіряємо вік: якщо менше 12 місяців (1 рік) – лоша, інакше дорослий
    if age is not None:
        try:
            age_val = int(age)  # вік у місяцях
            if age_val < 12:
                # Якщо лоша — повертаємо зображення за типом
                return DEFAULT_LITTLE_HORSE_IMAGES.get(horse_type, 'img/horses/default_little_horse.png')
        except (ValueError, TypeError):
            # Якщо не вдалося перетворити — ігноруємо вік
            pass

    # Спочатку пробуємо знайти за породою та забарвленням
    key = (breed.lower().strip(), coat_color.lower().strip())
    image = HORSE_IMAGES.get(key)
    if image:
        return image

    # Якщо немає специфічного зображення, повертаємо за типом
    return DEFAULT_HORSE_IMAGES.get(horse_type, 'img/horses/default_horse.png')