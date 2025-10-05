# src/core/pu/pu06_checkout_fsm.py
from typing import Any, Dict
from telebot import types

# ինչ դաշտեր ենք պահում
FIELDS = ["name", "phone", "country", "city", "street", "apt", "note"]


def _ust(shop_state: Dict, uid: int) -> Dict[str, Any]:
    """User state for checkout scope"""
    scope = shop_state.setdefault("checkout", {})
    return scope.setdefault(
        uid,
        {"mode": "checkout", "data": {}, "await": None, "summary_msg_id": None, "lang": "hy"},
    )


# -------------------- keyboards & view --------------------

def _kb(lang: str = "hy"):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🌍 Երկիր", "📍 Մարզ / քաղաք")
    kb.row("🏠 Փողոց, շենք", "🏢 Բնակարան / մուտք")
    kb.row("👤 Անուն Ազգանուն", "📞 Հեռախոս")
    kb.row("✍️ Նշում (ոչ պարտադիր)")
    kb.row("📲 Կիսվել կոնտակտով", "📍 Կիսվել տեղակայմամբ")
    kb.row("⬅️ Վերադառնալ", "➡️ Շարունակել՝ առաքում")
    return kb


def _summary(data: Dict[str, Any]) -> str:
    return (
        "🧾 Անձնական տվյալներ\n"
        f"• Անուն՝ {data.get('name','—')}\n"
        f"• Հեռ․ {data.get('phone','—')}\n"
        f"• Երկիր՝ {data.get('country','—')}\n"
        f"• Քաղաք՝ {data.get('city','—')}\n"
        f"• Փողոց՝ {data.get('street','—')}\n"
        f"• Բնակարան՝ {data.get('apt','—')}\n"
        f"• Նշում՝ {data.get('note','—')}\n"
        "\nℹ️ Սեղմեք կանաչ կոճակը, հետո գրեք արժեքը։"
    )


def _send_window(bot, chat_id: int, st: Dict[str, Any]):
    """Shows white summary + sends the reply keyboard"""
    txt = _summary(st["data"])
    if st.get("summary_msg_id"):
        try:
            bot.edit_message_text(txt, chat_id, st["summary_msg_id"], parse_mode=None)
            # անպայման վերադարձնենք, եթե հաջողվեց edit անել
            return
        except Exception:
            pass
    msg = bot.send_message(chat_id, txt, parse_mode=None, disable_web_page_preview=True)
    st["summary_msg_id"] = msg.message_id
    # «տեսանելի զրո»՝ որ reply keyboard-ը երևա որպես նոր մեսիջ
    bot.send_message(chat_id, "\u2063", reply_markup=_kb(st.get("lang", "hy")))


# -------------------- public open --------------------

def open_checkout(bot, shop_state: Dict, uid: int, chat_id: int):
    st = _ust(shop_state, uid)
    st["mode"] = "checkout"
    st.setdefault("data", {})
    st["await"] = None
    _send_window(bot, chat_id, st)


# ==================== REGISTER ====================

def register(bot, ctx):
    shop_state: Dict = ctx["shop_state"]
    resolve_lang = ctx["resolve_lang"]

    # ── CONTROLS ─────────────────────────────────────────

    @bot.message_handler(func=lambda m: m.text == "➡️ Շարունակել՝ առաքում")
    def _goto_delivery(m):
        uid = m.from_user.id
        st = _ust(shop_state, uid)
        data = st.get("data", {})
        # մինիմալ վալիդացիա
        if not data.get("name") or not data.get("phone") or not (data.get("city") or data.get("street")):
            bot.send_message(m.chat.id, "⚠️ Լրացրեք առնվազն Անուն, Հեռախոս, Քաղաք/Հասցե։")
            return
        from .pu13_delivery import open_delivery
        st["mode"] = None
        open_delivery(bot, shop_state, uid, m.chat.id)

    @bot.message_handler(func=lambda m: m.text == "⬅️ Վերադառնալ")
    def _back(m):
        # պարզապես դուրս ենք գալիս checkout-ից (մնացածը կկառավարի հիմնական router-ը)
        uid = m.from_user.id
        st = _ust(shop_state, uid)
        st["mode"] = None
        st["await"] = None
        bot.send_message(m.chat.id, "🔙 Վերադարձավ մենյու։", reply_markup=types.ReplyKeyboardRemove())

    # ── SHARE CONTACT / LOCATION ─────────────────────────

    @bot.message_handler(content_types=['contact'])
    def _contact(m):
        uid = m.from_user.id
        st = _ust(shop_state, uid)
        phone = getattr(getattr(m, "contact", None), "phone_number", "") or st["data"].get("phone")
        if phone:
            st["data"]["phone"] = phone
        _send_window(bot, m.chat.id, st)

    @bot.message_handler(content_types=['location'])
    def _location(m):
        uid = m.from_user.id
        st = _ust(shop_state, uid)
        loc = getattr(m, "location", None)
        if loc:
            st["data"]["city"] = st["data"].get("city") or "քարտեզով նշված"
            note_old = st["data"].get("note") or ""
            st["data"]["note"] = (note_old + f"\n📍 lat={loc.latitude}, lon={loc.longitude}").strip()
        _send_window(bot, m.chat.id, st)

    # ── BUTTON → AWAIT TEXT ──────────────────────────────
    # Սրանցից որևէ մեկը սեղմելուց՝ սպասում ենք հաջորդ տեքստին
    _BTN2FIELD = {
        "👤 անուն ազգանուն": "name",
        "📞 հեռախոս": "phone",
        "🌍 երկիր": "country",
        "📍 մարզ / քաղաք": "city",
        "🏠 փողոց, շենք": "street",
        "🏢 բնակարան / մուտք": "apt",
        "✍️ նշում (ոչ պարտադիր)": "note",
    }

    def _btn_to_field(txt: str) -> str | None:
        low = (txt or "").lower()
        for label, field in _BTN2FIELD.items():
            if label in low:  # emoji + բառերի համադրությունը կա մուտքում
                return field
        return None

    @bot.message_handler(func=lambda m: _btn_to_field(m.text) is not None)
    def _await_text(m):
        uid = m.from_user.id
        st = _ust(shop_state, uid)
        field = _btn_to_field(m.text)
        st["await"] = {"field": field}
        prompts = {
            "name": "Գրեք Ձեր Անուն Ազգանունը",
            "phone": "Գրեք հեռախոսահամարը՝ +374…",
            "country": "Գրեք երկիրը (օր. Armenia)",
            "city": "Գրեք քաղաքը/մարզը (օր. Երևան)",
            "street": "Գրեք հասցեն (օր. Շիրակ 10, շենք 4)",
            "apt": "Գրեք բնակարան/մուտք (եթե կա)",
            "note": "Գրեք նշումը (ոչ պարտադիր)",
        }
        bot.send_message(m.chat.id, f"✍️ {prompts[field]}")

    # ── TEXT SAVE ────────────────────────────────────────

    @bot.message_handler(func=lambda m: isinstance(getattr(m, "text", None), str))
    def _on_text(m):
        uid = m.from_user.id
        st = shop_state.get("checkout", {}).get(uid)
        if not st or st.get("mode") != "checkout":
            return

        txt = (m.text or "").strip()
        st["lang"] = resolve_lang(uid, "hy")

        # 1) եթե սպասում էինք արժեքին՝ պահենք
        if st.get("await"):
            field = st["await"].get("field")
            if field:
                st["data"][field] = txt
            st["await"] = None
            _send_window(bot, m.chat.id, st)
            bot.send_message(m.chat.id, "✅ Պահպանվեց.", reply_markup=_kb(st.get("lang","hy")))
            return

        # 2) եթե անմիջապես գրել է «Երկիր», «Քաղաք» և այլն՝ enable-await ու խնդրենք կրկնել արժեքը
        possible_field = _btn_to_field(txt)
        if possible_field:
            st["await"] = {"field": possible_field}
            _await_text(m)  # կուղարկի համապատասխան prompt-ը
            return

        # այլ դեպքերում՝ անտեսում ենք, որ checkout-ի հոսքը մաքուր մնա
        return

    # ---------------- public API (imports use it) ----------------
    api = shop_state.setdefault("api", {})
    api["checkout_open"] = lambda uid, chat_id: open_checkout(bot, shop_state, uid, chat_id)
# synced from phone ✅
# synced from phone ✅
