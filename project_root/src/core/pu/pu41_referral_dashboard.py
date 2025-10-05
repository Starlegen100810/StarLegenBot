# src/core/pu/pu41_referral_dashboard.py
# PU41 – Referral Dashboard (basic storage + stats)

from typing import Dict, Any, List, Optional
import time, random, string

def _rand_code(prefix="STAR", n=5):
    return f"{prefix}{''.join(random.choices(string.ascii_uppercase+string.digits, k=n))}"

def _ensure(ref: dict):
    ref.setdefault("_codes", {})        # code -> referrer_id
    ref.setdefault("_owners", {})       # referrer_id -> code
    ref.setdefault("_invited", {})      # referrer_id -> set(invitee_id)
    ref.setdefault("_orders", {})       # referrer_id -> count
    ref.setdefault("_earned", {})       # referrer_id -> int (points/money)
    ref.setdefault("_used_by", {})      # invitee_id -> code
    ref.setdefault("_issued_at", {})    # code -> ts

# ---------- Programmatic API builders ----------
def _get_or_create_code(ref: dict, user_id: int) -> str:
    owners, codes, issued = ref["_owners"], ref["_codes"], ref["_issued_at"]
    code = owners.get(user_id)
    if code:
        return code
    for _ in range(5):
        c = _rand_code()
        if c not in codes:
            codes[c] = user_id
            owners[user_id] = c
            issued[c] = time.time()
            return c
    c = f"STAR{user_id}"
    codes[c] = user_id
    owners[user_id] = c
    issued[c] = time.time()
    return c

def _attach_code(ref: dict, invitee_id: int, code: str) -> bool:
    used_by, codes, invited = ref["_used_by"], ref["_codes"], ref["_invited"]
    if invitee_id in used_by:
        return False
    ref_id = codes.get(code)
    if not ref_id or ref_id == invitee_id:
        return False
    used_by[invitee_id] = code
    invited.setdefault(ref_id, set()).add(invitee_id)
    return True

def _record_order(ref: dict, user_id: int, amount: int):
    used_by, codes, orders, earned = ref["_used_by"], ref["_codes"], ref["_orders"], ref["_earned"]
    code = used_by.get(user_id)
    if not code:
        return
    ref_id = codes.get(code)
    if not ref_id:
        return
    orders[ref_id] = orders.get(ref_id, 0) + 1
    earned[ref_id] = earned.get(ref_id, 0) + int(amount * 0.03)  # 3% placeholder

def _stats(ref: dict, user_id: int) -> Dict[str, Any]:
    owners, invited, orders, earned = ref["_owners"], ref["_invited"], ref["_orders"], ref["_earned"]
    code = owners.get(user_id) or _get_or_create_code(ref, user_id)
    inv = invited.get(user_id, set())
    return {
        "code": code,
        "invited": len(inv),
        "orders": orders.get(user_id, 0),
        "earned": earned.get(user_id, 0),
    }

def _top_referrers(ref: dict, limit: int = 10):
    invited = ref["_invited"]
    items = [(uid, len(inv)) for uid, inv in invited.items()]
    items.sort(key=lambda x: x[1], reverse=True)
    return items[:limit]

# ---------- Wiring into bot ----------
def register(bot, ctx):
    """
    PU41 Referral Dashboard
      • Programmatic API: shop_state['referrals']{ get_or_create_code, attach_code, record_order, stats, top_referrers }
      • Reply-menu hook: api['referral_dashboard']  (mapped from 🤝 Գործընկերներ)
    """
    shop_state: Dict[str, Any] = ctx["shop_state"]
    ref = shop_state.setdefault("referrals", {})
    _ensure(ref)

    # Expose programmatic API
    ref.update({
        "get_or_create_code": lambda user_id: _get_or_create_code(ref, user_id),
        "attach_code":        lambda invitee_id, code: _attach_code(ref, invitee_id, code),
        "record_order":       lambda user_id, amount: _record_order(ref, user_id, amount),
        "stats":              lambda user_id: _stats(ref, user_id),
        "top_referrers":      lambda limit=10: _top_referrers(ref, limit),
    })

    # Reply-menu entry (FEATURE_MAP → "referral_dashboard")
    api = shop_state.setdefault("api", {})
    def _entry(bot2, m):
        uid = m.from_user.id
        code = ref["get_or_create_code"](uid)
        st = ref["stats"](uid)
        lines = [
            "🤝 Referral Dashboard",
            f"Քո հրավիրելու կոդը: `{code}`",
            "",
            "Ինչպես օգտագործել:",
            " • Տարածիր այս կոդը ընկերների հետ",
            " • Նրանք կարող են մուտքագրել/կցել կոդը առաջին գնումից առաջ",
            "",
            f"📈 Քո վիճակագրությունը",
            f" • Հրավիրվածներ: {st['invited']}",
            f" • Նրանց պատվերները: {st['orders']}",
            f" • Կուտակած բոնուս (3% placeholder): {st['earned']}",
        ]
        try:
            bot2.send_message(m.chat.id, "\n".join(lines), parse_mode=None)
        except Exception:
            pass

    api["referral_dashboard"] = _entry




