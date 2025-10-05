# src/core/pu/pu09_payment.py
from typing import Any, Dict
from telebot import types

PAY_METHODS = ["📲 IDram", "🏦 Telcell", "💳 Քարտ", "⚡ FastShift", "🧊 Alipay/USDT", "💵 Կանխիկ (COD)"]

def _ust(shop_state: Dict, uid: int) -> Dict[str, Any]:
    scope = shop_state.setdefault("payment", {})
    return scope.setdefault(uid, {"mode": "payment", "data": {"method": "", "account": ""}, "await": None, "summary_msg_id": None})

ACCOUNTS = {
    "📲 IDram": "123456789",
    "🏦 Telcell": "123456789",
    "💳 Քարտ": "5555 4444 3333 2222",
    "⚡ FastShift": "@your_username",
    "🧊 Alipay/USDT": "USDT-TRC20: Txxxx…",
    "💵 Կանխիկ (COD)": "Ընդունում ենք առաքման պահին",
}

def _kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for m in PAY_METHODS:
        kb.row(m)
    kb.row("📎 Կցել անդորագիր", "🔢 Մուտքագրել վճարված գումարը")
    kb.row("⬅️ Վերադառնալ", "➡️ Շարունակել՝ ամփոփում")
    return kb

def _summary(data: Dict[str, Any]) -> str:
    return (
        "💳 Վճարում\n"
        f"• Եղանակ՝ {data.get('method','—')}\n"
        f"• Մանրամասներ՝ {data.get('account','—')}\n"
        f"• Վճարված գումար՝ {data.get('paid','—')}\n"
        f"• Անդորագիր՝ {'✓' if data.get('receipt') else '—'}\n"
        "Ավարտելուց հետո սեղմեք «➡️ Շարունակել՝ ամփոփում»։"
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

def open_payment(bot, shop_state: Dict, uid: int, chat_id: int):
    st = _ust(shop_state, uid)
    if not st["data"]["method"]:
        st["data"]["method"] = "💵 Կանխիկ (COD)"
        st["data"]["account"] = ACCOUNTS["💵 Կանխիկ (COD)"]
    st["mode"] = "payment"
    _send_window(bot, chat_id, st)

def register(bot, ctx):
    shop_state = ctx["shop_state"]

    @bot.message_handler(func=lambda m: m.text in PAY_METHODS)
    def _pick_method(m):
        uid = m.from_user.id
        st = _ust(shop_state, uid)
        st["data"]["method"] = m.text
        st["data"]["account"] = ACCOUNTS.get(m.text, "—")
        _send_window(bot, m.chat.id, st)

    @bot.message_handler(func=lambda m: m.text == "📎 Կցել անդորագիր", content_types=['text'])
    def _ask_receipt(m):
        uid = m.from_user.id
        st = _ust(shop_state, uid)
        st["await"] = "receipt"
        bot.send_message(m.chat.id, "📎 Ուղարկեք անդորագրի նկար/ֆայլը։")

    @bot.message_handler(content_types=['photo', 'document'])
    def _on_file(m):
        uid = m.from_user.id
        st = shop_state.get("payment", {}).get(uid)
        if not st or st.get("mode") != "payment":
            return
        if st.get("await") == "receipt":
            st["data"]["receipt"] = True
            st["await"] = None
            _send_window(bot, m.chat.id, st)

    @bot.message_handler(func=lambda m: m.text == "🔢 Մուտքագրել վճարված գումարը")
    def _ask_amount(m):
        uid = m.from_user.id
        st = _ust(shop_state, uid)
        st["await"] = "paid"
        bot.send_message(m.chat.id, "Գրեք գումարը թվերով՝ օրինակ 1400")

    @bot.message_handler(func=lambda m: m.text == "➡️ Շարունակել՝ ամփոփում")
    def _next(m):
        uid = m.from_user.id
        st = _ust(shop_state, uid)
        from .pu31_confirm import open_confirm
        st["mode"] = None
        open_confirm(bot, shop_state, uid, m.chat.id)

    @bot.message_handler(func=lambda m: m.text == "⬅️ Վերադառնալ")
    def _back(m):
        from .pu13_delivery import open_delivery
        open_delivery(bot, shop_state, m.from_user.id, m.chat.id)

    @bot.message_handler(func=lambda m: isinstance(getattr(m, "text", None), str))
    def _free_text(m):
        uid = m.from_user.id
        st = shop_state.get("payment", {}).get(uid)
        if not st or st.get("mode") != "payment":
            return
        if st.get("await") == "paid":
            txt = (m.text or "").strip().replace(" ", "")
            if not txt.isdigit():
                bot.send_message(m.chat.id, "Գրեք միայն թվերով, օրինակ՝ 1400")
                return
            st["data"]["paid"] = int(txt)
            st["await"] = None
            _send_window(bot, m.chat.id, st)

    # public
    shop_state.setdefault("api", {})["payment_open"] = lambda uid, chat_id: open_payment(bot, shop_state, uid, chat_id)
