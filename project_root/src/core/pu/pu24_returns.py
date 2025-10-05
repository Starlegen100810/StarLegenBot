# PU24 — Returns & Refunds (workflow + policy skeleton)
# Բոլոր վերադարձները lifecycle-ով՝ Pending → Approved/Rejected → Picked → Refunded/Closed

from datetime import datetime
from itertools import count

_counter = count(1001)  # local ID generator for returns

STATUSES = (
    "PENDING", "APPROVED", "REJECTED", "PICKED", "REFUNDED", "CLOSED"
)

DEFAULT_POLICY = {
    "window_days": 14,           # գնման օրվանից
    "allow_open_box": True,      # բացված, բայց օգտագործված չէ
    "restock_fee_pct": 0.0,      # եթե կա վերադասավորում
    "eligible_reasons": {
        "damaged": True,
        "wrong_item": True,
        "not_as_described": True,
        "changed_mind": True,    # կարող ես False դնել policy-ում
        "other": True,
    }
}

def _now_iso():
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def _ensure(shop_state):
    shop_state.setdefault("returns", {
        "by_id": {},          # rid -> record
        "by_user": {},        # uid -> set(rid)
        "policy": DEFAULT_POLICY.copy(),
        "timeline": [],       # audit trail: {ts, rid, actor, action, meta}
    })

def _audit(shop_state, rid, actor, action, **meta):
    shop_state["returns"]["timeline"].append({
        "ts": _now_iso(), "rid": rid, "actor": actor, "action": action, "meta": meta or {}
    })
    # trim to last N
    shop_state["returns"]["timeline"] = shop_state["returns"]["timeline"][-5000:]

def init(bot, resolve_lang, catalog, shop_state):
    """
    features['returns'] API
      - policy() / set_policy(dict) -> dict
      - create(user_id, order_id, items:list[{product_id, qty}], reason, note=None, photos: list[str]=None)
      - list_user(user_id) -> list[dict]
      - get(rid) -> dict|None
      - admin_approve(rid, admin_id, restock_fee_pct=None)
      - admin_reject(rid, admin_id, reason_text="")
      - mark_picked(rid, admin_id=None)
      - mark_refunded(rid, admin_id=None, amount=None, channel=None)
      - close(rid, admin_id=None)
      - stats() -> dict
    """
    _ensure(shop_state)
    feats = shop_state.setdefault("features", {})
    api = feats.setdefault("returns", {})

    def policy():
        return dict(shop_state["returns"]["policy"])

    def set_policy(p: dict):
        pol = shop_state["returns"]["policy"]
        for k, v in (p or {}).items():
            # թույլ ենք տալիս վերագրանցել վերը նշված բանալիները
            if k in ("window_days", "allow_open_box", "restock_fee_pct", "eligible_reasons"):
                pol[k] = v
        return dict(pol)

    def create(user_id, order_id, items, reason, note=None, photos=None):
        rid = next(_counter)
        rec = {
            "id": rid,
            "created_at": _now_iso(),
            "status": "PENDING",
            "user_id": user_id,
            "order_id": str(order_id),
            "items": [],
            "reason": str(reason or "other"),
            "note": str(note or ""),
            "photos": photos or [],
            "admin": {},
            "history": []
        }
        # normalize items
        for it in (items or []):
            pid = str(it.get("product_id"))
            qty = int(it.get("qty", 1))
            if not pid or qty <= 0:
                continue
            rec["items"].append({"product_id": pid, "qty": qty})
        shop_state["returns"]["by_id"][rid] = rec
        shop_state["returns"]["by_user"].setdefault(user_id, set()).add(rid)
        _audit(shop_state, rid, actor=user_id, action="CREATE", reason=rec["reason"])
        return rec

    def list_user(user_id):
        ids = sorted(shop_state["returns"]["by_user"].get(user_id, []))
        return [shop_state["returns"]["by_id"][rid] for rid in ids]

    def get(rid):
        return shop_state["returns"]["by_id"].get(int(rid))

    def _set_status(rid, status, actor=None, **meta):
        rec = get(rid)
        if not rec:
            return False
        if status not in STATUSES:
            return False
        rec["status"] = status
        rec["history"].append({"ts": _now_iso(), "status": status, "meta": meta or {}})
        _audit(shop_state, rid, actor=actor or "system", action=f"STATUS_{status}", **meta)
        return True

    # --- Admin actions ---
    def admin_approve(rid, admin_id, restock_fee_pct=None):
        rec = get(rid)
        if not rec:
            return False
        if restock_fee_pct is not None:
            try:
                rec["admin"]["restock_fee_pct"] = float(restock_fee_pct)
            except Exception:
                pass
        return _set_status(rid, "APPROVED", actor=admin_id)

    def admin_reject(rid, admin_id, reason_text=""):
        rec = get(rid)
        if not rec:
            return False
        rec["admin"]["reject_reason"] = str(reason_text or "")
        return _set_status(rid, "REJECTED", actor=admin_id, reason=reason_text)

    def mark_picked(rid, admin_id=None):
        return _set_status(rid, "PICKED", actor=admin_id)

    def mark_refunded(rid, admin_id=None, amount=None, channel=None):
        rec = get(rid)
        if not rec:
            return False
        if amount is not None:
            try:
                rec["admin"]["refund_amount"] = float(amount)
            except Exception:
                rec["admin"]["refund_amount"] = None
        if channel:
            rec["admin"]["refund_channel"] = str(channel)
        return _set_status(rid, "REFUNDED", actor=admin_id)

    def close(rid, admin_id=None):
        return _set_status(rid, "CLOSED", actor=admin_id)

    def stats():
        by = {s: 0 for s in STATUSES}
        for rec in shop_state["returns"]["by_id"].values():
            by[rec["status"]] = by.get(rec["status"], 0) + 1
        total = sum(by.values())
        return {"total": total, "by_status": by, "policy": policy()}

    api.update({
        "policy": policy,
        "set_policy": set_policy,
        "create": create,
        "list_user": list_user,
        "get": get,
        "admin_approve": admin_approve,
        "admin_reject": admin_reject,
        "mark_picked": mark_picked,
        "mark_refunded": mark_refunded,
        "close": close,
        "stats": stats,
    })


def init(bot, ctx):
    def feature(bot, m):
        bot.send_message(m.chat.id, "✅ pu24_returns աշխատեց")
    ctx["shop_state"].setdefault("api", {})["returns"] = feature




