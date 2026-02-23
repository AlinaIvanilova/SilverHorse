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


def get_horse_image(breed, coat_color):
    """
    Повертає шлях до фото коня на основі породи та забарвлення
    Якщо комбінація не знайдена, повертає фото за замовчуванням
    """
    key = (breed.lower().strip(), coat_color.lower().strip())
    return HORSE_IMAGES.get(key, 'img/horses/default_horse.png')


