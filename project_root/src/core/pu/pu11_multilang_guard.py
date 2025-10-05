# PU11 – Multilang Guard (auto-detect, per-user lang, safe format helpers)
from __future__ import annotations
from typing import Dict, Any, Optional

SUPPORTED = ("hy", "ru", "en")  # ARM/RU/ENG

def _store(shop_state):
    return shop_state.setdefault("i18n", {}).setdefault("users", {})  # user_id -> lang

def get_lang(resolve_lang, user_id: int) -> str:
    try:
        val = resolve_lang(user_id)
        if val in SUPPORTED: return val
    except Exception:
        pass
    return "hy"

def set_lang(shop_state, user_id: int, lang: str) -> bool:
    lang = (lang or "").lower()
    if lang not in SUPPORTED: return False
    _store(shop_state)[user_id] = lang
    return True

def remembered(shop_state, user_id: int) -> Optional[str]:
    return _store(shop_state).get(user_id)

def autodetect_lang(ctx) -> Optional[str]:
    # Prefer platform-provided language
    plat = (ctx.get("platform_lang") or ctx.get("tg_lang") or "").lower()
    if plat[:2] in SUPPORTED: return plat[:2]
    # Fallback by text alphabet (very rough)
    txt = (ctx.get("text") or "")[:64]
    if any("\u0530" <= ch <= "\u058F" for ch in txt): return "hy"
    if any("\u0400" <= ch <= "\u04FF" for ch in txt): return "ru"
    return "en" if txt else None

# Tiny dictionary (extendable from Admin Translation Manager later)
DICT = {
    "hy": {
        "lang_set": "Լեզուն փոխվեց՝ հայերեն 🇦🇲",
        "pick_lang": "Ընտրեք լեզուն",
        "help": "Կարող եք փոխել լեզուն /lang հրամանով։",
    },
    "ru": {
        "lang_set": "Язык установлен: русский 🇷🇺",
        "pick_lang": "Выберите язык",
        "help": "Вы можете сменить язык командой /lang.",
    },
    "en": {
        "lang_set": "Language set to English 🇬🇧",
        "pick_lang": "Choose your language",
        "help": "You can change language with /lang.",
    }
}

def t(lang: str, key: str, default: str = "") -> str:
    return DICT.get(lang, {}).get(key, default or DICT["en"].get(key, key))

def fmt_money(lang: str, amount: int, currency: str = "֏") -> str:
    # Simple locale-ish grouping
    s = f"{amount:,}".replace(",", " ")
    return f"{s}{currency}" if lang == "hy" else f"{currency}{s}"

def init(bot, resolve_lang, catalog, shop_state):
    """
    PU11 Multilang Guard
    - Remembers per-user language
    - Auto-detects on first interaction
    - Commands: /lang, /lang hy|ru|en
    - Helpers exposed in shop_state.api.i18n: get/set/remembered/t/fmt_money
    """
    api = shop_state.setdefault("api", {})
    i18n = api.setdefault("i18n", {})
    i18n.update({
        "get": lambda uid: (remembered(shop_state, uid) or get_lang(resolve_lang, uid)),
        "set": lambda uid, lg: set_lang(shop_state, uid, lg),
        "remembered": lambda uid: remembered(shop_state, uid),
        "t": t,
        "fmt_money": fmt_money,
    })

    on = getattr(bot, "on", None)
    if not callable(on): return

    # First contact auto-detect (safe: only once per user)
    @on("event:user:first_seen")
    def _first(ctx):
        uid = ctx["user_id"]
        if remembered(shop_state, uid): 
            return
        lg = autodetect_lang(ctx) or get_lang(resolve_lang, uid)
        set_lang(shop_state, uid, lg)

    # /lang or /lang hy|ru|en
    @on("cmd:/lang")
    def _lang_cmd(ctx):
        uid = ctx["user_id"]
        parts = (ctx.get("text") or "").split()
        if len(parts) >= 2 and parts[1].lower() in SUPPORTED:
            ok = set_lang(shop_state, uid, parts[1].lower())
            if ok:
                bot.send(uid, t(parts[1].lower(), "lang_set"))
            else:
                bot.send(uid, "Unsupported language.")
            return

        rows = [
            [{"text": "Հայերեն 🇦🇲", "data": "lang:pick:hy"},
             {"text": "Русский 🇷🇺", "data": "lang:pick:ru"},
             {"text": "English 🇬🇧", "data": "lang:pick:en"}]
        ]
        bot.ui(uid, t(remembered(shop_state, uid) or get_lang(resolve_lang, uid), "pick_lang"), rows=rows)
        bot.send(uid, t(remembered(shop_state, uid) or get_lang(resolve_lang, uid), "help"))

    for lg in SUPPORTED:
        @on(f"tap:lang:pick:{lg}")
        def _pick(ctx, _lg=lg):
            uid = ctx["user_id"]
            set_lang(shop_state, uid, _lg)
            bot.send(uid, t(_lg, "lang_set"))




