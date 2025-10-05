# PU33 – Dynamic UI (themes/day-night/emoji headers)
# Սա չի դիպչում բիզնես-լոգիկային. պարզապես տալիս է helper-ներ theme-ի համար։
# Կօգտագործվի view-երում՝ ցանկալի պահին.

from typing import Dict, Any

THEMES = {
    "day": {
        "emoji_header": "🌞",
        "palette": {"bg": "#ffffff", "fg": "#111111", "accent": "#ffb703"},
    },
    "night": {
        "emoji_header": "🌙",
        "palette": {"bg": "#0f1419", "fg": "#e6edf3", "accent": "#58a6ff"},
    },
    "classic": {
        "emoji_header": "✨",
        "palette": {"bg": "#fafafa", "fg": "#222222", "accent": "#6c5ce7"},
    },
}

def init(bot, resolve_lang, catalog, shop_state: Dict[str, Any]):
    """
    Dynamic UI: visual themes, small randomizations per session.
    Usage (later in views):
        theme = shop_state["ui"]["get_theme"]()
        emoji = theme["emoji_header"]
        colors = theme["palette"]
    """
    features = shop_state.setdefault("features", {})
    config   = shop_state.setdefault("config", {})
    ui       = shop_state.setdefault("ui", {})

    # Feature toggle (admin կարող է փոխել հետագայում admin-panel-ից)
    features.setdefault("dynamic_ui", True)

    # Default theme per-bot (per-user override՝ optional)
    config.setdefault("ui", {})
    config["ui"].setdefault("default_theme", "day")

    # Per-user in-memory override storage (պահեստավորում ենք session-ի մեջ)
    state_store = ui.setdefault("_per_user", {})  # {user_id: theme_name}

    def set_theme(name: str, user_id: int = None):
        if name not in THEMES:
            name = config["ui"]["default_theme"]
        if user_id is not None:
            state_store[user_id] = name
        else:
            config["ui"]["default_theme"] = name
        return name

    def get_theme(user_id: int = None):
        if not features.get("dynamic_ui", True):
            return THEMES[config["ui"]["default_theme"]]
        name = config["ui"]["default_theme"]
        if user_id is not None:
            name = state_store.get(user_id, name)
        return THEMES.get(name, THEMES["day"])

    ui["set_theme"] = set_theme
    ui["get_theme"] = get_theme
    ui["available_themes"] = list(THEMES.keys())


def init(bot, ctx):
    def feature(bot, m):
        bot.send_message(m.chat.id, "✅ pu33_dynamic_ui աշխատեց")
    ctx["shop_state"].setdefault("api", {})["dynamic_ui"] = feature




