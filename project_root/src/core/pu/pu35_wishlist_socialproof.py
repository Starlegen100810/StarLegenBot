# PU35 – Wishlist + Social Proof ("liked by N users")
# Պահում ենք like-երի հաշվիչն ու user-level պաշտպանությունը կրկնակի հաշվելուց։

from typing import Dict, Any, Set, DefaultDict
from collections import defaultdict

def init(bot, resolve_lang, catalog, shop_state: Dict[str, Any]):
    """
    API:
      like(product_id, user_id) -> bool
      unlike(product_id, user_id) -> bool
      get_count(product_id) -> int
      get_badge(product_id, lang=None) -> str  # "Liked by 12 users" (ARM/RU/EN)
    """
    social = shop_state.setdefault("socialproof", {})
    store_counts: DefaultDict[str, int] = social.setdefault("_counts", defaultdict(int))
    store_users: DefaultDict[str, Set[int]] = social.setdefault("_users", defaultdict(set))

    # Simple i18n copy
    def _badge_text(n: int, lang: str) -> str:
        if lang == "ru":
            return f"Понравилось {n} пользователям" if n != 1 else "Понравилось 1 пользователю"
        if lang == "en":
            return f"Liked by {n} users" if n != 1 else "Liked by 1 user"
        # default: Armenian
        return f"Հավանել է {n} օգտվող" if n != 1 else "Հավանել է 1 օգտվող"

    def _lang():
        code = resolve_lang() if callable(resolve_lang) else "hy"
        return (code or "hy")[:2].lower()

    def like(product_id: str, user_id: int) -> bool:
        users = store_users[product_id]
        if user_id in users:
            return False
        users.add(user_id)
        store_counts[product_id] += 1
        return True

    def unlike(product_id: str, user_id: int) -> bool:
        users = store_users[product_id]
        if user_id not in users:
            return False
        users.remove(user_id)
        store_counts[product_id] = max(0, store_counts[product_id] - 1)
        return True

    def get_count(product_id: str) -> int:
        return int(store_counts.get(product_id, 0))

    def get_badge(product_id: str, lang: str = None) -> str:
        n = get_count(product_id)
        code = (lang or _lang())
        return _badge_text(n, code)

    social["inc_like"] = like
    social["dec_like"] = unlike
    social["get_count"] = get_count
    social["get_badge"] = get_badge


def init(bot, ctx):
    def feature(bot, m):
        bot.send_message(m.chat.id, "✅ pu35_wishlist_socialproof աշխատեց")
    ctx["shop_state"].setdefault("api", {})["wishlist_socialproof"] = feature




