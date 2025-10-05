# src/core/pu/pu31_confirm.py
from typing import Any, Dict
from telebot import types

def _ust(shop_state: Dict, uid: int) -> Dict[str, Any]:
    scope = shop_state.setdefault("confirm", {})
    return scope.setdefault(uid, {"mode": "confirm", "summary_msg_id": None})

def _kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("✅ Հաստատել պատվերը")
    kb.row("⬅️ Վերադառնալ")
    return kb

def _calc_totals(shop_state: Dict, uid: int) -> Dict[str, Any]:
    api = shop_state.get("api", {})
    cart = api.get("cart")
    bd = cart["breakdown"](lambda u, d="hy": "hy", None, shop_state, uid) if cart else {}
    subtotal = int(bd.get("subtotal", 0))
    delivery_price = 0
    deldata = shop_state.get("delivery", {}).get(uid, {}).get("data", {})
    try:
        delivery_price = int(str(deldata.get("price","0")).replace("֏","") or 0)
    except Exception:
        delivery_price = 0
    total = subtotal + delivery_price
    return {"subtotal": subtotal, "delivery": delivery_price, "total": total}

def _summary(shop_state: Dict, uid: int) -> str:
    ch = shop_state.get("checkout", {}).get(uid, {}).get("data", {})
    dl = shop_state.get("delivery", {}).get(uid, {}).get("data", {})
    pm = shop_state.get("payment", {}).get(uid, {}).get("data", {})
    totals = _calc_totals(shop_state, uid)
    paid = int(pm.get("paid") or 0)
    overpay = max(0, paid - totals["total"])
    return (
        "📄 Պատվերի ամփոփագիր\n"
        f"Անուն՝ {ch.get('name','—')}\n"
        f"Հեռ․ {ch.get('phone','—')}\n"
        f"Քաղաք՝ {ch.get('city','—')} • Փողոց՝ {ch.get('street','—')}\n"
        f"Առաքում՝ {dl.get('method','—')} • Գին՝ {dl.get('price','—')} • ETA {dl.get('eta','—')}\n"
        f"Վճարեալ՝ {paid if paid else '—'}\n"
        f"Ընդամենը՝ {totals['total']}֏ (ապրանքներ {totals['subtotal']}֏ + առաքում {totals['delivery']}֏)\n"
        + (f"➕ Ավել վճարում՝ {overpay}֏ — կավելացվի կուպոն balance-ին\n" if overpay>0 else "")
    )

def _send_window(bot, chat_id: int, shop_state: Dict, uid: int, st: Dict[str, Any]):
    txt = _summary(shop_state, uid)
    if st.get("summary_msg_id"):
        try:
            bot.edit_message_text(txt, chat_id, st["summary_msg_id"], parse_mode=None)
            bot.send_message(chat_id, "\u2063", reply_markup=_kb())
            return
        except Exception:
            pass
    msg = bot.send_message(chat_id, txt, parse_mode=None)
    st["summary_msg_id"] = msg.message_id
    bot.send_message(chat_id, "\u2063", reply_markup=_kb())

def open_confirm(bot, shop_state: Dict, uid: int, chat_id: int):
    st = _ust(shop_state, uid)
    st["mode"] = "confirm"
    _send_window(bot, chat_id, shop_state, uid, st)

def register(bot, ctx):
    shop_state = ctx["shop_state"]

    @bot.message_handler(func=lambda m: m.text == "⬅️ Վերադառնալ")
    def _back(m):
        from .pu09_payment import open_payment
        open_payment(bot, shop_state, m.from_user.id, m.chat.id)

    @bot.message_handler(func=lambda m: m.text == "✅ Հաստատել պատվերը")
    def _confirm(m):
        uid = m.from_user.id
        totals = _calc_totals(shop_state, uid)
        paid = int(shop_state.get("payment", {}).get(uid, {}).get("data", {}).get("paid") or 0)
        over = max(0, paid - totals["total"])
        if over > 0:
            # Loyalty balance
            lstore = shop_state.setdefault("loyalty", {})
            lstore[uid] = int(lstore.get(uid, 0)) + over

        # մաքրենք զամբյուղը
        api = shop_state.get("api", {})
        cart = api.get("cart")
        if cart and "clear" in cart:
            cart["clear"](shop_state, uid)

        # reset wizard scopes
        for scope in ("checkout", "delivery", "payment", "confirm"):
            shop_state.get(scope, {}).pop(uid, None)

        bot.send_message(
            m.chat.id,
            "✅ Պատվերը ընդունված է։ Շնորհակալություն գնումների համար!\n"
            + (f"💚 +{over}֏ ավելացվեց Ձեր կուպոնին։" if over>0 else ""),
            parse_mode=None, reply_markup=types.ReplyKeyboardRemove()
        )
