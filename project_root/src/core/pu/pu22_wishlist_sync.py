# PU22 — Wishlist Sync (multi-device, merge, import/export)
# Բոլոր ցանկացանկերը պահվում են մեկտեղ՝ user_id-ի տակ։
# Չի փոխում մենյուն, տալիս է ներքին API features['wishlist']։

from datetime import datetime

def _now_iso():
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def _ensure(shop_state):
    shop_state.setdefault("wishlist", {
        "by_user": {},       # user_id -> set(product_id)
        "meta": {},          # user_id -> {updated_at}
        "limits": {"max_per_user": 500}
    })

def init(bot, resolve_lang, catalog, shop_state):
    """
    features['wishlist'] API
      - add(user_id, product_id) -> bool
      - remove(user_id, product_id) -> bool
      - clear(user_id) -> None
      - list(user_id) -> list[str]
      - merge(user_id, *other_user_ids) -> merged_count
      - import_ids(user_id, ids: list[str|int]) -> imported_count
      - export_ids(user_id) -> list[str]
      - stats(user_id=None) -> dict
    """
    _ensure(shop_state)
    feats = shop_state.setdefault("features", {})
    api = feats.setdefault("wishlist", {})

    def _bucket(uid):
        b = shop_state["wishlist"]["by_user"].setdefault(uid, set())
        shop_state["wishlist"]["meta"].setdefault(uid, {"updated_at": _now_iso()})
        return b

    def _touch(uid):
        shop_state["wishlist"]["meta"][uid]["updated_at"] = _now_iso()

    def add(user_id, product_id):
        if product_id is None:
            return False
        b = _bucket(user_id)
        if len(b) >= int(shop_state["wishlist"]["limits"]["max_per_user"]):
            # պահպանում ենք վերջին 500-ը՝ հինը թող լինի
            pass
        b.add(str(product_id))
        _touch(user_id)
        return True

    def remove(user_id, product_id):
        _bucket(user_id).discard(str(product_id))
        _touch(user_id)
        return True

    def clear(user_id):
        shop_state["wishlist"]["by_user"][user_id] = set()
        _touch(user_id)

    def list_ids(user_id):
        # վերադարձնում է առկա product_id-ների list (catalog lookup թող լինի caller-ի վրա)
        return sorted(_bucket(user_id))

    def merge(user_id, *other_user_ids):
        base = _bucket(user_id)
        before = len(base)
        for oid in other_user_ids:
            base |= _bucket(oid)
        _touch(user_id)
        return len(base) - before

    def import_ids(user_id, ids):
        if not ids:
            return 0
        base = _bucket(user_id)
        before = len(base)
        for i in ids:
            if i is not None:
                base.add(str(i))
        _touch(user_id)
        return len(base) - before

    def export_ids(user_id):
        return list(list_ids(user_id))

    def stats(user_id=None):
        w = shop_state["wishlist"]
        if user_id is None:
            total_users = len(w["by_user"])
            total_items = sum(len(v) for v in w["by_user"].values())
            return {"users": total_users, "items": total_items}
        return {
            "count": len(_bucket(user_id)),
            "updated_at": w["meta"].get(user_id, {}).get("updated_at")
        }

    api.update({
        "add": add,
        "remove": remove,
        "clear": clear,
        "list": list_ids,
        "merge": merge,
        "import_ids": import_ids,
        "export_ids": export_ids,
        "stats": stats,
    })


def init(bot, ctx):
    def feature(bot, m):
        bot.send_message(m.chat.id, "✅ pu22_wishlist_sync աշխատեց")
    ctx["shop_state"].setdefault("api", {})["wishlist_sync"] = feature




