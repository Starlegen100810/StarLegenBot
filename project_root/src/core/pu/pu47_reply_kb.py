# -*- coding: utf-8 -*-
# Forces checkout wizard to use ReplyKeyboard (bottom menu) + text handlers
# Safe add-on: doesn't break your existing inline buttons; just prefers reply kb.

from telebot import types

BTN_HOME = "🏠 Գլխավոր մենյու"
BTN_BACK = "🔙 Վերադառնալ"
BTN_CANCEL = "❌ Չեղարկել"
BTN_NEXT = "➡️ Շարունակել՝ Ափո"
BTN_COUNTRY = "🌍 Երկիր"
BTN_CITY = "📍 Մարզ / քաղաք"
BTN_STREET = "🏠 Փողոց, շենք"
BTN_APT = "🏢 Բնակարան / մուտք"
BTN_FULLNAME = "👤 Անուն Ազգանուն"
BTN_PHONE = "📞 Հեռախոս"
BTN_ATTACH_CONTACT = "📇 Կցել կոնտակտ"
BTN_ATTACH_LOCATION = "📌 Կցել տեղադրություն"

def _kb_rows(*rows):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for r in rows:
        kb.row(*r) if isinstance(r, (list, tuple)) else kb.row(r)
    return kb

def wizard_kb():
    return _kb_rows(
        [BTN_COUNTRY, BTN_CITY],
        [BTN_STREET, BTN_APT],
        [BTN_FULLNAME, BTN_PHONE],
        [BTN_ATTACH_CONTACT, BTN_ATTACH_LOCATION],
        [BTN_CANCEL, BTN_BACK],
    )

def nav_kb():
    return _kb_rows([BTN_BACK, BTN_HOME])

def _match(txt, *keys):
    if not isinstance(txt, str):
        return False
    low = txt.lower()
    return any(k in low for k in keys)

def register(bot, ctx):
    SHOP_STATE = ctx["shop_state"]
    resolve_lang = ctx["resolve_lang"]

    # put a small hook for any message that opens checkout (if your PU06 starts it differently, it's still ok)
    # we only supply reply-kb during address/name/phone steps.
    def _ensure_chk(uid: int):
        st = SHOP_STATE.setdefault(uid, {})
        chk = st.setdefault("checkout", {"step": None, "data": {}, "await": None})
        chk.setdefault("data", {}).setdefault("address", {})
        return chk

    # ——— render helpers (reply keyboard) ———
    def ask_free_text(chat_id: int, label: str):
        bot.send_message(
            chat_id,
            label + "\n\nℹ️ Կարող եք ուղարկել ազատ տեքստով և կկապեմ դաշտին։",
            reply_markup=wizard_kb(),
            parse_mode=None
        )

    # ——— OPEN REPLY-WIZARD UI WHEN CHECKOUT IS RUNNING ———
    @bot.message_handler(func=lambda m: _match(m.text, "շարունակ", "աշխատեցի", "ապա") or _match(m.text, "checkout"))
    def _noop_continue(m):
        # This exists just to avoid "fallback" stealing the focus; real FSM is in PU06/PU09.
        pass

    # Քայլային կոճակներ → սպասել ազատ տեքստ
    @bot.message_handler(func=lambda m: m.text in {
        BTN_COUNTRY, BTN_CITY, BTN_STREET, BTN_APT, BTN_FULLNAME, BTN_PHONE
    })
    def _await_text(m):
        uid = m.from_user.id
        chk = _ensure_chk(uid)
        mapping = {
            BTN_COUNTRY: ("country", "🌍 Գրեք երկիրը (օր. Հայաստան)"),
            BTN_CITY: ("city", "📍 Գրեք մարզ/քաղաքը (օր. Երևան)"),
            BTN_STREET: ("street", "🏠 Գրեք փողոցն ու շենքը (օր. Սարյան 10)"),
            BTN_APT: ("apt", "🏢 Գրեք բնակարան / մուտք / հարկ"),
            BTN_FULLNAME: ("fullname", "👤 Գրեք Անուն Ազգանուն"),
            BTN_PHONE: ("phone", "📞 Գրեք հեռախոսահամար (+374...)"),
        }
        key, label = mapping[m.text]
        chk["await"] = key
        ask_free_text(m.chat.id, label)

    # location/contact attach (ըստ ցանկության քո PU09-ում կարող ես այս արժեքներով աշխատեցնել վճարում)
    @bot.message_handler(content_types=["contact"])
    def _got_contact(m):
        uid = m.from_user.id
        chk = _ensure_chk(uid)
        c = m.contact
        if not c: return
        chk["data"]["contact"] = {
            "phone": c.phone_number,
            "name": (c.first_name or "") + (" " + c.last_name if c.last_name else "")
        }
        bot.send_message(m.chat.id, "✅ Կոնտակտը կցվեց։", reply_markup=wizard_kb(), parse_mode=None)

    @bot.message_handler(content_types=["location"])
    def _got_loc(m):
        uid = m.from_user.id
        chk = _ensure_chk(uid)
        loc = m.location
        if not loc: return
        chk["data"]["location"] = {"lat": loc.latitude, "lon": loc.longitude}
        bot.send_message(m.chat.id, "✅ Տեղադրությունը կցվեց։", reply_markup=wizard_kb(), parse_mode=None)

    # Սպասված ազատ տեքստը պահել տվյալ դաշտում
    @bot.message_handler(func=lambda m: True, content_types=["text"])
    def _freefill(m):
        uid = m.from_user.id
        st = SHOP_STATE.get(uid, {})
        chk = st.get("checkout")
        if not chk or not chk.get("await"):
            return  # ուրիշ հենդլերները թող աշխատեն

        key = chk["await"]
        val = (m.text or "").strip()
        if key in {"country", "city", "street", "apt", "fullname", "phone"}:
            addr = chk["data"].setdefault("address", {})
            if key in {"country", "city", "street", "apt"}:
                addr[key] = val
            else:
                chk["data"][key] = val
            chk["await"] = None
            bot.send_message(m.chat.id, "✅ Պահվեց։ Կարող եք շարունակել կամ լրացնել մյուս դաշտերը։",
                             reply_markup=wizard_kb(), parse_mode=None)

    # Cancel / Back (հանձնել քո PU06/PU47 guard-ին, բայց reply-kb չպակասի)
    @bot.message_handler(func=lambda m: m.text in {BTN_CANCEL, BTN_BACK})
    def _cancel_back(m):
        uid = m.from_user.id
        st = SHOP_STATE.setdefault(uid, {})
        if m.text == BTN_CANCEL:
            st.pop("checkout", None)
            bot.send_message(m.chat.id, "❌ Չեղարկվեց։", reply_markup=nav_kb(), parse_mode=None)
        else:
            # back just shows navigation kb; իրական քայլափոխությունը թող անում է քո PU06 FSM-ը
            bot.send_message(m.chat.id, "🔙 Վերադարձ։", reply_markup=nav_kb(), parse_mode=None)

    # Երբ checkout FSM-ը բացվում է (քո PU06-ում), կարող ես ցանկացած պահի ցույց տալ reply-kb-ն՝
    # bot.send_message(chat_id, "Լրացրու դաշտերը 👇", reply_markup=wizard_kb(), parse_mode=None)
