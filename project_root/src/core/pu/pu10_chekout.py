# src/core/pu/pu10_checkout.py
from __future__ import annotations
from typing import Dict, Any, Optional
from telebot import types
import re

# ================== helpers: state per-user ==================
def _root(store: Dict[str, Any]) -> Dict[str, Any]:
    return store.setdefault("checkout", {})

def _ust(store: Dict[str, Any], uid: int) -> Dict[str, Any]:
    st = _root(store).setdefault(uid, {})
    st.setdefault("data", {
        "country": "🇦🇲 Armenia",
        "city": "",
        "address": "",
        "apt": "",
        "fullname": "",
        "phone": "",
        "note": "",
        "geo": None,       # {"lat":..,"lon":..}
    })
    st.setdefault("await", None)    # which field we are waiting text for
    st.setdefault("page_msg_ids", [])
    return st

def _try_del(bot, chat_id: int, mid: int):
    try:
        bot.delete_message(chat_id, mid)
    except Exception:
        pass

def _clear_page(bot, chat_id: int, st: Dict[str, Any]):
    for mid in st.get("page_msg_ids", []):
        _try_del(bot, chat_id, mid)
    st["page_msg_ids"] = []

# ================== smart parse (free text) ==================
PHONE_RE = re.compile(r'(?:\+?374|\b0)\d{8}\b')

def _smart_parse(txt: str) -> Dict[str, str]:
    """շատ պարզ հուշողական parser՝ ազատ տեքստից city/address/apt/fullname/phone"""
    out: Dict[str, str] = {}
    s = (txt or "").strip()
    if not s:
        return out

    m = PHONE_RE.search(s)
    if m:
        out["phone"] = m.group(0)

    low = s.lower()

    # fullname hint — if contains at least 2 words and no keywords
    if not any(k in low for k in ["քաղաք", "марк", "город", "city", "փողոց", "улица", "address", "բնակարան", "кв", "apt"]):
        parts = [p for p in re.split(r"[\s,]+", s) if p]
        if len(parts) >= 2 and not m:
            out["fullname"] = " ".join(parts[:2])

    # city
    for key in ["քաղաք", "մարզ", "город", "city"]:
        if key in low:
            k = low.index(key) + len(key)
            out["city"] = s[k:].strip(" :,-|")[:60]
            break
    # address
    for key in ["փողոց", "улица", "adress", "адрес", "address", "փնղ", "փող"]:
        if key in low:
            k = low.index(key) + len(key)
            out["address"] = s[k:].strip(" :,-|")[:80]
            break
    # apt
    for key in ["բնակարան", "մուտք", "кв", "подъезд", "apt", "բնա"]:
        if key in low:
            k = low.index(key) + len(key)
            out["apt"] = s[k:].strip(" :,-|")[:40]
            break

    # If nothing matched but it looks like a city (1-2 words, not digits)
    if "city" not in out and "address" not in out and "fullname" not in out and not any(ch.isdigit() for ch in s) and len(s.split()) <= 2:
        out["city"] = s

    return out

# ================== i18n mini ==================
LBL = {
    "title": "📋 Checkout — Հասցե / Ստացող",
    "country": "🌍 Երկիր",
    "city": "📍 Մարզ / քաղաք",
    "address": "🏠 Փողոց, շենք",
    "apt": "🏢 Բնակարան / մուտք",
    "fullname": "👤 Անուն Ազգանուն",
    "phone": "📞 Հեռախոս",
    "note": "✍️ Նշում (ոչ պարտադիր)",
    "share_contact": "📲 Կիսվել կոնտակտով",
    "share_location": "📍 Կիսվել տեղակայությամբ",
    "next": "➡️ Շարունակել՝ Առաքում",
    "cancel": "❌ Չեղարկել",
    "ask_text": "Գրեք `{field}` դաշտի արժեքը և ուղարկեք պատասխանով 👇",
    "contact_tip": "Սեղմեք «Կիսվել կոնտակտով» բտն. կամ գրեք համարն այստեղ։",
    "location_tip": "Սեղմեք «Կիսվել տեղակայությամբ» բտն. կամ գրեք հասցեն ձեռքով։",
    "saved": "✅ Պահպանվեց",
    "help":
        "ℹ️ Կարող եք ուղղակի գրել այստեղ, և ես կլրացնեմ դաշտերը.\n"
        "— Օր՝ *Երևան, Սայաթ-Նովա 10, բն. 4*\n"
        "— Օր՝ *Անուն Ազգանուն*\n"
        "— Օր՝ *+37499123456*\n\n"
        "RU: Можно писать свободным текстом: город, улица 10, кв. 4; Имя Фамилия; +374...\n"
        "EN: You may type: City, Street 10, apt 4; Full Name; +374...",
}

# ================== UI render ==================
def _value(v: Optional[str]) -> str:
    v = (v or "").strip()
    return v if v else "—"

def _window_text(d: Dict[str, Any]) -> str:
    lines = [
        f"*{LBL['title']}*",
        "",
        f"{LBL['country']}: { _value(d.get('country')) }",
        f"{LBL['city']}: { _value(d.get('city')) }",
        f"{LBL['address']}: { _value(d.get('address')) }",
        f"{LBL['apt']}: { _value(d.get('apt')) }",
        f"{LBL['fullname']}: { _value(d.get('fullname')) }",
        f"{LBL['phone']}: { _value(d.get('phone')) }",
        f"{LBL['note']}: { _value(d.get('note')) }",
        "",
        LBL["help"]
    ]
    if d.get("geo"):
        lines.append(f"🌐 Geo: {d['geo'].get('lat'):.6f}, {d['geo'].get('lon'):.6f}")
    return "\n".join(lines)

def _window_kb() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton(LBL["country"], callback_data="chk:edit:country"),
        types.InlineKeyboardButton(LBL["city"], callback_data="chk:edit:city"),
    )
    kb.row(
        types.InlineKeyboardButton(LBL["address"], callback_data="chk:edit:address"),
        types.InlineKeyboardButton(LBL["apt"], callback_data="chk:edit:apt"),
    )
    kb.row(
        types.InlineKeyboardButton(LBL["fullname"], callback_data="chk:edit:fullname"),
        types.InlineKeyboardButton(LBL["phone"], callback_data="chk:edit:phone"),
    )
    kb.row(
        types.InlineKeyboardButton(LBL["note"], callback_data="chk:edit:note"),
    )
    kb.row(
        types.InlineKeyboardButton(LBL["share_contact"], callback_data="chk:share:contact"),
        types.InlineKeyboardButton(LBL["share_location"], callback_data="chk:share:loc"),
    )
    kb.row(
        types.InlineKeyboardButton(LBL["cancel"], callback_data="chk:cancel"),
        types.InlineKeyboardButton(LBL["next"], callback_data="chk:next"),
    )
    return kb

def _send_window(bot, chat_id: int, st: Dict[str, Any]):
    _clear_page(bot, chat_id, st)
    txt = _window_text(st["data"])
    kb = _window_kb()
    msg = bot.send_message(chat_id, txt, reply_markup=kb, parse_mode="Markdown", disable_web_page_preview=True)
    st["page_msg_ids"].append(msg.message_id)

# ================ public API to open =================
def open_address(bot, shop_state: Dict[str, Any], uid: int, chat_id: int):
    st = _ust(shop_state, uid)
    _send_window(bot, chat_id, st)

# ================ contact/location request keyboards ================
def _kb_contact_request() -> types.ReplyKeyboardMarkup:
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn = types.KeyboardButton(text="📲 Կիսվել կոնտակտով", request_contact=True)
    kb.row(btn)
    return kb

def _kb_location_request() -> types.ReplyKeyboardMarkup:
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn = types.KeyboardButton(text="📍 Ուղարկել տեղակայություն", request_location=True)
    kb.row(btn)
    return kb

# ================= validation =================
def _missing_fields(d: Dict[str, Any]) -> list[str]:
    miss = []
    if not (d.get("fullname") or "").strip():
        miss.append("Անուն Ազգանուն")
    if not (d.get("phone") or "").strip():
        miss.append("Հեռախոս")
    if not ((d.get("address") or "").strip() or (d.get("city") or "").strip() or d.get("geo")):
        miss.append("Հասցե / Քաղաք կամ Гео")
    return miss

# ================= register =================
def register(bot, ctx):
    shop_state = ctx["shop_state"]

    # expose API: api['checkout_open'](uid, chat_id)
    api = shop_state.setdefault("api", {})
    api["checkout_open"] = lambda uid, chat_id: open_address(bot, shop_state, uid, chat_id)

    # command for quick test
    @bot.message_handler(commands=["checkout"])
    def _cmd_checkout(m):
        uid = m.from_user.id
        chat_id = m.chat.id
        open_address(bot, shop_state, uid, chat_id)

    # --- callbacks: edit/share/next/cancel ---
    @bot.callback_query_handler(func=lambda c: isinstance(c.data, str) and c.data.startswith("chk:"))
    def _cb(c):
        uid = c.from_user.id
        chat_id = c.message.chat.id
        st = _ust(shop_state, uid)
        parts = c.data.split(":", 2)
        action = parts[1]
        arg = parts[2] if len(parts) > 2 else ""

        # clean the previous window to avoid clutter
        _clear_page(bot, chat_id, st)

        if action == "edit":
            field = arg
            st["await"] = field
            msg = bot.send_message(
                chat_id,
                LBL["ask_text"].format(field=LBL.get(field, field)),
                parse_mode=None
            )
            st["page_msg_ids"].append(msg.message_id)
            # re-show the window under the prompt
            _send_window(bot, chat_id, st)
            bot.answer_callback_query(c.id)
            return

        if action == "share":
            if arg == "contact":
                msg = bot.send_message(chat_id, LBL["contact_tip"], reply_markup=_kb_contact_request(), parse_mode=None)
                st["page_msg_ids"].append(msg.message_id)
            elif arg == "loc":
                msg = bot.send_message(chat_id, LBL["location_tip"], reply_markup=_kb_location_request(), parse_mode=None)
                st["page_msg_ids"].append(msg.message_id)
            _send_window(bot, chat_id, st)
            bot.answer_callback_query(c.id)
            return

        if action == "next":
            # validate required fields
            miss = _missing_fields(st["data"])
            if miss:
                bot.answer_callback_query(c.id, "Լրացրեք՝ " + ", ".join(miss), show_alert=True)
                _send_window(bot, chat_id, st)
                return
            # handoff to PU13 Delivery
            delivery_open = api.get("delivery_open")
            if callable(delivery_open):
                delivery_open(uid, chat_id)  # PU13 responsibility
            else:
                bot.send_message(chat_id, "🚚 Առաքման պատուհանը դեռ չի միացվել (PU13).", parse_mode=None)
            bot.answer_callback_query(c.id, "Շարունակում ենք առաքմամբ")
            return

        if action == "cancel":
            # wipe user checkout state
            _root(shop_state).pop(uid, None)
            bot.answer_callback_query(c.id, "Չեղարկվեց")
            try:
                bot.send_message(chat_id, "❌ Checkout-ը փակվեց։", parse_mode=None)
            except Exception:
                pass
            return

        # default
        bot.answer_callback_query(c.id)

    # --- text answers for awaited fields OR free-text smart fill ---
    @bot.message_handler(func=lambda m: True, content_types=["text"])
    def _on_text(m):
        uid = m.from_user.id
        chat_id = m.chat.id
        st = _ust(shop_state, uid)
        d = st["data"]
        field = st.get("await")
        txt = (m.text or "").strip()

        changed = False
        if field:
            d[field] = txt
            st["await"] = None
            changed = True
        else:
            parsed = _smart_parse(txt)
            if parsed:
                d.update(parsed)
                changed = True

        if changed:
            try:
                _try_del(bot, chat_id, m.message_id)  # remove user bubble
            except Exception:
                pass
            _send_window(bot, chat_id, st)
            bot.send_message(chat_id, LBL["saved"], parse_mode=None)

    # --- contact share ---
    @bot.message_handler(content_types=["contact"])
    def _on_contact(m):
        uid = m.from_user.id
        chat_id = m.chat.id
        st = _ust(shop_state, uid)
        ph = None
        try:
            ph = m.contact.phone_number
        except Exception:
            ph = None
        if ph:
            st["data"]["phone"] = ph
        try:
            _try_del(bot, chat_id, m.message_id)
        except Exception:
            pass
        _send_window(bot, chat_id, st)
        bot.send_message(chat_id, LBL["saved"], parse_mode=None)

    # --- location share ---
    @bot.message_handler(content_types=["location"])
    def _on_location(m):
        uid = m.from_user.id
        chat_id = m.chat.id
        st = _ust(shop_state, uid)
        try:
            lat = m.location.latitude
            lon = m.location.longitude
            st["data"]["geo"] = {"lat": float(lat), "lon": float(lon)}
        except Exception:
            pass
        try:
            _try_del(bot, chat_id, m.message_id)
        except Exception:
            pass
        _send_window(bot, chat_id, st)
        bot.send_message(chat_id, LBL["saved"], parse_mode=None)
