# src/core/pu/pu21_referral.py
# PU21 — Referral & Invite (codes, tracking, rewards)

from __future__ import annotations
import random, string
from datetime import datetime
from telebot import types

def _now_iso():
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def _ensure_structs(shop_state):
    shop_state.setdefault("referral", {
        "codes": {},     # user_id -> code
        "owners": {},    # code -> user_id
        "invites": {},   # invitee_user_id -> referrer_user_id
        "stats": {},     # user_id -> {...}
        "rules": {
            "first_order_bonus_pct": 10.0,
            "repeat_order_bonus_pct": 3.0,
            "max_discount_per_order_pct": 20.0,
        },
    })

def _gen_code(prefix="STAR"):
    s = "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))
    return f"{prefix}{s}"

def init(bot, ctx):
    """
    Ստանդարտ ստորագրություն՝ init(bot, ctx)
    ctx = {"resolve_lang": ..., "catalog": ..., "shop_state": ...}
    """
    resolve_lang = ctx["resolve_lang"]
    catalog      = ctx["catalog"]
    shop_state   = ctx["shop_state"]

    _ensure_structs(shop_state)
    feats = shop_state.setdefault("features", {})
    api   = feats.setdefault("referral", {})

    def _stat(uid):
        ref = shop_state["referral"]
        s = ref["stats"].setdefault(uid, {
            "invited": 0,
            "orders_from_invited": 0,
            "bonus_pct": 0.0,
            "bonus_balance": 0.0,
            "updated_at": _now_iso(),
        })
        return s

    def my_code(user_id: int) -> str:
        ref = shop_state["referral"]
        if user_id in ref["codes"]:
            return ref["codes"][user_id]
        for _ in range(5):
            c = _gen_code()
            if c not in ref["owners"]:
                ref["codes"][user_id] = c
                ref["owners"][c] = user_id
                break
        return ref["codes"][user_id]

    def attach(invitee_user_id: int, code: str) -> bool:
        ref = shop_state["referral"]
        if invitee_user_id in ref["invites"]:
            return False
        owner = ref["owners"].get(str(code).strip())
        if not owner or owner == invitee_user_id:
            return False
        ref["invites"][invitee_user_id] = owner
        _stat(owner)["invited"] += 1
        return True

    def record_order(invitee_user_id: int, order_total: float):
        ref   = shop_state["referral"]
        owner = ref["invites"].get(invitee_user_id)
        if not owner:
            return {"applied": False, "reason": "no_referrer"}

        rules = ref["rules"]
        st    = _stat(owner)
        flag  = f"first_done_with_{invitee_user_id}"
        first_time = st.get(flag) is None

        pct   = float(rules["first_order_bonus_pct"] if first_time else rules["repeat_order_bonus_pct"])
        bonus = max(0.0, float(order_total or 0) * pct / 100.0)

        st["bonus_balance"] += bonus
        st["orders_from_invited"] += 1
        st["updated_at"] = _now_iso()
        if first_time:
            st[flag] = True

        return {
            "applied": True,
            "referrer_id": owner,
            "invitee_id": invitee_user_id,
            "pct": pct,
            "bonus_added": round(bonus, 2),
            "bonus_balance": round(st["bonus_balance"], 2),
        }

    def stats(user_id: int):
        s = _stat(user_id)
        ref = shop_state["referral"]
        return {
            "invited": s["invited"],
            "orders_from_invited": s["orders_from_invited"],
            "bonus_balance": round(s["bonus_balance"], 2),
            "updated_at": s["updated_at"],
            "code": ref["codes"].get(user_id),
        }

    def rules():
        return dict(shop_state["referral"]["rules"])

    def set_rules(new_rules: dict):
        r = shop_state["referral"]["rules"]
        for k, v in (new_rules or {}).items():
            if k in r:
                try: r[k] = float(v)
                except Exception: pass
        return dict(r)

    # expose API
    api.update({
        "my_code": my_code,
        "attach": attach,
        "record_order": record_order,
        "stats": stats,
        "rules": rules,
        "set_rules": set_rules,
    })

    # --------- Simple admin/user commands for smoke test ---------
    @bot.message_handler(commands=['refcode'])
    def _cmd_refcode(m: types.Message):
        code = my_code(m.from_user.id)
        bot.send_message(m.chat.id, f"🔗 Քո հրավիրելու կոդը՝ {code}\n"
                                    f"Կիսվիր այս կոդով, ու ընկերոջ առաջին պատվերից կստանաս բոնուս։",
                         parse_mode=None)

    # /attach STARXXXXX  → օգտվողը մուտքագրում է ստացած կոդը
    @bot.message_handler(commands=['attach'])
    def _cmd_attach(m: types.Message):
        parts = (m.text or "").split(maxsplit=1)
        if len(parts) < 2:
            bot.send_message(m.chat.id, "Օգտագործիր՝ /attach ՔՈ_ՍՏԱՑԱԾ_ԿՈԴԸ", parse_mode=None)
            return
        ok = attach(m.from_user.id, parts[1])
        bot.send_message(m.chat.id, "✅ Կցվեց հրավիրողին։" if ok else "⚠️ Չստացվեց կցել։",
                         parse_mode=None)

    # /refstats
    @bot.message_handler(commands=['refstats'])
    def _cmd_refstats(m: types.Message):
        s = stats(m.from_user.id)
        txt = (f"👥 Հրավիրվածներ՝ {s['invited']}\n"
               f"🧾 Պատվերներ՝ {s['orders_from_invited']}\n"
               f"💰 Բալանս՝ {s['bonus_balance']}\n"
               f"🔗 Կոդ՝ {s['code'] or '—'}")
        bot.send_message(m.chat.id, txt, parse_mode=None)

    # /buytest 10000  → միայն smoke-test, գրանցում ենք «հրավիրվածի» պատվեր
    @bot.message_handler(commands=['buytest'])
    def _cmd_buytest(m: types.Message):
        parts = (m.text or "").split(maxsplit=1)
        try:
            total = float(parts[1]) if len(parts) > 1 else 0.0
        except Exception:
            total = 0.0
        res = record_order(m.from_user.id, total)
        if res.get("applied"):
            bot.send_message(
                m.chat.id,
                f"✅ Գրանցվեց։ Referrer={res['referrer_id']} • Bonus +{res['bonus_added']} • Balance={res['bonus_balance']}",
                parse_mode=None
            )
        else:
            bot.send_message(m.chat.id, "ℹ️ Հրավիրված/հրավիրող կապ չգտնվեց։ /attach CODE", parse_mode=None)



