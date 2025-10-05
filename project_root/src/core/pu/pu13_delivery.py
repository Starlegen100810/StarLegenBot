# src/core/pu/pu13_delivery.py
from typing import Any, Dict
from telebot import types

def _ust(shop_state: Dict, uid: int) -> Dict[str, Any]:
    scope = shop_state.setdefault("delivery", {})
    return scope.setdefault(uid, {"mode": "delivery", "data": {}, "summary_msg_id": None})

def _kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🚚 Անձամբ առնել (ՍՍ)")
    kb.row("📦 HayPost tracking")
    kb.row("⚡ Express (արագ)")
    kb.row("✍️ Գրել նշում՝ առաքման մասին")
    kb.row("⬅️ Վերադառնալ", "➡️ Շարունակել՝ վճարում")
    return kb

def _summary(data: Dict[str, Any]) -> str:
    return (
        "🚚 Առաքում\n"
        f"• Մեթոդ՝ {data.get('method','—')}\n"
        f"• Գինը՝ {data.get('price','—')}\n"
        f"• ETA՝ {data.get('eta','—')}\n"
        f"• Նշում՝ {data.get('note','—')}\n"
    )

def _send_window(bot, chat_id: int, st: Dict[str, Any]):
    txt = _summary(st["data"])
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

def open_delivery(bot, shop_state: Dict, uid: int, chat_id: int):
    st = _ust(shop_state, uid)
    st["mode"] = "delivery"
    _send_window(bot, chat_id, st)

def register(bot, ctx):
    shop_state = ctx["shop_state"]

    prices = {
        "🚚 Անձամբ առնել (ՍՍ)": ("self", 0, "—"),
        "📦 HayPost tracking": ("haypost", 1200, "ԶՁ 2–5 օր • Սփյուռք 7–14"),
        "⚡ Express (արագ)": ("express", 2500, "1–2 օրվա ընթացքում"),
    }

    @bot.message_handler(func=lambda m: m.text in prices.keys())
    def _pick(m):
        uid = m.from_user.id
        st = _ust(shop_state, uid)
        code, price, eta = prices[m.text]
        st["data"].update({"method": m.text, "price": f"{price}֏", "eta": eta})
        _send_window(bot, m.chat.id, st)

    @bot.message_handler(func=lambda m: m.text == "✍️ Գրել նշում՝ առաքման մասին")
    def _note(m):
        uid = m.from_user.id
        st = _ust(shop_state, uid)
        st["await"] = "note"
        bot.send_message(m.chat.id, "✏️ Գրեք նշումը՝")

    @bot.message_handler(func=lambda m: m.text == "➡️ Շարունակել՝ վճարում")
    def _next(m):
        uid = m.from_user.id
        st = _ust(shop_state, uid)
        if not st["data"].get("method"):
            bot.send_message(m.chat.id, "⚠️ Ընտրեք առաքման եղանակը։")
            return
        from .pu09_payment import open_payment
        st["mode"] = None
        open_payment(bot, shop_state, uid, m.chat.id)

    @bot.message_handler(func=lambda m: m.text == "⬅️ Վերադառնալ")
    def _back(m):
        from .pu06_checkout_fsm import open_checkout
        open_checkout(bot, shop_state, m.from_user.id, m.chat.id)

    @bot.message_handler(func=lambda m: isinstance(getattr(m, "text", None), str))
    def _free_text(m):
        uid = m.from_user.id
        st = shop_state.get("delivery", {}).get(uid)
        if not st or st.get("mode") != "delivery":
            return
        if st.get("await") == "note":
            st["data"]["note"] = (m.text or "").strip()
            st["await"] = None
            _send_window(bot, m.chat.id, st)

    # public
    api = shop_state.setdefault("api", {})
    api["delivery_open"] = lambda uid, chat_id: open_delivery(bot, shop_state, uid, chat_id)
