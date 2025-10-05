# src/commerce/pv.py
from __future__ import annotations
from pathlib import Path
from telebot import types

def register(bot, ctx):
    catalog     = ctx["catalog"]
    shop_state  = ctx["shop_state"]
    resolve_lang= ctx["resolve_lang"]

    # ---- helpers -------------------------------------------------
    def _pv_state(uid: int) -> dict:
        return shop_state.setdefault("pv", {}).setdefault(uid, {
            "pid": None, "idx": 0, "msg_id": None
        })

    def _del_prev_msg(chat_id: int, uid: int):
        st = _pv_state(uid)
        mid = st.get("msg_id")
        if mid:
            try:
                bot.delete_message(chat_id, mid)
            except Exception:
                pass
            st["msg_id"] = None

    def _caption(pid: str, lang: str) -> str:
        # օգտագործում ենք catalog.product_caption (արդեն ունի գներ, sales, badges, rating)
        return catalog.product_caption(pid, lang)

    def _ikb(pid: str, idx: int, total: int, lang: str) -> types.InlineKeyboardMarkup:
        kb = types.InlineKeyboardMarkup()
        # slide nav
        left  = types.InlineKeyboardButton("⬅️", callback_data=f"pvslide:{pid}:{(idx-1)%max(1,total)}")
        right = types.InlineKeyboardButton("➡️", callback_data=f"pvslide:{pid}:{(idx+1)%max(1,total)}")
        kb.row(left, types.InlineKeyboardButton(f"{idx+1}/{total}", callback_data="noop"), right)
        # actions
        kb.row(types.InlineKeyboardButton("🛒 Ավելացնել զամբյուղ", callback_data=f"addcart:{pid}"))
        kb.row(types.InlineKeyboardButton("❤️ Հավանել", callback_data=f"like:{pid}"),
               types.InlineKeyboardButton("✍️ Կարծիք", callback_data=f"review:{pid}"))
        kb.row(types.InlineKeyboardButton("🔙 Վերադառնալ", callback_data="pvback"))
        return kb

    def _send_slide(chat_id: int, uid: int, pid: str, idx: int):
        lang   = resolve_lang(uid)
        total  = max(1, catalog.gallery_len(pid))
        itype, src = catalog.slide_info(pid, idx % total)

        # delete previous pv message
        _del_prev_msg(chat_id, uid)

        cap = _caption(pid, lang)
        kb  = _ikb(pid, idx % total, total, lang)

        msg = None
        try:
            if itype == "video" and src and Path(src).exists():
                with open(src, "rb") as f:
                    msg = bot.send_video(chat_id, f, caption=cap, reply_markup=kb, parse_mode=None)
            elif itype == "image" and src and Path(src).exists():
                with open(src, "rb") as f:
                    msg = bot.send_photo(chat_id, f, caption=cap, reply_markup=kb, parse_mode=None)
            else:
                # fallback text if file missing
                msg = bot.send_message(chat_id, cap, reply_markup=kb, parse_mode=None, disable_web_page_preview=True)
        except Exception:
            msg = bot.send_message(chat_id, cap, reply_markup=kb, parse_mode=None, disable_web_page_preview=True)

        st = _pv_state(uid)
        st.update({"pid": pid, "idx": idx % total, "msg_id": getattr(msg, "message_id", None)})

    # ---- public API for main.py to call (optional use) ----------
    def show_product(chat_id: int, uid: int, pid: str):
        _send_slide(chat_id, uid, pid, 0)

    # Դնենք API-ի տակ, եթե հետագայում պետք գա main-ից կոչել
    shop_state.setdefault("api", {})["product_view"] = show_product

    # ---- callbacks ----------------------------------------------
    @bot.callback_query_handler(func=lambda c: isinstance(c.data, str) and c.data.startswith("pv:"))
    def cb_open(c: types.CallbackQuery):
        # from products grid: "pv:{pid}"
        pid = c.data.split(":", 1)[1]
        uid = c.from_user.id
        bot.answer_callback_query(c.id)
        _send_slide(c.message.chat.id, uid, pid, 0)

    @bot.callback_query_handler(func=lambda c: isinstance(c.data, str) and c.data.startswith("pvslide:"))
    def cb_slide(c: types.CallbackQuery):
        # "pvslide:{pid}:{idx}"
        _, pid, idx_s = c.data.split(":")
        uid = c.from_user.id
        try:
            idx = int(idx_s)
        except ValueError:
            idx = 0
        bot.answer_callback_query(c.id)
        _send_slide(c.message.chat.id, uid, pid, idx)

    @bot.callback_query_handler(func=lambda c: isinstance(c.data, str) and c.data.startswith("addcart:"))
    def cb_addcart(c: types.CallbackQuery):
        pid = c.data.split(":", 1)[1]
        uid = c.from_user.id
        api = shop_state.setdefault("api", {})
        cart_api = api.get("cart")
        if not cart_api:
            bot.answer_callback_query(c.id, "⚠️ Զամբյուղը հասանելի չէ", show_alert=True)
            return
        try:
            cart_api["add"](shop_state, uid, pid, 1)
            bot.answer_callback_query(c.id, "Ավելացվեց 🛒")
        except Exception:
            bot.answer_callback_query(c.id, "Տեխնիկական սխալ", show_alert=True)

    @bot.callback_query_handler(func=lambda c: isinstance(c.data, str) and c.data.startswith("like:"))
    def cb_like(c: types.CallbackQuery):
        pid = c.data.split(":", 1)[1]
        try:
            catalog.inc_like(pid)
        except Exception:
            pass
        bot.answer_callback_query(c.id, "❤️ Շնորհակալություն!")

    @bot.callback_query_handler(func=lambda c: isinstance(c.data, str) and c.data.startswith("review:"))
    def cb_review(c: types.CallbackQuery):
        # Քննարկված համակարգը հետո կավելացնենք (աստղեր, տեքստ, նկարի upload)
        bot.answer_callback_query(c.id, "✍️ Շուտով հասանելի կլինի", show_alert=False)

    @bot.callback_query_handler(func=lambda c: c.data == "pvback")
    def cb_back(c: types.CallbackQuery):
        bot.answer_callback_query(c.id, "Վերադարձ")
        # Չենք ջարդում shop flow-ը. Պարզ նշում ենք՝ օգտվիր reply մենյուից
        try:
            bot.send_message(c.message.chat.id, "⬅️ Վերադառնալու համար օգտվեք մենյուից «Վերադառնալ / Գլխավոր մենյու».")
        except Exception:
            pass
