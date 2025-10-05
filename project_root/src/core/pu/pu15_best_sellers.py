# src/core/pu/pu15_best_sellers.py
# PU15 – Best Sellers Logic (Top3, fixed +2 growth per order, labels, admin control)
from __future__ import annotations
from typing import Dict, Any, List
from datetime import datetime

def _iso(): return datetime.utcnow().isoformat()

def _db(shop_state):
    root = shop_state.setdefault("bestsellers", {})
    root.setdefault("top3", [])         # [product_id, ...]
    root.setdefault("counters", {})     # product_id -> fake_sales
    root.setdefault("history", [])      # records
    return root

def set_top3(shop_state, ids: List[int]):
    db = _db(shop_state)
    db["top3"] = [int(x) for x in ids][:3]
    return list(db["top3"])

def get_top3(shop_state) -> List[int]:
    return list(_db(shop_state)["top3"])

def inc_for_order(shop_state, product_ids: List[int], order_id: int, uid: int):
    """Increase fake counters +2 for each product that is in Top3."""
    db = _db(shop_state); top = set(db["top3"])
    touched = []
    for pid in product_ids:
        pid = int(pid)
        if pid in top:
            db["counters"][pid] = db["counters"].get(pid, 0) + 2
            touched.append(pid)
    if touched:
        db["history"].append({"ts": _iso(), "order_id": order_id, "uid": uid, "inc": 2, "items": touched})

def label_for(shop_state, product_id: int) -> str | None:
    if int(product_id) in set(get_top3(shop_state)):
        return "🔥 Լավագույն վաճառվող"
    return None

def get_counter(shop_state, product_id: int) -> int:
    return _db(shop_state)["counters"].get(int(product_id), 0)

def summary(shop_state) -> Dict[str, Any]:
    db = _db(shop_state)
    return {"top3": db["top3"], "counters": dict(db["counters"])}

def _register_api(shop_state):
    api = shop_state.setdefault("api", {})
    api.setdefault("bestsellers", {}).update({
        "top3":          lambda: get_top3(shop_state),
        "set_top3":      lambda ids: set_top3(shop_state, ids),
        "label_for":     lambda pid: label_for(shop_state, pid),
        "counter":       lambda pid: get_counter(shop_state, pid),
        "summary":       lambda: summary(shop_state),
        "inc_for_order": lambda product_ids, order_id, uid: inc_for_order(shop_state, product_ids, order_id, uid),
    })

def register(bot, ctx):
    """
    PU15 Best Sellers:
      • Admin: /set_top3 <id1,id2,id3>  • /top3  • /bs_info <PRODUCT_ID>
      • Counters: +2 per paid order on Top3 items (event:order:paid)
      • Reply-menu hook: api['best_sellers'] — բացում է արագ info/summary
    """
    shop_state = ctx["shop_state"]
    _register_api(shop_state)

    # ✅ Reply-menu կոճակի hook (🏆 Լավագույններ)
    api = shop_state.setdefault("api", {})
    def _entry(bot2, m):
        db = summary(shop_state)
        top = db.get("top3") or []
        if not top:
            bot2.send_message(m.chat.id, "🏆 TOP3 դեռ կարգավորված չէ։ Օգտ․ /set_top3 1,2,3")
            return
        lines = ["🏆 TOP3 Best Sellers:"]
        for i, pid in enumerate(top, start=1):
            cnt = get_counter(shop_state, pid)
            lines.append(f"{i}) #{pid} • *վաճառված {cnt}*")
        bot2.send_message(m.chat.id, "\n".join(lines), parse_mode=None)
    api["best_sellers"] = _entry

    # ✅ Bot event/command hookups (եթե քո bot-ը ունի bot.on(event))
    on = getattr(bot, "on", None)
    if not callable(on):
        return

    @on("cmd:/set_top3")
    def _set(ctx2):
        parts = (ctx2.get("text") or "").split(maxsplit=1)
        if len(parts) < 2:
            bot.send(ctx2["user_id"], "Օգտ․ /set_top3 <id1,id2,id3>")
            return
        try:
            ids = [int(p) for p in parts[1].replace(" ", "").split(",") if p]
        except Exception:
            bot.send(ctx2["user_id"], "Սխալ ձևաչափ։ Օգտ․ /set_top3 101,102,103")
            return
        top = set_top3(shop_state, ids)
        bot.send(ctx2["user_id"], f"OK Top3 → {top}")

    @on("cmd:/top3")
    def _show(ctx2):
        db = summary(shop_state)
        if not db["top3"]:
            bot.send(ctx2["user_id"], "🏆 TOP3 — դատարկ է")
            return
        view = [f"{i+1}) #{pid} → վաճառված* {db['counters'].get(pid,0)}"
                for i, pid in enumerate(db["top3"])]
        bot.send(ctx2["user_id"], "🏆 TOP3 Best Sellers\n" + "\n".join(view))

    @on("cmd:/bs_info")
    def _info(ctx2):
        parts = (ctx2.get("text") or "").split()
        if len(parts) < 2:
            bot.send(ctx2["user_id"], "Օգտ․ /bs_info <PRODUCT_ID>")
            return
        try:
            pid = int(parts[1])
        except Exception:
            bot.send(ctx2["user_id"], "Սխալ PRODUCT_ID")
            return
        label = label_for(shop_state, pid) or "—"
        cnt = get_counter(shop_state, pid)
        bot.send(ctx2["user_id"], f"Ապրանք #{pid}: {label} | *վաճառված {cnt}*")

    # երբ պատվերը վճարվում է, բարձրացնենք հաշվիչները Top3 ապրանքների համար
    @on("event:order:paid")
    def _bump(ctx2):
        uid = ctx2["user_id"]
        oid = int(ctx2.get("order_id", 0))
        product_ids = ctx2.get("product_ids", [])
        if product_ids:
            inc_for_order(shop_state, product_ids, oid, uid)




