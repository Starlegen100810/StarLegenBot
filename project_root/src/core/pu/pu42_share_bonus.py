# PU42 – Share Bonus (post-order share -> instant coupon placeholder)

from typing import Dict, Any
import time
import random
import string

def _coupon(prefix="SHARE", n=6):
    return f"{prefix}-{''.join(random.choices(string.ascii_uppercase+string.digits, k=n))}"

def init(bot, resolve_lang, catalog, shop_state: Dict[str, Any]):
    """
    API:
      mark_shared(order_id, user_id) -> dict {code, pct, expires}
      get_coupon(code) -> dict|None
    """
    sb = shop_state.setdefault("share_bonus", {})
    coupons = sb.setdefault("_coupons", {})      # code -> {user_id, pct, expires, order_id, ts}

    def mark_shared(order_id: str, user_id: int):
        code = _coupon()
        c = {
            "user_id": user_id,
            "order_id": order_id,
            "pct": 5,  # default 5% off
            "expires": time.time() + 7 * 24 * 3600,
            "ts": time.time(),
        }
        coupons[code] = c
        return {"code": code, "pct": c["pct"], "expires": c["expires"]}

    def get_coupon(code: str):
        c = coupons.get(code)
        if not c:
            return None
        if c["expires"] < time.time():
            return None
        return c

    sb["mark_shared"] = mark_shared
    sb["get_coupon"] = get_coupon


def init(bot, ctx):
    def feature(bot, m):
        bot.send_message(m.chat.id, "✅ pu42_share_bonus աշխատեց")
    ctx["shop_state"].setdefault("api", {})["share_bonus"] = feature




