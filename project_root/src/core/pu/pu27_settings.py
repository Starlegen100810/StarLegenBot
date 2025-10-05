# src/core/pu/pu27_settings.py
from __future__ import annotations
from copy import deepcopy
from datetime import datetime
from telebot import types

DEFAULT_USER_SETTINGS = {
    "lang": "hy",
    "push": {"commerce": True, "service": True, "fun": True, "community": True, "marketing": True},
    "privacy": {"share_activity": False, "show_city": False},
    "ui": {"theme": "auto", "compact_mode": False},
}

DEFAULT_GLOBAL = {
    "currency": "AMD",
    "max_discount_pct": 20,
    "daily_deal_enabled": True,
    "spin_wheel_enabled": True,
}

def _now_iso():
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def _ensure(shop_state):
    shop_state.setdefault("settings", {
        "users": {},  # uid -> dict
        "global": deepcopy(DEFAULT_GLOBAL),
        "updated_at": _now_iso()
    })

def _merge(base: dict, patch: dict):
    if not isinstance(patch, dict):
        return base
    for k, v in patch.items():
        if isinstance(v, dict):
            base[k] = _merge(base.get(k, {}), v)
        else:
            base[k] = v
    return base

def init(bot, ctx):
    """
    Ստանդարտ ստորագրություն՝ init(bot, ctx)
    ctx = {"resolve_lang": ..., "catalog": ..., "shop_state": ...}
    """
    resolve_lang = ctx["resolve_lang"]
    shop_state   = ctx["shop_state"]

    _ensure(shop_state)
    feats = shop_state.setdefault("features", {})
    api   = feats.setdefault("settings", {})

    def _bucket(uid: int) -> dict:
        users = shop_state["settings"]["users"]
        if uid not in users:
            users[uid] = deepcopy(DEFAULT_USER_SETTINGS)
        return users[uid]

    def get_user(user_id: int) -> dict:
        return deepcopy(_bucket(user_id))

    def set_user(user_id: int, patch: dict) -> dict:
        cur = _bucket(user_id)
        _merge(cur, patch or {})
        shop_state["settings"]["updated_at"] = _now_iso()
        return deepcopy(cur)

    def toggle(user_id: int, path: str, value=None) -> dict:
        cur = _bucket(user_id)
        parts = str(path).split(".")
        node = cur
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        leaf = parts[-1]
        if value is None:
            node[leaf] = not bool(node.get(leaf, False))
        else:
            node[leaf] = value
        shop_state["settings"]["updated_at"] = _now_iso()
        return deepcopy(cur)

    def get_global() -> dict:
        return deepcopy(shop_state["settings"]["global"])

    def set_global(patch: dict) -> dict:
        _merge(shop_state["settings"]["global"], patch or {})
        shop_state["settings"]["updated_at"] = _now_iso()
        return deepcopy(shop_state["settings"]["global"])

    def reset_user(user_id: int) -> dict:
        shop_state["settings"]["users"][user_id] = deepcopy(DEFAULT_USER_SETTINGS)
        shop_state["settings"]["updated_at"] = _now_iso()
        return deepcopy(shop_state["settings"]["users"][user_id])

    def reset_global() -> dict:
        shop_state["settings"]["global"] = deepcopy(DEFAULT_GLOBAL)
        shop_state["settings"]["updated_at"] = _now_iso()
        return deepcopy(shop_state["settings"]["global"])

    # expose API for other modules
    api.update({
        "get_user": get_user,
        "set_user": set_user,
        "toggle": toggle,
        "get_global": get_global,
        "set_global": set_global,
        "reset_user": reset_user,
        "reset_global": reset_global,
    })

    # -------- smoke-test commands (parse_mode=None to avoid 400) --------
    @bot.message_handler(commands=['settings'])
    def _cmd_settings(m: types.Message):
        s_user = get_user(m.from_user.id)
        s_glob = get_global()
        txt = (
            "⚙️ Settings\n"
            f"• lang: {s_user.get('lang')}\n"
            f"• push: {s_user.get('push')}\n"
            f"• privacy: {s_user.get('privacy')}\n"
            f"• ui: {s_user.get('ui')}\n"
            "\n"
            f"🌍 Global: {s_glob}\n"
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton("🌐 HY", callback_data="set:lang:hy"),
            types.InlineKeyboardButton("🌐 RU", callback_data="set:lang:ru"),
            types.InlineKeyboardButton("🌐 EN", callback_data="set:lang:en"),
        )
        kb.add(
            types.InlineKeyboardButton("🔔 Marketing ON/OFF", callback_data="toggle:push.marketing")
        )
        bot.send_message(m.chat.id, txt, reply_markup=kb, parse_mode=None)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("set:lang:"))
    def _cb_set_lang(call: types.CallbackQuery):
        lang = (call.data.split(":")[2] or "hy").lower()
        set_user(call.from_user.id, {"lang": lang})
        # եթե ունես main_menu_keyboard(lang)՝ core-ի մեջ, PU-ից չենք կանչում, բայց կարող ես հետո home-ը թարմացնել
        try: bot.answer_callback_query(call.id, f"Lang = {lang}")
        except Exception: pass

    @bot.callback_query_handler(func=lambda c: c.data.startswith("toggle:"))
    def _cb_toggle(call: types.CallbackQuery):
        path = call.data.split(":", 1)[1] if ":" in call.data else ""
        if not path:
            try: bot.answer_callback_query(call.id); 
            except Exception: pass
            return
        new_state = toggle(call.from_user.id, path)
        try: bot.answer_callback_query(call.id, f"Toggled {path}")
        except Exception: pass
        # optionally send a small confirmation
        bot.send_message(call.message.chat.id, f"✅ {path} -> {new_state}", parse_mode=None)




