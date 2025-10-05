# -*- coding: utf-8 -*-
# src/core/pu/pu01_start.py — /start + bunny + LONG welcome + language select + main menu

from pathlib import Path
from telebot import types

# manager-ը կարող է չլինել՝ կախված կառուցվածքից, ուստի Optional-import
try:
    from src.i18n import manager as M   # ← ՍԱ Է ՃԻՇՏԸ
except Exception:
    M = None

def register(bot, ctx):
    USER_LANG    = ctx["user_lang"]
    remember     = ctx.get("remember_msg")
    cleanup      = ctx.get("cleanup_bot_msgs")
    resolve_lang = ctx["resolve_lang"]
    app_name     = ctx.get("app_name", "StarLegen")

    # ---------- keyboards ----------
    def _lang_kb():
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        kb.row("🇦🇲 Հայերեն", "🇷🇺 Русский", "🇬🇧 English")
        return kb

    def _main_menu_kb(lang: str):
        rows = None
        if M and hasattr(M, "MENU"):
            try:
                m = M.MENU.get(lang, M.MENU.get("hy"))
                rows = [
                    [m["shop"], m["cart"]],
                    [m["mypage"], m.get("best", "🏆 Լավագույններ")],
                    [m["exchange"], m["rates"]],
                    [m["support"], m["partners"]],
                    [m["search"], m["invite"]],
                    [m["lang"], m["back"], m["home"]],
                ]
            except Exception:
                rows = None

        if rows is None:  # fallback՝ եթե MENU չկա
            if lang == "ru":
                rows = [
                    ["🛍 Магазин","🛒 Корзина"],
                    ["👤 Моя страница","🏆 Лучшее"],
                    ["💱 Обмен","📊 Курс дня"],
                    ["💬 Поддержка","🤝 Партнёры"],
                    ["🔍 Поиск","🤝 Пригласить друзей"],
                    ["🌐 Язык","🔙 Назад","🏠 Главное меню"],
                ]
            elif lang == "en":
                rows = [
                    ["🛍 Shop","🛒 Cart"],
                    ["👤 My Page","🏆 Best"],
                    ["💱 Exchange","📊 Daily Rate"],
                    ["💬 Support","🤝 Partners"],
                    ["🔍 Search","🤝 Invite Friends"],
                    ["🌐 Language","🔙 Back","🏠 Main Menu"],
                ]
            else:
                rows = [
                    ["🛍 Խանութ","🛒 Զամբյուղ"],
                    ["👤 Իմ էջ","🏆 Լավագույններ"],
                    ["💱 Փոխարկումներ","📊 Օրվա կուրս"],
                    ["💬 Կապ մեզ հետ","🤝 Գործընկերներ"],
                    ["🔍 Որոնել","🤝 Հրավիրել ընկերների"],
                    ["🌐 Լեզու","🔙 Վերադառնալ","🏠 Գլխավոր մենյու"],
                ]

        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for r in rows:
            kb.row(*r)
        return kb

    # ---------- helpers ----------
    def _send_bunny(chat_id):
        pic = Path(__file__).resolve().parents[3] / "media" / "bunny.jpg"
        if pic.exists():
            with open(pic, "rb") as fh:
                return bot.send_photo(chat_id, fh)
        return bot.send_message(chat_id, "🐰")

    def _to_lang_code(text: str | None):
        if not text: return None
        t = text.lower()
        if "հայ" in t or "🇦🇲" in t: return "hy"
        if "рус" in t or "🇷🇺" in t: return "ru"
        if "eng" in t or "english" in t or "🇬🇧" in t: return "en"
        return None

    def _long_welcome_text(lang: str, customer_no: int = 1008) -> str:
        # նախընտրում ենք manager.WELCOME_LONG, եթե կա
        if M and hasattr(M, "WELCOME_LONG"):
            try:
                raw = M.WELCOME_LONG.get(lang, M.WELCOME_LONG.get("hy"))
                return raw.format(customer_no=customer_no)
            except Exception:
                pass
        # fallback՝ կարճ
        base = {
            "hy": "🐰🌸 Բարի գալուստ StarLegen 🛍✨",
            "ru": "🐰🌸 Добро пожаловать в StarLegen 🛍✨",
            "en": "🐰🌸 Welcome to StarLegen 🛍✨",
        }
        return base.get(lang, base["hy"])

    # ---------- /start ----------
    @bot.message_handler(commands=["start"])
    def _start(m: types.Message):
        uid = m.from_user.id
        try:
            cleanup(m.chat.id, uid)
        except Exception:
            pass

        # bunny
        remember(uid, _send_bunny(m.chat.id))

        # LONG welcome (ՁԵՐ ՏԵԿՍՏԸ manager.py-ից)
        lang = resolve_lang(uid) or "hy"
        welcome = _long_welcome_text(lang, customer_no=1008)
        remember(uid, bot.send_message(m.chat.id, welcome, parse_mode=None))

        # լեզվի ընտրություն
        remember(uid, bot.send_message(m.chat.id, {
            "hy": "🌐 Ընտրեք լեզուն ⬇️",
            "ru": "🌐 Выберите язык ⬇️",
            "en": "🌐 Choose your language ⬇️",
        }[lang], reply_markup=_lang_kb(), parse_mode=None))

    # ---------- լեզվի ընտրում ----------
    @bot.message_handler(func=lambda m: _to_lang_code(getattr(m, "text", None)) is not None)
    def _set_lang(m: types.Message):
        uid  = m.from_user.id
        lang = _to_lang_code(m.text) or "hy"
        USER_LANG[uid] = lang

        try:
            cleanup(m.chat.id, uid)
        except Exception:
            pass

        # հաստատում + ԳԼԽԱՎՈՐ ՄԵՆՅՈՒ
        confirm = {
            "hy": "✅ Լեզուն պահպանվեց",
            "ru": "✅ Язык сохранён",
            "en": "✅ Language set",
        }[lang]
        kb = _main_menu_kb(lang)
        remember(uid, bot.send_message(m.chat.id, confirm, reply_markup=kb, parse_mode=None))

def healthcheck(_ctx):
    return True
