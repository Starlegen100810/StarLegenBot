# PU34 – Smart Reminder (abandoned cart / browse reminder)
# Այստեղ միայն պլագինի helper-ներն են. ոչ մի push չի ուղարկվում ինքնուրույն։
# Հետագայում main scheduler-ը կարող է հարցնել due reminder-ները և ուղարկել։

from typing import Dict, Any, List, Tuple
import time

def init(bot, resolve_lang, catalog, shop_state: Dict[str, Any]):
    """
    Reminder helpers.
    API:
      schedule_abandoned_cart(user_id, ttl_min=60)
      cancel_on_checkout(user_id)
      get_due(now=None) -> List[(user_id, reason)]
      stats() -> dict
    """
    config    = shop_state.setdefault("config", {})
    reminder  = shop_state.setdefault("reminder", {})
    features  = shop_state.setdefault("features", {})
    features.setdefault("smart_reminder", True)

    # Default thresholds/config
    cfg = config.setdefault("reminder", {})
    cfg.setdefault("abandoned_cart_ttl_min", 60)
    cfg.setdefault("max_per_day", 2)

    # Very simple in-memory queue: {user_id: [{"ts":..., "ttl":..., "reason":"cart"}]}
    queue = reminder.setdefault("_queue", {})

    def schedule_abandoned_cart(user_id: int, ttl_min: int = None):
        if not features.get("smart_reminder", True):
            return False
        ttl = (ttl_min if ttl_min is not None else cfg["abandoned_cart_ttl_min"]) * 60
        arr = queue.setdefault(user_id, [])
        arr.append({"ts": time.time(), "ttl": ttl, "reason": "cart"})
        return True

    def cancel_on_checkout(user_id: int):
        if user_id in queue:
            # ջնջում ենք միայն cart reminder-ները
            arr = [x for x in queue[user_id] if x.get("reason") != "cart"]
            if arr:
                queue[user_id] = arr
            else:
                queue.pop(user_id, None)
        return True

    def get_due(now: float = None) -> List[Tuple[int, str]]:
        if not features.get("smart_reminder", True):
            return []
        now = now or time.time()
        due: List[Tuple[int, str]] = []
        to_delete = []
        for uid, items in list(queue.items()):
            keep = []
            for it in items:
                if now - it["ts"] >= it["ttl"]:
                    due.append((uid, it.get("reason", "generic")))
                else:
                    keep.append(it)
            if keep:
                queue[uid] = keep
            else:
                to_delete.append(uid)
        for uid in to_delete:
            queue.pop(uid, None)
        return due

    def stats():
        return {
            "enabled": features.get("smart_reminder", True),
            "queued_users": len(queue),
            "items_total": sum(len(v) for v in queue.values()),
            "cfg": dict(cfg),
        }

    reminder["schedule_abandoned_cart"] = schedule_abandoned_cart
    reminder["cancel_on_checkout"] = cancel_on_checkout
    reminder["get_due"] = get_due
    reminder["stats"] = stats


def init(bot, ctx):
    def feature(bot, m):
        bot.send_message(m.chat.id, "✅ pu34_smart_reminder աշխատեց")
    ctx["shop_state"].setdefault("api", {})["smart_reminder"] = feature



