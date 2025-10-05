# src/core/pu/pu23_history.py
# PU23 — Activity / View History (in-memory)

from collections import deque
from datetime import datetime
from typing import Optional, List, Dict, Any

def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def _ensure(shop_state: dict) -> None:
    shop_state.setdefault("history", {
        "by_user": {},     # user_id -> {"views": deque, "search": deque, "orders": deque}
        "limits": {"views": 50, "search": 20, "orders": 50}
    })

def _bucket(shop_state: dict, uid: int) -> dict:
    _ensure(shop_state)
    hroot = shop_state["history"]
    h = hroot["by_user"].setdefault(uid, {})
    lim = hroot["limits"]
    h.setdefault("views",  deque(maxlen=int(lim["views"])))
    h.setdefault("search", deque(maxlen=int(lim["search"])))
    h.setdefault("orders", deque(maxlen=int(lim["orders"])))
    return h

# -------- Feature (programmatic) API --------
def _add_view(shop_state: dict, user_id: int, product_id: str|int) -> bool:
    b = _bucket(shop_state, user_id)
    b["views"].append({"ts": _now_iso(), "product_id": str(product_id)})
    return True

def _add_search(shop_state: dict, user_id: int, query: str) -> bool:
    q = (query or "").strip()
    if not q:
        return False
    b = _bucket(shop_state, user_id)
    b["search"].append({"ts": _now_iso(), "q": q})
    return True

def _add_order(shop_state: dict, user_id: int, order_id: str|int, total: Optional[float]=None, currency: str="֏") -> bool:
    b = _bucket(shop_state, user_id)
    rec: Dict[str, Any] = {"ts": _now_iso(), "order_id": str(order_id), "currency": currency}
    if total is not None:
        try:
            rec["total"] = float(total)
        except Exception:
            rec["total"] = None
    b["orders"].append(rec)
    return True

def _last_views(shop_state: dict, user_id: int, n: int = 10) -> List[dict]:
    return list(_bucket(shop_state, user_id)["views"])[-int(n):]

def _last_searches(shop_state: dict, user_id: int, n: int = 10) -> List[dict]:
    return list(_bucket(shop_state, user_id)["search"])[-int(n):]

def _last_orders(shop_state: dict, user_id: int, n: int = 10) -> List[dict]:
    return list(_bucket(shop_state, user_id)["orders"])[-int(n):]

def _clear(shop_state: dict, user_id: int, kind: Optional[str] = None) -> bool:
    b = _bucket(shop_state, user_id)
    if kind in (None, "views"):
        b["views"].clear()
    if kind in (None, "search"):
        b["search"].clear()
    if kind in (None, "orders"):
        b["orders"].clear()
    return True

def _stats(shop_state: dict, user_id: int) -> Dict[str, int]:
    b = _bucket(shop_state, user_id)
    return {"views": len(b["views"]), "search": len(b["search"]), "orders": len(b["orders"])}

# -------- Wiring into bot --------
def register(bot, ctx):
    """
    PU23 History
      • features['history'] API: add_view/add_search/add_order/last_* /clear /stats
      • reply-menu hook api['history']  -> ցույց է տալիս օգտագործողի activity ամփոփ
      • ցանկության դեպքում կարող ես այլ PU-երից programmatic կանչել features['history'] API-ն
    """
    shop_state = ctx["shop_state"]

    # programmatic feature api
    feats = shop_state.setdefault("features", {})
    feats.setdefault("history", {}).update({
        "add_view":   lambda user_id, product_id: _add_view(shop_state, user_id, product_id),
        "add_search": lambda user_id, query: _add_search(shop_state, user_id, query),
        "add_order":  lambda user_id, order_id, total=None, currency="֏": _add_order(shop_state, user_id, order_id, total, currency),
        "last_views": lambda user_id, n=10: _last_views(shop_state, user_id, n),
        "last_searches": lambda user_id, n=10: _last_searches(shop_state, user_id, n),
        "last_orders": lambda user_id, n=10: _last_orders(shop_state, user_id, n),
        "clear":      lambda user_id, kind=None: _clear(shop_state, user_id, kind),
        "stats":      lambda user_id: _stats(shop_state, user_id),
    })

    # reply-menu hook: FEATURE_MAP → "👤 իմ էջ" -> "history"
    api = shop_state.setdefault("api", {})
    def _entry(bot2, m):
        uid = m.from_user.id if hasattr(m, "from_user") else None
        if not uid:
            bot2.send_message(m.chat.id, "Չհաջողվեց որոշել օգտվողին։")
            return
        s = _stats(shop_state, uid)
        v = _last_views(shop_state, uid, 5)
        sr = _last_searches(shop_state, uid, 5)
        od = _last_orders(shop_state, uid, 5)

        lines = [
            "👤 Իմ էջ — վերջին ակտիվություն",
            f"👁 Դիտումներ: {s['views']}  |  🔎 Որոնումներ: {s['search']}  |  🧾 Պատվերներ: {s['orders']}",
        ]
        if v:
            lines.append("\nՎերջին ապրանքների դիտումներ:")
            for it in v:
                lines.append(f" • #{it.get('product_id')} ({it.get('ts')})")
        if sr:
            lines.append("\nՎերջին որոնումներ:")
            for it in sr:
                lines.append(f" • “{it.get('q')}” ({it.get('ts')})")
        if od:
            lines.append("\nՎերջին պատվերներ:")
            for it in od:
                tot = it.get("total")
                cur = it.get("currency", "֏")
                suffix = f" — {tot} {cur}" if tot not in (None, "") else ""
                lines.append(f" • №{it.get('order_id')}{suffix} ({it.get('ts')})")

        if len(lines) == 2:
            lines.append("\nԴեռ պատմություն չկա 🙂")
        bot2.send_message(m.chat.id, "\n".join(lines), parse_mode=None)

    api["history"] = _entry




