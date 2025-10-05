# PU39 – Auto Language Detect
# Առաջին մեսիջից կամ Telegram locale-ից որոշում է լեզուն և պահում է user config-ում։

from typing import Dict, Any

def init(bot, resolve_lang, catalog, shop_state: Dict[str, Any]):
    """
    API:
      detect(user_id, tg_locale=None, first_text=None) -> lang
      get_lang(user_id) -> lang
    """
    langmod = shop_state.setdefault("auto_lang", {})
    user_langs = langmod.setdefault("_users", {})

    def detect(user_id: int, tg_locale: str = None, first_text: str = None) -> str:
        lang = None
        if tg_locale:
            lang = tg_locale[:2].lower()
        elif first_text:
            # Վերջնական տարբերակում կկապենք langid/fasttext, հիմա՝ պարզ heuristic
            if any(ch in first_text for ch in "абвгд"):
                lang = "ru"
            elif any(ch in first_text for ch in "aeiou"):
                lang = "en"
            else:
                lang = "hy"
        else:
            lang = "hy"
        user_langs[user_id] = lang
        return lang

    def get_lang(user_id: int) -> str:
        return user_langs.get(user_id, "hy")

    langmod["detect"] = detect
    langmod["get_lang"] = get_lang


def init(bot, ctx):
    def feature(bot, m):
        bot.send_message(m.chat.id, "✅ pu39_auto_lang_detect աշխատեց")
    ctx["shop_state"].setdefault("api", {})["auto_lang_detect"] = feature




