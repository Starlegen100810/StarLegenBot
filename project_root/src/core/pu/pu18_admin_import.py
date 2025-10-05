# src/core/pu/pu18_admin_import.py
from __future__ import annotations
import os
from typing import Dict, Any, Iterable
from telebot import types

ADMIN_KEYS = ["ADMINS", "ADMIN_IDS"]  # config/env

def _parse_admin_ids(val: str | Iterable[int] | None) -> set[int]:
    out: set[int] = set()
    if not val:
        return out
    if isinstance(val, (list, tuple, set)):
        for v in val:
            try: out.add(int(v))
            except Exception: pass
        return out
    s = str(val)
    for tok in s.replace(";", ",").replace(" ", ",").split(","):
        tok = tok.strip()
        if not tok: continue
        try: out.add(int(tok))
        except Exception: pass
    return out

def _get_admin_ids(ctx: Dict[str, Any], shop_state: Dict[str, Any]) -> set[int]:
    cfg = ctx.get("config") or {}
    for k in ADMIN_KEYS:
        if k in cfg:
            ids = _parse_admin_ids(cfg.get(k))
            if ids: return ids
    for k in ADMIN_KEYS:
        v = os.environ.get(k)
        if v:
            ids = _parse_admin_ids(v)
            if ids: return ids
    mem = shop_state.get("admin_ids")
    if isinstance(mem, (set, list, tuple)) and mem:
        return set(int(x) for x in mem)
    return set()

def _is_admin(uid: int, shop_state: Dict[str, Any]) -> bool:
    ids = shop_state.get("admin_ids") or set()
    return int(uid) in ids

def _admin_kb() -> types.ReplyKeyboardMarkup:
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📦 Պատվերներ", "📷 Վճարման ապացույցներ")
    kb.row("📢 Բրոդքաստ", "📊 Վիճակագրություն")
    kb.row("⬅️ Ելք ադմինից")
    return kb

def register(bot, ctx):
    """
    /admin հրամանով՝ ադմին պանել:
    ADMINS ID-երը կարդում է config-ից կամ ENV-ից (ADMINS=123,456)
    """
    shop_state: Dict[str, Any] = ctx["shop_state"]
    shop_state["admin_ids"] = set(_get_admin_ids(ctx, shop_state))  # persist

    def _not_admin(chat_id: int):
        bot.send_message(chat_id, "⛔ Այս բաժինը հասանելի է միայն ադմիններին։", parse_mode=None)

    @bot.message_handler(commands=["admin"])
    def _cmd_admin(m: types.Message):
        uid = m.from_user.id
        chat_id = m.chat.id
        if not _is_admin(uid, shop_state):
            return _not_admin(chat_id)
        try:
            if getattr(m, "message_id", None):
                bot.delete_message(chat_id, m.message_id)
        except Exception:
            pass
        bot.send_message(chat_id, "✅ Բարի գալուստ ադմին պանել։", reply_markup=_admin_kb(), parse_mode=None)

    @bot.message_handler(func=lambda m: isinstance(m.text, str) and m.text.strip() == "⬅️ Ելք ադմինից")
    def _admin_exit(m: types.Message):
        uid = m.from_user.id
        if not _is_admin(uid, shop_state): return
        try: bot.delete_message(m.chat.id, m.message_id)
        except Exception: pass
        bot.send_message(m.chat.id, "🏁 Փակվեց ադմին պանելի պատուհանը։", reply_markup=types.ReplyKeyboardRemove())

    # ------- Ադմին մենյու կոճակներ -------
    @bot.message_handler(func=lambda m: m.text == "📦 Պատվերներ")
    def _orders(m: types.Message):
        if not _is_admin(m.from_user.id, shop_state):
            return _not_admin(m.chat.id)
        api = shop_state.setdefault("api", {})
        open_orders = api.get("admin_orders_open")
        if callable(open_orders):
            open_orders(m.chat.id)
        else:
            bot.send_message(m.chat.id, "ℹ️ Orders admin դիտարկիչը (PU31) դեռ միացված չէ։")

    @bot.message_handler(func=lambda m: m.text == "📷 Վճարման ապացույցներ")
    def _proofs(m: types.Message):
        if not _is_admin(m.from_user.id, shop_state):
            return _not_admin(m.chat.id)
        api = shop_state.setdefault("api", {})
        open_proofs = api.get("admin_proofs_open")
        if callable(open_proofs):
            open_proofs(m.chat.id)
        else:
            bot.send_message(m.chat.id, "ℹ️ Proof inbox-ը (PU20) դեռ միացված չէ։")

    @bot.message_handler(func=lambda m: m.text == "📢 Բրոդքաստ")
    def _broadcast(m: types.Message):
        if not _is_admin(m.from_user.id, shop_state):
            return _not_admin(m.chat.id)
        bot.send_message(m.chat.id, "✉️ Ուղարկեք տեքստը՝ broadcast-ի համար (demo).", parse_mode=None)

    @bot.message_handler(func=lambda m: m.text == "📊 Վիճակագրություն")
    def _stats(m: types.Message):
        if not _is_admin(m.from_user.id, shop_state):
            return _not_admin(m.chat.id)
        users = len(shop_state.get("cart", {}))
        orders = len(shop_state.get("orders", []))
        bot.send_message(m.chat.id, f"👥 Approx users with carts: {users}\n📦 Orders saved: {orders}", parse_mode=None)

    # նոր ադմին ավելացնելու պարզ հրաման (միայն ադմինների համար)
    @bot.message_handler(commands=["make_admin"])
    def _make_admin(m: types.Message):
        uid = m.from_user.id
        chat_id = m.chat.id
        if not _is_admin(uid, shop_state):
            return _not_admin(chat_id)
        try:
            parts = (m.text or "").split()
            target = int(parts[1])
        except Exception:
            return bot.send_message(chat_id, "Օգտագործում՝ `/make_admin <user_id>`", parse_mode="Markdown")
        shop_state.setdefault("admin_ids", set()).add(int(target))
        bot.send_message(chat_id, f"✅ Ավելացվեց որպես ադմին՝ {target}", parse_mode=None)
