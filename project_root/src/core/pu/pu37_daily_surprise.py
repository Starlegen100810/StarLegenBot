# PU37 – Daily Surprise (24h special offer / gift)
# Պահում է մեկ օրում մեկ առաջարկի տվյալները. reset ամեն 24 ժամում։

import time
from typing import Dict, Any

def init(bot, resolve_lang, catalog, shop_state: Dict[str, Any]):
    """
    API:
      set_offer(product_id, discount_pct, expires=None)
      get_offer() -> dict | None
      clear()
    """
    ds = shop_state.setdefault("daily_surprise", {})

    state = ds.setdefault("_state", {"offer": None, "ts": 0})

    def set_offer(product_id: str, discount_pct: int, expires: float = None):
        state["offer"] = {
            "product_id": product_id,
            "discount": discount_pct,
            "expires": expires or (time.time() + 24 * 3600),
        }
        state["ts"] = time.time()

    def get_offer():
        offer = state.get("offer")
        if not offer:
            return None
        if offer["expires"] and time.time() > offer["expires"]:
            clear()
            return None
        return offer

    def clear():
        state["offer"] = None
        state["ts"] = time.time()

    ds["set_offer"] = set_offer
    ds["get_offer"] = get_offer
    ds["clear"] = clear


def init(bot, ctx):
    def feature(bot, m):
        bot.send_message(m.chat.id, "✅ pu37_daily_surprise աշխատեց")
    ctx["shop_state"].setdefault("api", {})["daily_surprise"] = feature




