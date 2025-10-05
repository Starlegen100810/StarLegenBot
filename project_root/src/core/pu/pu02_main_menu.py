# -*- coding: utf-8 -*-
# src/core/pu/pu02_main_menu.py — Main menu (HY/RU/EN) + home/back + placeholders

from telebot import types

LABELS = {
    "hy": {
        "shop": "🛍 Խանութ", "cart": "🛒 Զամբյուղ",
        "profile": "👤 Իմ էջ", "leaders": "🏆 Լավագույններ",
        "fin": "💱 Ֆինանսականներ", "analytics": "📊 Օրվա կորպո",
        "support": "💬 Կապ մեզ հետ", "partners": "🤝 Գործընկերներ",
        "search": "🔎 Որոնել", "invite": "🤝 Հրավիրել ընկերների",
        "lang": "🌐 Լեզու", "back": "🔙 Վերադառնալ", "home": "🏠 Գլխավոր մենյու",
        "menu_title": "📋 Գլխավոր մենյու։",
        "ph": {
            "profile": "👤 «Իմ էջ» շուտով։",
            "leaders": "🏆 «Լավագույններ» շուտով։",
            "fin": "💱 «Ֆինանսականներ» շուտով։",
            "analytics": "📊 «Օրվա կորպո» շուտով։",
            "support": "💬 «Կապ մեզ հետ» շուտով։",
            "partners": "🤝 «Գործընկերներ» շուտով։",
            "search": "🔎 «Որոնել» շուտով։",
            "invite": "🤝 «Հրավիրել ընկերների» շուտով։",
            "lang": "🌐 Լեզուն փոխելու համար օգտվիր /start-ից։",
        }
    },
    "ru": {
        "shop": "🛍 Магазин", "cart": "🛒 Корзина",
        "profile": "👤 Профиль", "leaders": "🏆 Лидеры",
        "fin": "💱 Финансы", "analytics": "📊 Дневной отчёт",
        "support": "💬 Поддержка", "partners": "🤝 Партнёры",
        "search": "🔎 Поиск", "invite": "🤝 Пригласить друзей",
        "lang": "🌐 Язык", "back": "🔙 Назад", "home": "🏠 Главное меню",
        "menu_title": "📋 Главное меню.",
        "ph": {
            "profile": "👤 «Профиль» скоро.",
            "leaders": "🏆 «Лидеры» скоро.",
            "fin": "💱 «Финансы» скоро.",
            "analytics": "📊 «Дневной отчёт» скоро.",
            "support": "💬 «Поддержка» скоро.",
            "partners": "🤝 «Партнёры» скоро.",
            "search": "🔎 «Поиск» скоро.",
            "invite": "🤝 «Пригласить друзей» скоро.",
            "lang": "🌐 Сменить язык можно через /start.",
        }
    },
    "en": {
        "shop": "🛍 Shop", "cart": "🛒 Cart",
        "profile": "👤 Profile", "leaders": "🏆 Leaders",
        "fin": "💱 Finances", "analytics": "📊 Daily stats",
        "support": "💬 Support", "partners": "🤝 Partners",
        "search": "🔎 Search", "invite": "🤝 Invite friends",
        "lang": "🌐 Language", "back": "🔙 Back", "home": "🏠 Main menu",
        "menu_title": "📋 Main menu.",
        "ph": {
            "profile": "👤 “Profile” coming soon.",
            "leaders": "🏆 “Leaders” coming soon.",
            "fin": "💱 “Finances” coming soon.",
            "analytics": "📊 “Daily stats” coming soon.",
            "support": "💬 “Support” coming soon.",
            "partners": "🤝 “Partners” coming soon.",
            "search": "🔎 “Search” coming soon.",
            "invite": "🤝 “Invite friends” coming soon.",
            "lang": "🌐 Change language via /start.",
        }
    },
}

def _L(lang: str): return LABELS.get(lang, LABELS["hy"])

def main_menu_keyboard(lang: str = "hy") -> types.ReplyKeyboardMarkup:
    L = _L(lang)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(L["shop"], L["cart"])
    kb.row(L["profile"], L["leaders"])
    kb.row(L["fin"], L["analytics"])
    kb.row(L["support"], L["partners"])
    kb.row(L["search"], L["invite"])
    kb.row(L["lang"], L["back"], L["home"])
    return kb

def register(bot, ctx):
    resolve_lang = ctx["resolve_lang"]
    remember_msg = ctx.get("remember_msg")
    cleanup_msgs = ctx.get("cleanup_bot_msgs")
    shop_state   = ctx["shop_state"]

    # տրամադրում ենք PU01-ին
    ctx["main_menu_keyboard"] = main_menu_keyboard

    def _home(chat_id, uid):
        kb = main_menu_keyboard(resolve_lang(uid))
        remember_msg(uid, bot.send_message(chat_id, _L(resolve_lang(uid))["menu_title"], reply_markup=kb))

    # Home
    @bot.message_handler(func=lambda m: isinstance(getattr(m,"text",None), str)
                         and any(m.text.strip()==LABELS[l]["home"] for l in LABELS))
    def __home(m):
        uid = m.from_user.id
        cleanup_msgs(m.chat.id, uid)
        _home(m.chat.id, uid)

    # Back → մինչ FSM՝ տուն
    @bot.message_handler(func=lambda m: isinstance(getattr(m,"text",None), str)
                         and any(m.text.strip()==LABELS[l]["back"] for l in LABELS))
    def __back(m):
        uid = m.from_user.id
        cleanup_msgs(m.chat.id, uid)
        _home(m.chat.id, uid)

    # Cart → բացում ենք PU05 UI-ն, եթե գրանցված է
    @bot.message_handler(func=lambda m: isinstance(getattr(m,"text",None), str)
                         and any(m.text.strip()==LABELS[l]["cart"] for l in LABELS))
    def __cart(m):
        uid = m.from_user.id
        api = shop_state.setdefault("api", {})
        show = api.get("cart_ui") or api.get("cart_ui_show")
        if callable(show):
            try:
                if getattr(show, "__code__", None) and show.__code__.co_argcount >= 2:
                    show(bot, m)         # (bot, message)
                else:
                    show(m.chat.id)      # (chat_id)
            except Exception as e:
                remember_msg(uid, bot.send_message(m.chat.id, f"⚠️ Cart UI error: {e}", reply_markup=main_menu_keyboard(resolve_lang(uid))))
        else:
            remember_msg(uid, bot.send_message(m.chat.id, "🛒 Cart UI դեռ միացված չէ։", reply_markup=main_menu_keyboard(resolve_lang(uid))))

    # Մնացած կոճակների placeholder (մենյուն չի կորչում)
    def _ph(key, msg_key):
        @bot.message_handler(func=lambda m: isinstance(getattr(m,"text",None), str)
                             and any(m.text.strip()==LABELS[l][key] for l in LABELS))
        def _(m):
            uid = m.from_user.id
            lang = resolve_lang(uid)
            txt = _L(lang)["ph"][msg_key]
            remember_msg(uid, bot.send_message(m.chat.id, txt, reply_markup=main_menu_keyboard(lang)))
        return _
    _ph("profile","profile"); _ph("leaders","leaders")
    _ph("fin","fin"); _ph("analytics","analytics")
    _ph("support","support"); _ph("partners","partners")
    _ph("search","search"); _ph("invite","invite")
    _ph("lang","lang")

def healthcheck(_): return True
