from .dashboard import dashboard_view, skip_tutorial, start_tutorial
from .auth import logout_view
from .sources import sources
from .messages import messages_page, mark_message_read, block_user_view, unblock_user_view
from .profile import profile_page, account_page, language_page
from .subscription import subscription_page
from .horses import horses_page, horse_detail, buy_horse, update_horse_stat
from .equestrian import equestrian_page, manage_complex
from .market import market_view
from .shelter import shelter_view, send_to_shelter, pet_horse
from .auction import auction_list, auction_detail, create_auction, place_bid, finalize_auction, cancel_auction
"""
dashboard.py — відображення дашборду.

auth.py — логіка входу, виходу, реєстрації.

messages.py — повідомлення користувачів.

horses.py — все про коней.

market.py — ринок, купівля-продаж.

equestrian.py — кінні комплекси та рейтинги.
"""