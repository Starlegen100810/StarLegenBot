# PU43 – Feedback Gallery (photos/videos per product)

from typing import Dict, Any, List, Optional
import time

def init(bot, resolve_lang, catalog, shop_state: Dict[str, Any]):
    """
    API:
      add_feedback(user_id, product_id, rating, text="", photos=None, videos=None) -> id
      get_gallery(product_id, limit=20) -> List[dict]
      recent(limit=20) -> List[dict]
    """
    fg = shop_state.setdefault("feedback_gallery", {})
    store: List[Dict[str, Any]] = fg.setdefault("_items", [])  # list of entries
    seq = fg.setdefault("_seq", 1)

    def add_feedback(user_id: int, product_id: str, rating: int, text: str = "",
                     photos: Optional[List[str]] = None, videos: Optional[List[str]] = None):
        nonlocal seq
        entry = {
            "id": seq,
            "user_id": user_id,
            "product_id": product_id,
            "rating": max(1, min(5, int(rating))),
            "text": text.strip(),
            "photos": photos or [],
            "videos": videos or [],
            "ts": time.time(),
        }
        store.append(entry)
        seq += 1
        return entry["id"]

    def get_gallery(product_id: str, limit: int = 20):
        items = [e for e in store if e["product_id"] == product_id]
        items.sort(key=lambda e: e["ts"], reverse=True)
        return items[:limit]

    def recent(limit: int = 20):
        items = sorted(store, key=lambda e: e["ts"], reverse=True)
        return items[:limit]

    fg["add_feedback"] = add_feedback
    fg["get_gallery"] = get_gallery
    fg["recent"] = recent


def init(bot, ctx):
    def feature(bot, m):
        bot.send_message(m.chat.id, "✅ pu43_feedback_gallery աշխատեց")
    ctx["shop_state"].setdefault("api", {})["feedback_gallery"] = feature




