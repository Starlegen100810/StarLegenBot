# src/core/pu/pu05_cart_ui.py
from __future__ import annotations
from typing import Dict, Any, List
from telebot import types
from pathlib import Path

# ------------------------ helpers (render) ------------------------

def _render_line(item: Dict[str, Any]) -> str:
    name  = item.get("name", "Ապրանք")
    code  = item.get("sku", "")
    price = float(item.get("price", 0))
    qty   = int(item.get("qty", 0))
    total = float(item.get("total", price * qty))
    return f"• {name} ({code})\n  {price:.0f}֏ × {qty} = {total:.0f}֏"

def _render_breakdown(bd: Dict[str, Any]) -> str:
    subtotal    = float(bd.get("subtotal", 0))
    discount    = float(bd.get("discount", 0))
    final_total = float(bd.get("final_total", subtotal - discount))
    lines: List[str] = []
    lines.append(f"Ապրանքներ — {subtotal:.0f}֏")
    if discount > 0:
        lines.append(f"Զեղչ — −{discount:.0f}֏")
    lines.append(f"Վերջնական — {final_total:.0f}֏")
    if final_total >= 10000:
        lines.append("🎉 Անվճար առաքում (≥ 10,000֏)")
    return "\n".join(lines)

def _emoji_step_bar(step_idx: int = 0) -> str:
    # 0: Cart → 1: Address → 2: Payment → 3: Confirm
    states = ["🛒", "📋", "💳", "✅"]
    done   = ["🟩", "🟩", "🟩", "🟩"]
    out = []
    for i, s in enumerate(states):
        if i < step_idx: out.append(done[i])
        elif i == step_idx: out.append(s)
        else: out.append("⬜")
    return " ".join(out) + "  (🛒 → 📋 → 💳 → ✅)"

# ------------------------ state helpers ------------------------

def _ui_state(shop_state: Dict[str, Any], uid: int) -> Dict[str, Any]:
    return shop_state.setdefault("cart_ui", {}).setdefault(uid, {"msg_ids": []})

def _del_prev(bot, chat_id: int, shop_state: Dict[str, Any], uid: int):
    st = _ui_state(shop_state, uid)
    for mid in st.get("msg_ids", []):
        try:
            bot.delete_message(chat_id, mid)
        except Exception:
            pass
    st["msg_ids"] = []

def _send_thumb(bot, chat_id: int, img_path: str | None, caption: str) -> int | None:
    try:
        if img_path and Path(img_path).exists():
            with open(img_path, "rb") as f:
                msg = bot.send_photo(chat_id, f, caption=caption, parse_mode=None)
                return getattr(msg, "message_id", None)
    except Exception:
        pass
    return None

# ------------------------ compose & show ------------------------

def _compose_text(resolve_lang, catalog, cart_api, shop_state, uid: int) -> tuple[str, Dict[str, Any]]:
    bd = cart_api["breakdown"](resolve_lang, catalog, shop_state, uid)
    items = bd.get("items") or []
    if not items:
        return ("🛒 Զամբյուղը դատարկ է։", bd)

    lines: List[str] = []
    lines.append(_emoji_step_bar(0))
    lines.append("🛒 **Ձեր զամբյուղը**")
    lines.append("")

    for it in items:
        stock_hint = ""
        try:
            pid = it.get("sku")
            lang = resolve_lang(uid)
            p = catalog.product_data(pid, lang) if pid else None
            st_left = int(p.get("stock", 0)) if p else 0
            if 0 < st_left <= 3:
                stock_hint = f"\n  ⏳ Մնացել է {st_left} հատ"
        except Exception:
            pass
        lines.append(_render_line(it) + stock_hint)

    lines.append("")
    lines.append("— — —")
    lines.append(_render_breakdown(bd))
    lines.append("— — —")
    lines.append("🎁 Եթե ունեք կուպոն — կիրառեք վճարման պահին։")
    return ("\n".join(lines), bd)

def _buttons_for_items(items: List[Dict[str, Any]]) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup()
    for it in items:
        sku = it.get("sku", "")
        qty = int(it.get("qty", 1))
        if not sku:
            continue
        kb.row(
            types.InlineKeyboardButton("➖", callback_data=f"cartui:dec:{sku}"),
            types.InlineKeyboardButton(f"{qty}", callback_data="noop"),
            types.InlineKeyboardButton("➕", callback_data=f"cartui:inc:{sku}"),
            types.InlineKeyboardButton("✖️", callback_data=f"cartui:rm:{sku}"),
        )
    kb.row(
        types.InlineKeyboardButton("🗑 Մաքրել", callback_data="cartui:clear?"),
        types.InlineKeyboardButton("✅ Վճարում", callback_data="cartui:checkout"),
    )
    kb.row(types.InlineKeyboardButton("⬅️ Վերադառնալ խանութ", callback_data="cartui:backshop"))
    return kb

def _show_cart(bot, resolve_lang, catalog, shop_state, uid: int, chat_id: int) -> None:
    api = shop_state.setdefault("api", {})
    cart_api = api.get("cart")
    if not cart_api or "breakdown" not in cart_api:
        bot.send_message(chat_id, "⚠️ Զամբյուղի մոդուլը դեռ ակտիվ չէ։")
        return

    text, bd = _compose_text(resolve_lang, catalog, cart_api, shop_state, uid)
    items = bd.get("items") or []

    # clean old
    _del_prev(bot, chat_id, shop_state, uid)
    st = _ui_state(shop_state, uid)

    # thumbnails (մինչև 3 հատ)
    for it in items[:3]:
        pid = it.get("sku")
        try:
            p = catalog.product_data(pid, resolve_lang(uid)) if pid else None
        except Exception:
            p = None
        img = (p.get("images") or [None])[0] if p else None
        cap = f"{it.get('name','Ապրանք')} — {int(float(it.get('price',0))):,}֏".replace(",", " ")
        mid = _send_thumb(bot, chat_id, img, cap)
        if mid: st["msg_ids"].append(mid)

    # main UI
    kb = _buttons_for_items(items)
    msg = bot.send_message(chat_id, text, reply_markup=kb, parse_mode=None, disable_web_page_preview=True)
    st["msg_ids"].append(getattr(msg, "message_id", None))

# ------------------------ public register ------------------------

def register(bot, ctx) -> None:
    resolve_lang = ctx["resolve_lang"]
    catalog = ctx["catalog"]
    shop_state = ctx["shop_state"]

    # 1) handler տարբերակ — կոչվում է (bot, message)
    def feature(bot_, m):
        chat_id = m.chat.id
        uid = m.from_user.id
        try:
            if getattr(m, "message_id", None):
                bot_.delete_message(chat_id, m.message_id)
        except Exception:
            pass
        _show_cart(bot_, resolve_lang, catalog, shop_state, uid, chat_id)

    api = shop_state.setdefault("api", {})
    api["cart_ui"] = feature

    # 2) show(chat_id) տարբերակ — երբ պետք է ուղղակի ցուցադրել
    def _show(chat_id: int):
        class _M:
            chat = type("C",(object,),{"id": chat_id})()
            from_user = type("U",(object,),{"id": chat_id})()  # fallback՝ uid=chat_id
            message_id = None
        feature(bot, _M())
    api["cart_ui_show"] = _show

    # --- callbacks for +/-/rm/clear/checkout ---
    @bot.callback_query_handler(func=lambda c: isinstance(c.data, str) and c.data.startswith("cartui:"))
    def cb_cartui(c: types.CallbackQuery):
        parts  = c.data.split(":", 2)
        action = parts[1] if len(parts) > 1 else ""
        arg    = parts[2] if len(parts) > 2 else ""
        uid    = c.from_user.id
        chat_id= c.message.chat.id

        cart_api = shop_state.setdefault("api", {}).get("cart")
        if not cart_api:
            bot.answer_callback_query(c.id, "Տեխնիկական խնդիր է", show_alert=True)
            return

        try:
            if action in ("inc", "dec"):
                bd = cart_api["breakdown"](resolve_lang, catalog, shop_state, uid)
                q = 0
                for it in (bd.get("items") or []):
                    if it.get("sku") == arg:
                        q = int(it.get("qty", 1)); break
                if action == "inc":
                    cart_api["set_qty"](shop_state, uid, arg, q + 1)
                    bot.answer_callback_query(c.id, "➕ Ավելացավ")
                else:
                    newq = max(0, q - 1)
                    if newq == 0:
                        cart_api["remove"](shop_state, uid, arg)
                    else:
                        cart_api["set_qty"](shop_state, uid, arg, newq)
                    bot.answer_callback_query(c.id, "➖ Քչացավ")

            elif action == "rm":
                cart_api["remove"](shop_state, uid, arg)
                bot.answer_callback_query(c.id, "✖️ Հեռացվեց")

            elif action == "clear?":
                bot.answer_callback_query(c.id)
                _del_prev(bot, chat_id, shop_state, uid)
                msg = bot.send_message(
                    chat_id,
                    "🗑 Վստա՞հ եք, որ ուզում եք մաքրել ամբողջ զամբյուղը։",
                    reply_markup=types.InlineKeyboardMarkup().row(
                        types.InlineKeyboardButton("❌ Չեղարկել", callback_data="cartui:clear_no"),
                        types.InlineKeyboardButton("🗑 Այո, մաքրել", callback_data="cartui:clear_yes"),
                    )
                )
                _ui_state(shop_state, uid)["msg_ids"] = [getattr(msg, "message_id", None)]
                return

            elif action == "clear_yes":
                cart_api["clear"](shop_state, uid)
                bot.answer_callback_query(c.id, "Մաքրվեց 🗑")

            elif action == "clear_no":
                bot.answer_callback_query(c.id, "Չեղարկվեց")

            elif action == "checkout":
                bot.answer_callback_query(c.id)
                # handed off to checkout (PU08/PU10)
                open_addr = api.get("checkout_open") or api.get("address_open")
                if callable(open_addr):
                    open_addr(uid, chat_id)
                else:
                    bot.send_message(chat_id, "✅ Շուտով՝ Checkout FSM (հասցե → վճարում).")
                return

            elif action == "backshop":
                bot.answer_callback_query(c.id, "Բացիր «🛍 Խանութ» մենյույից")
                return

            else:
                bot.answer_callback_query(c.id, "Չհասկացա գործողությունը")
                return

        except Exception:
            bot.answer_callback_query(c.id, "Սխալ է տեղի ունեցել", show_alert=True)

        # refresh cart UI
        _show_cart(bot, resolve_lang, catalog, shop_state, uid, chat_id)
