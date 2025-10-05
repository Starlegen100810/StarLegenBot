# src/core/pu/pu08_checkout.py
from telebot import types

def register(bot, ctx):
    """
    PU08 — Checkout (launcher/bridge)
    Սա ոչինչ չի նկարում ինքնուրույն. Պարզապես բացում է հասցեի պատուհանը,
    որը գրանցում է Address/Checkout PU-ը (api['checkout_open']).
    Այդպես խուսափում ենք callback prefix-ների բախումներից։
    """
    shop_state = ctx["shop_state"]
    api = shop_state.setdefault("api", {})

    def _open(uid: int, chat_id: int):
        # delegate to the real Address window (PU10 or ձեր address PU)
        open_addr = api.get("checkout_open")
        if callable(open_addr):
            open_addr(uid, chat_id)
        else:
            bot.send_message(
                chat_id,
                "📋 Checkout-ի հասցեի պատուհանը դեռ միացված չէ (api['checkout_open']).",
                parse_mode=None,
            )

    # expose a simple entry for others
    api["checkout_start"] = _open

    # convenience command for testing
    @bot.message_handler(commands=["checkout"])
    def _cmd_checkout(m: types.Message):
        uid = m.from_user.id
        chat_id = m.chat.id
        _open(uid, chat_id)
