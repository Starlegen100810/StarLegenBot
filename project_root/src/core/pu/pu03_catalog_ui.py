# -*- coding: utf-8 -*-
# src/core/pu/pu03_catalog_ui.py — Shop: Category → Subcategory → Products + Product View/Gallery

from __future__ import annotations
from pathlib import Path
from telebot import types
from typing import List, Tuple

def register(bot, ctx):
    shop_state   = ctx["shop_state"]
    resolve_lang = ctx["resolve_lang"]
    catalog      = ctx["catalog"]
    remember     = ctx.get("remember_msg")
    cleanup_msgs = ctx.get("cleanup_bot_msgs")

    MEDIA_ROOT = Path(__file__).resolve().parents[3] / "media" / "PRODUCT"

    # ------------- UI helpers (reply) -------------
    def _kb_rows(*rows):
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for r in rows:
            kb.row(*r) if isinstance(r, (list, tuple)) else kb.row(r)
        return kb

    # նորը
    def _reply_nav_texts(lang: str) -> tuple[str, str]:
        L = {
            "hy": ("🔙 Վերադառնալ", "🏠 Գլխավոր մենյու"),
            "ru": ("🔙 Назад", "🏠 Главное меню"),
            "en": ("🔙 Back", "🏠 Main menu"),
    }
    return L.get(lang if lang in ("hy","ru","en") else "hy", L["hy"])


    # keep last page bot messages to delete (for shop listing)
    def _clear_prev_page(uid: int, chat_id: int):
        st = shop_state.setdefault(uid, {})
        for mid in st.get("page_msg_ids", []):
            try: bot.delete_message(chat_id, mid)
            except Exception: pass
        st["page_msg_ids"] = []

    # ------------- Keyboards for shop levels -------------
    # նորը
    def _categories_keyboard(lang: str):
        cats = list(catalog.categories(lang))  # [(cid,title)]
        titles = [t for _, t in cats] or ["—"]
        shop_state.setdefault("cats_map", {})[lang] = {title: cid for cid, title in cats}
        back_txt, home_txt = _reply_nav_texts(lang)
        return _kb_rows(*[[t] for t in titles], [back_txt, home_txt])


   # նորը
    def _subcats_keyboard(lang: str, cat_id: str):
        subs = list(catalog.subcategories(lang, cat_id))
        titles = [t for _, t in subs] or ["—"]
        shop_state.setdefault("subs_map", {})[(lang, cat_id)] = {title: sid for sid, title in subs}
        back_txt, home_txt = _reply_nav_texts(lang)
        return _kb_rows(*[[t] for t in titles], [back_txt, home_txt])


    # ------------- MEDIA DISCOVERY -------------
    def _find_media(pid: str) -> Tuple[Path|None, List[Path], Path|None]:
        """
        cover: rugs/{pid}.jpg if exists, else any **/{pid}.jpg
        gallery: any **/{pid}_*.jpg
        shared: if BA-prefixed (rugs), append shared/*.jpg in nice order
        video: first *.mp4 near cover or any **/{pid}*.mp4
        """
        pid_u = (pid or "").upper()
        cover = None
        gallery: List[Path] = []
        video = None

        # prefer rugs/{pid}.jpg
        cand = MEDIA_ROOT / "rugs" / f"{pid}.jpg"
        if cand.exists():
            cover = cand

        # any exact {pid}.jpg elsewhere if no cover yet
        if not cover:
            for p in MEDIA_ROOT.rglob(f"{pid}.jpg"):
                cover = p; break

        # collect {pid}_*.jpg
        for p in sorted(MEDIA_ROOT.rglob(f"{pid}_*.jpg")):
            if p.is_file():
                gallery.append(p)

        # shared for BA… (rugs)
        if pid_u.startswith("BA"):
            shared_dir = MEDIA_ROOT / "shared"
            shared_names = ["advantages.jpg","interior.jpg","layers.jpg","care.jpg","universal.jpg","absorb.jpg"]
            for name in shared_names:
                sp = shared_dir / name
                if sp.exists():
                    gallery.append(sp)

        # video near cover first
        if cover:
            for mp in sorted(cover.parent.glob("*.mp4")):
                video = mp; break
        if not video:
            for mp in MEDIA_ROOT.rglob(f"{pid}*.mp4"):
                video = mp; break

        return cover, gallery, video

    # ------------- Product Caption -------------
    def _caption_for(pid: str, lang: str) -> str:
        p = catalog.product_data(pid, lang) or {}
        name   = p.get("title") or p.get("name") or f"Product {pid}"
        price  = p.get("price") or p.get("new_price") or 0
        old    = p.get("old_price") or p.get("price_old") or 0
        feats  = p.get("features") or []
        if isinstance(feats, str):
            feats = [feats]

        # fake sold counter in state
        sold_map = shop_state.setdefault("sold_counter", {})
        base = sold_map.get(pid, 200)  # default base; can be adjusted
        sold_map[pid] = base  # ensure exists

        lines = []
        lines.append(f"🏷️ {name} — {pid}")
        if feats:
            for f in feats[:3]:
                lines.append(f"• {f}")
        if old and float(old) > float(price or 0):
            lines.append(f"❌ {int(float(old))}֏  →  ✅ **{int(float(price))}֏**")
        else:
            lines.append(f"✅ **{int(float(price))}֏**")
        lines.append(f"📊 Վաճառված՝ {base} հատ" if lang=="hy"
                    else f"📊 Продано: {base} шт" if lang=="ru"
                    else f"📊 Sold: {base} pcs")
        return "\n".join(lines)

    # ------------- Product VIEW send/delete helpers -------------
    def _pv_state(uid: int) -> dict:
        return shop_state.setdefault("pv", {}).setdefault(uid, {"msg_ids": [], "idx": 0, "pid": None})

    def _pv_clear(uid: int, chat_id: int):
        st = _pv_state(uid)
        for mid in st.get("msg_ids", []):
            try: bot.delete_message(chat_id, mid)
            except Exception: pass
        st["msg_ids"] = []

    def _pv_kb(pid: str, idx: int, total: int, lang: str) -> types.InlineKeyboardMarkup:
        kb = types.InlineKeyboardMarkup()
        left = types.InlineKeyboardButton("⬅️", callback_data=f"gal:{pid}:{idx-1}")
        page = types.InlineKeyboardButton(f"{idx+1}/{total}", callback_data="noop")
        right= types.InlineKeyboardButton("➡️", callback_data=f"gal:{pid}:{idx+1}")
        kb.row(left, page, right)
        kb.row(types.InlineKeyboardButton(
            {"hy":"➕ Ավելացնել զամբյուղ", "ru":"➕ В корзину", "en":"➕ Add to cart"}[lang],
            callback_data=f"cart:add:{pid}"
        ))
        kb.row(types.InlineKeyboardButton(
            {"hy":"🛒 Բացել զամբյուղը", "ru":"🛒 Открыть корзину", "en":"🛒 Open cart"}[lang],
            callback_data="open:cart"
        ))
        return kb

    def _pv_send_slide(chat_id: int, uid: int, pid: str, idx: int, lang: str):
        cover, gallery, video = _find_media(pid)
        media: List[Path] = []
        if cover: media.append(cover)
        media.extend(gallery)
        total = max(1, len(media))
        # clamp idx
        idx = max(0, min(idx, total-1))

        # delete previous media+caption
        _pv_clear(uid, chat_id)

        # media send
        current = media[idx] if media else None
        if current and current.suffix.lower() in (".jpg",".jpeg",".png"):
            with open(current, "rb") as fh:
                msg_media = bot.send_photo(chat_id, fh)
        elif current and current.suffix.lower() == ".mp4":
            with open(current, "rb") as fh:
                msg_media = bot.send_video(chat_id, fh)
        else:
            msg_media = bot.send_message(chat_id, "📸")

        # caption under media (separate message to keep UX stable)
        cap = _caption_for(pid, lang)
        kb = _pv_kb(pid, idx, total, lang)
        msg_cap = bot.send_message(chat_id, cap, reply_markup=kb, parse_mode=None)

        st = _pv_state(uid)
        st["msg_ids"] = [getattr(msg_media, "message_id", None), getattr(msg_cap, "message_id", None)]
        st["idx"] = idx
        st["pid"] = pid

    # ------------- OPEN SHOP (from main menu) -------------
    from src.core.pu.pu02_main_menu import LABELS as LBL
    @bot.message_handler(func=lambda m: isinstance(getattr(m,"text",None), str)
                         and any(m.text.strip()==LBL[l]["shop"] for l in LBL))
    def __open_shop(m: types.Message):
        uid = m.from_user.id
        cleanup_msgs(m.chat.id, uid)
        _open_shop(m.chat.id, uid)

    def _open_shop(chat_id: int, uid: int):
        lang = resolve_lang(uid)
        shop_state[uid] = {"mode": "cats", "page_msg_ids": []}
        remember(uid, bot.send_message(chat_id, {
            "hy": "🛍 Ընտրեք կատեգորիա 👇", "ru": "🛍 Выберите категорию 👇", "en": "🛍 Choose a category 👇"
        }[lang], reply_markup=_categories_keyboard(lang), parse_mode=None))

    # ------------- PRODUCTS PAGE (listing) -------------
    def _product_main_image(pid: str, lang: str) -> str | None:
        cover, gallery, _ = _find_media(pid)
        if cover: return str(cover)
        return None

    def _send_products_page(chat_id: int, uid: int, lang: str, cat_id: str, sub_id: str, page: int):
        prods = list(catalog.products(lang, cat_id, sub_id))  # [(pid,title)]
        if not prods:
            remember(uid, bot.send_message(chat_id, {
                "hy":"Դատարկ է։", "ru":"Пусто.", "en":"Empty."
            }[lang], reply_markup=_reply_nav_kb(lang), parse_mode=None))
            return

        per_page = 3
        pages = max(1, (len(prods) + per_page - 1) // per_page)
        page = max(0, min(page, pages - 1))

        _clear_prev_page(uid, chat_id)

        st = shop_state.setdefault(uid, {})
        st.update({"mode": "prods", "cat_id": cat_id, "sub_id": sub_id, "plist": prods, "page": page})
        st["page_msg_ids"] = []

        start = page * per_page
        for pid, _title in prods[start:start + per_page]:
            img = _product_main_image(pid, lang)
            cap = catalog.product_caption(pid, lang)
            ikb = types.InlineKeyboardMarkup()
            ikb.add(types.InlineKeyboardButton({
                "hy":"🔎 Մանրամասներ","ru":"🔎 Детали","en":"🔎 Details"
            }[lang], callback_data=f"pv:{pid}"))
            ikb.row(
                types.InlineKeyboardButton("➕", callback_data=f"cart:add:{pid}"),
                types.InlineKeyboardButton("🛒", callback_data="open:cart")
            )
            try:
                if img and Path(img).exists():
                    with open(img, "rb") as fh:
                        msg = bot.send_photo(chat_id, fh, caption=cap, parse_mode=None, reply_markup=ikb)
                else:
                    msg = bot.send_message(chat_id, cap, parse_mode=None, reply_markup=ikb)
            except Exception:
                msg = bot.send_message(chat_id, cap, parse_mode=None, reply_markup=ikb)
            st["page_msg_ids"].append(getattr(msg, "message_id", None))

        nav = types.InlineKeyboardMarkup()
        nav.row(
            types.InlineKeyboardButton("◀️", callback_data=f"pg:{cat_id}:{sub_id}:{page-1}"),
            types.InlineKeyboardButton(f"{page+1}/{pages}", callback_data="noop"),
            types.InlineKeyboardButton("▶️", callback_data=f"pg:{cat_id}:{sub_id}:{page+1}")
        )
        msg_nav = bot.send_message(chat_id, "⬇️", reply_markup=nav, parse_mode=None)
        st["page_msg_ids"].append(getattr(msg_nav, "message_id", None))
        # նորը
    back_txt, home_txt = _reply_nav_texts(lang)
    remember(uid, bot.send_message(chat_id, " ", reply_markup=_kb_rows([back_txt, home_txt]), parse_mode=None))
  

    # ------------- TEXT ROUTER (cats/subs → prods) -------------
    @bot.message_handler(func=lambda m: isinstance(getattr(m,"text",None), str) and not m.text.startswith('/'))
    def _shop_router(m: types.Message):
        uid = m.from_user.id
        txt = (m.text or "").strip()
        lang = resolve_lang(uid)
        st = shop_state.get(uid) or {}
        mode = st.get("mode")

        if mode == "cats":
            title_to_id = shop_state.get("cats_map", {}).get(lang, {})
            chosen = next((cid for title, cid in title_to_id.items() if title in txt), None)
            if not chosen:
                remember(uid, bot.send_message(m.chat.id, {
                    "hy":"Ընտրեք կատեգորիա 👇","ru":"Выберите категорию 👇","en":"Choose a category 👇"
                }[lang], reply_markup=_categories_keyboard(lang)))
                return
            shop_state[uid] = {"mode": "subs", "cat_id": chosen, "page_msg_ids": []}
            remember(uid, bot.send_message(m.chat.id, {
                "hy":"Ընտրեք ենթակատեգորիա 👇","ru":"Выберите подкатегорию 👇","en":"Choose a subcategory 👇"
            }[lang], reply_markup=_subcats_keyboard(lang, chosen)))
            return

        if mode == "subs":
            cat_id = st.get("cat_id", "")
            title_to_sid = shop_state.get("subs_map", {}).get((lang, cat_id), {})
            chosen = next((sid for title, sid in title_to_sid.items() if title in txt), None)
            if not chosen:
                remember(uid, bot.send_message(m.chat.id, {
                    "hy":"Ընտրեք ենթակատեգորիա 👇","ru":"Выберите подкатегорию 👇","en":"Choose a subcategory 👇"
                }[lang], reply_markup=_subcats_keyboard(lang, cat_id)))
                return
            shop_state[uid] = {"mode": "prods", "cat_id": cat_id, "sub_id": chosen, "page": 0, "page_msg_ids": []}
            _send_products_page(m.chat.id, uid, lang, cat_id, chosen, page=0)
            return

        if mode == "prods":
            _send_products_page(m.chat.id, uid, lang, st.get("cat_id",""), st.get("sub_id",""), st.get("page",0))
            return

    # ------------- CALLBACKS: paging list -------------
    @bot.callback_query_handler(func=lambda c: isinstance(c.data, str) and c.data.startswith("pg:"))
    def _cb_products_page(c: types.CallbackQuery):
        _, cat_id, sub_id, page_s = c.data.split(":")
        uid = c.from_user.id
        lang = resolve_lang(uid)
        try: page = int(page_s)
        except: page = 0
        bot.answer_callback_query(c.id)
        _send_products_page(c.message.chat.id, uid, lang, cat_id, sub_id, page)

    # ------------- CALLBACKS: open product view + gallery nav -------------
    @bot.callback_query_handler(func=lambda c: isinstance(c.data, str) and c.data.startswith("pv:"))
    def _cb_product_view(c: types.CallbackQuery):
        uid = c.from_user.id
        chat_id = c.message.chat.id
        lang = resolve_lang(uid)
        pid = c.data.split(":", 1)[1]
        bot.answer_callback_query(c.id)
        _pv_send_slide(chat_id, uid, pid, idx=0, lang=lang)

    @bot.callback_query_handler(func=lambda c: isinstance(c.data, str) and c.data.startswith("gal:"))
    def _cb_gallery_nav(c: types.CallbackQuery):
        # gal:{pid}:{idx}
        parts = c.data.split(":")
        pid = parts[1]
        try: idx = int(parts[2])
        except: idx = 0
        uid = c.from_user.id
        lang = resolve_lang(uid)
        bot.answer_callback_query(c.id)
        _pv_send_slide(c.message.chat.id, uid, pid, idx, lang)

    # open cart from inline (from pv or list)
    @bot.callback_query_handler(func=lambda c: c.data == "open:cart")
    def _cb_open_cart(c: types.CallbackQuery):
        api = shop_state.setdefault("api", {})
        show = api.get("cart_ui") or api.get("cart_ui_show")
        bot.answer_callback_query(c.id)
        if callable(show):
            try:
                if getattr(show, "__code__", None) and show.__code__.co_argcount >= 2:
                    show(bot, c.message)
                else:
                    show(c.message.chat.id)
            except Exception as e:
                bot.send_message(c.message.chat.id, f"⚠️ Cart UI error: {e}", parse_mode=None)

def healthcheck(_): 
    return True
