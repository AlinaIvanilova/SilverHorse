# userspace/horse_images.py

HORSE_IMAGES = {
    # Формат: (порода, забарвлення): 'шлях/до/фото.png'
    ('ахалтекінець', 'вогняно-гнідий'): 'img/horses/ahaltekin_fire_chestnut.png',
    ('ахалтекінець', 'чорний'): 'img/horses/ahaltekin_full_black.png',
    ('ахалтекінець', 'світло-сірий'): 'img/horses/ahaltekin_light_gray.png',

    # Тут ви зможете додавати нові фото в майбутньому
    # ('арабська', 'сірий'): 'img/horses/arabian_gray.png',
    # ('фризька', 'чорний'): 'img/horses/friesian_black.png',
}


def get_horse_image(breed, coat_color, age=None):
    # Перевіряємо вік (дозволяємо рядки, булі, тощо)
    if age is not None:
        try:
            # Конвертуємо в число (float підтримує як цілі, так і дробові роки)
            age_val = float(age)
            if age_val <= 2:
                return 'img/horses/default_little_horse.png'
        except (ValueError, TypeError):
            # Якщо не вдалося перетворити на число — просто ігноруємо вік
            pass

    # Інакше шукаємо за породою та забарвленням
    key = (breed.lower().strip(), coat_color.lower().strip())
    return HORSE_IMAGES.get(key, 'img/horses/default_horse.png')