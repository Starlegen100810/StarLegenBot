# PU12 — Loyalty (balance + apply/remove to cart)
from __future__ import annotations
from typing import Dict, Any
from math import floor
from telebot import types

# Կոնֆիգ՝ իրական բիզնես տրամաբանություն
MAX_PERCENT_OF_SUBTOTAL = 0.20   # զամբյուղի սահմանափակումը՝ max 20%
ROUND_TO = 10                    # ձախ/վրա կլորացում դեպի տասականներ (օր. 187 -> 180)

# ---------- internal state helpers ----------
def _root(store: Dict[str, Any]) -> Dict[str, Any]:
    return store.setdefault("loyalty", {})

def _get_bal(store: Dict[str, Any], uid: int) -> int:
    return int(_root(store).get(uid, 0))

def _set_bal(store: Dict[str, Any], uid: int, value: int):
    _root(store)[uid] = max(0, int(value))

def _cart_meta(store: Dict[str, Any], uid: int) -> Dict[str, Any]:
    cart = store.setdefault("cart", {})
    return cart.setdefault(uid, {"items": []})

def _applied_discount(store: Dict[str, Any], uid: int) -> int:
    return int(float(_cart_meta(store, uid).get("applied_discount", 0)))

def _set_applied_discount(store: Dict[str, Any], uid: int, v: int):
    _cart_meta(store, uid)["applied_discount"] = max(0, int(v))

def _round_amt(v: float) -> int:
    if ROUND_TO <= 1:
        return int(round(v))
    return int(floor(v / ROUND_TO) * ROUND_TO)

# ---------- public API (pure functions) ----------
def get_balance(store: Dict[str, Any], uid: int) -> int:
    return _get_bal(store, uid)

def set_balance(store: Dict[str, Any], uid: int, value: int):
    _set_bal(store, uid, value)

def accrue(store: Dict[str, Any], uid: int, by_amount: int):
    """Կուտակել bonus (օր. պատվերից հետո)"""
    _set_bal(store, uid, _get_bal(store, uid) + int(max(0, by_amount)))

def max_applicable_for_cart(resolve_lang, catalog, store: Dict[str, Any], uid: int) -> int:
    """Հաշվել՝ որքան loyalty կարելի է կիրառել տվյալ զամբյուղի վրա"""
    api = store.setdefault("api", {})
    cart_api = api.get("cart")
    if not cart_api:
        return 0
    bd = cart_api["breakdown"](resolve_lang, catalog, store, uid)
    subtotal = float(bd.get("subtotal", 0.0))
    cap_by_percent = subtotal * MAX_PERCENT_OF_SUBTOTAL
    bal = _get_bal(store, uid)
    allow = min(bal, cap_by_percent)
    return _round_amt(max(0.0, allow))

def apply_to_cart(resolve_lang, catalog, store: Dict[str, Any], uid: int) -> int:
    """Կիրառել loyalty-ը զամբյուղում. Վերադարձնում է factically կիրառված չափը"""
    allow = max_applicable_for_cart(resolve_lang, catalog, store, uid)
    if allow <= 0:
        return 0
    # set applied + deduct from balance
    _set_applied_discount(store, uid, allow)
    _set_bal(store, uid, max(0, _get_bal(store, uid) - allow))
    return allow

def remove_from_cart(store: Dict[str, Any], uid: int) -> int:
    """Հանել loyalty զեղչը զամբյուղից և գումարը վերադարձնել balance-ի մեջ"""
    used = _applied_discount(store, uid)
    if used > 0:
        _set_applied_discount(store, uid, 0)
        _set_bal(store, uid, _get_bal(store, uid) + used)
    return used

def info_text(resolve_lang, catalog, store: Dict[str, Any], uid: int) -> str:
    bal = _get_bal(store, uid)
    api = store.setdefault("api", {})
    cart_api = api.get("cart")
    if not cart_api:
        return f"🏅 Loyalty balance: {bal}֏"
    bd = cart_api["breakdown"](resolve_lang, catalog, store, uid)
    sub = int(float(bd.get("subtotal", 0.0)))
    cap = _round_amt(sub * MAX_PERCENT_OF_SUBTOTAL)
    used = _applied_discount(store, uid)
    lines = []
    lines.append("🏅 *Հավատարմության բալանս*")
    lines.append(f"Մնացորդ՝ **{bal}֏**")
    lines.append(f"Զամբյուղ՝ {sub}֏  |  Սահմանափակում՝ ≤ {cap}֏ (max {int(MAX_PERCENT_OF_SUBTOTAL*100)}%)")
    if used > 0:
        lines.append(f"Կիրառված զեղչ՝ **{used}֏**")
    return "\n".join(lines)

# ---------- UI helpers ----------
def _kb_bal(applied: bool) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup()
    if not applied:
        kb.row(types.InlineKeyboardButton("🎁 Կիրառել զեղչը", callback_data="loy:apply"))
    else:
        kb.row(types.InlineKeyboardButton("↩️ Հանել զեղչը", callback_data="loy:remove"))
    kb.row(types.InlineKeyboardButton("🛒 Բացել զամբյուղը", callback_data="loy:cart"))
    return kb

def _refresh_cart_ui(bot, store: Dict[str, Any], chat_id: int):
    """Փորձել թարմացնել Cart UI-ն՝ мягкий fallback-ով"""
    api = store.setdefault("api", {})
    # 1) արագ ճանապարհ՝ cart_ui_show(chat_id)
    show = api.get("cart_ui_show")
    if callable(show):
        try:
            show(chat_id)
            return
        except Exception:
            pass
    # 2) fallback՝ cart_ui(bot, message) — user bubble hack
    feat = api.get("cart_ui")
    if callable(feat):
        try:
            tmp = bot.send_message(chat_id, "⏳ Թարմացնում եմ զամբյուղը…")
            feat(bot, tmp)  # ինքը կջնջի user bubble-ը
            return
        except Exception:
            pass
    # 3) ամենավերջում՝ պարզապես ասենք
    try:
        bot.send_message(chat_id, "🛒 Զամբյուղը թարմացված է։")
    except Exception:
        pass

# ---------- register ----------
def register(bot, ctx):
    store = ctx["shop_state"]
    resolve_lang = ctx.get("resolve_lang")
    catalog = ctx.get("catalog")

    # API key
    api = store.setdefault("api", {})
    api["loyalty"] = {
        "get": lambda uid: get_balance(store, uid),
        "set": lambda uid, v: set_balance(store, uid, v),
        "accrue": lambda uid, v: accrue(store, uid, v),
        "max_for_cart": lambda uid: max_applicable_for_cart(resolve_lang, catalog, store, uid),
        "apply": lambda uid: apply_to_cart(resolve_lang, catalog, store, uid),
        "remove": lambda uid: remove_from_cart(store, uid),
        "info": lambda uid: info_text(resolve_lang, catalog, store, uid),
    }

    # Quick test command (ըստ ցանկության)
    @bot.message_handler(commands=["loy"])
    def _cmd_loy(m):
        uid = m.from_user.id
        chat_id = m.chat.id
        txt = info_text(resolve_lang, catalog, store, uid)
        applied = _applied_discount(store, uid) > 0
        bot.send_message(chat_id, txt, reply_markup=_kb_bal(applied), parse_mode="Markdown")

    # Callbacks
    @bot.callback_query_handler(func=lambda c: isinstance(c.data, str) and c.data.startswith("loy:"))
    def _cb(c):
        uid = c.from_user.id
        chat_id = c.message.chat.id
        action = c.data.split(":", 1)[1]

        if action == "apply":
            used = apply_to_cart(resolve_lang, catalog, store, uid)
            if used > 0:
                bot.answer_callback_query(c.id, f"Կիրառվեց {used}֏ զեղչ 🎁")
            else:
                bot.answer_callback_query(c.id, "Չկար կիրառելի զեղչ", show_alert=True)
            # info + թարմացնել cart UI
            try:
                txt = info_text(resolve_lang, catalog, store, uid)
                bot.send_message(chat_id, txt, reply_markup=_kb_bal(True), parse_mode="Markdown")
            except Exception:
                pass
            _refresh_cart_ui(bot, store, chat_id)
            return

        if action == "remove":
            back = remove_from_cart(store, uid)
            if back > 0:
                bot.answer_callback_query(c.id, "Զեղչը հանվեց ↩️")
            else:
                bot.answer_callback_query(c.id, "Կիրառված զեղչ չկար")
            try:
                txt = info_text(resolve_lang, catalog, store, uid)
                bot.send_message(chat_id, txt, reply_markup=_kb_bal(False), parse_mode="Markdown")
            except Exception:
                pass
            _refresh_cart_ui(bot, store, chat_id)
            return

        if action == "cart":
            bot.answer_callback_query(c.id)
            _refresh_cart_ui(bot, store, chat_id)
            return

        bot.answer_callback_query(c.id)
