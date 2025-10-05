# -*- coding: utf-8 -*-
# src/core/main.py — Core runner with auto PU discovery

import os
import logging
from pathlib import Path
import importlib
from typing import Dict, Any, List

import telebot
from telebot import types

# ---------- .env load (project_root/.env) ----------
try:
    from dotenv import load_dotenv
    # որոնենք project_root/.env
    project_root = Path(__file__).resolve().parents[2]
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=False)
        print("[ENV] loaded:", env_file)
    else:
        print("[ENV] .env not found at", env_file)
except Exception as e:
    print("[ENV] dotenv not used:", e)

# ---------- ENV ----------
BOT_TOKEN = (os.getenv("BOT_TOKEN") or "").strip()
APP_NAME  = (os.getenv("APP_NAME") or "StarLegen").strip() or "StarLegen"
DEFAULT_LANG = (os.getenv("DEFAULT_LANG") or "hy").strip()

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN չի գտնվել .env֊ում")

telebot.logger.setLevel(logging.INFO)
bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

# ---------- STATE / CTX ----------
SHOP_STATE: Dict[str, Any] = {}
USER_LANG: Dict[int, str] = {}

def resolve_lang(uid: int, default_lang=DEFAULT_LANG):
    return USER_LANG.get(uid, default_lang)

def remember_msg(uid: int, msg):
    """Հիշում ենք ԲՈՏԻ ուղարկած մեսիջների id-ները՝ հետո ջնջելու համար"""
    if not msg:
        return
    st = SHOP_STATE.setdefault(uid, {})
    st.setdefault("bot_msgs", []).append(getattr(msg, "message_id", None))

def cleanup_bot_msgs(bot, chat_id: int, uid: int):
    """Ջնջում ենք հենց ԲՈՏԻ նախորդ ուղարկած մեսիջները տվյալ օգտվողի համար."""
    st = SHOP_STATE.get(uid, {})
    ids: List[int] = st.pop("bot_msgs", []) or []
    for mid in ids:
        try:
            if mid:
                bot.delete_message(chat_id, mid)
        except Exception:
            pass

CTX = {
    "shop_state": SHOP_STATE,
    "user_lang": USER_LANG,
    "resolve_lang": resolve_lang,
    "remember_msg": remember_msg,
    "cleanup_bot_msgs": lambda chat_id, uid: cleanup_bot_msgs(bot, chat_id, uid),
    "app_name": APP_NAME,
    # Կատալոգը պարտադիր է PU-երի մի մասի համար
    # եթե կա քո մոդուլը, կբեռնենք՝ թե չէ — կգցենք պարզ mock, որ չպետք է production-ում
}

# ---- catalog attach (try real, else minimal fallback so PU05 չընկնի) ----
try:
    from src.commerce import catalog as CATALOG
    CTX["catalog"] = CATALOG
except Exception:
    class _CatMock:
        def categories(self, lang): return [("home", "Տան համար"), ("rugs", "Գորգեր")]
        def subcategories(self, lang, cat_id):
            return [("top", "Թոփ ապրանքներ")] if cat_id else []
        def products(self, lang, cat_id, sub_id):
            return [("demo_sku", "Demo Product")]
        def product_data(self, pid, lang):
            return {"name": "Demo Product", "price": 9900, "images": []}
        def product_caption(self, pid, lang):
            return "Demo Product — 9,900֏"
    print("[WARN] catalog not found → using minimal mock")
    CTX["catalog"] = _CatMock()

# ---------- AUTO DISCOVER PU MODULES ----------
# ---------- AUTO DISCOVER PU MODULES ----------
def _discover_pus():
    project_root = Path(__file__).resolve().parents[2]
    pu_dir = project_root / "src" / "core" / "pu"

    print("[DEBUG] scan dir:", pu_dir)
    found = []
    if pu_dir.exists():
        for f in pu_dir.glob("pu*.py"):
            name = f.stem
            mod  = f"src.core.pu.{name}"
            found.append((name, mod))
    else:
        print("[DEBUG] pu_dir DOES NOT EXIST")

    # ՄԻԱՅՆ այս հիմնական փաթեթը թող աշխատի հիմա (քայլ 1–5 + core)
    priority = [
        "pu01_start",
        "pu02_main_menu",
        "pu03_catalog_ui",
        "pu04_cart",
        "pu05_cart_ui",
        "pu06_checkout_fsm",
        "pu08_checkout_address",
        "pu09_payment",
        "pu10_chekout",       # քո ֆայլի ճշգրիտ անունը
        "pu12_loyalty",
        "pu13_delivery",
        "pu18_admin_import",
        "pu20_notifications",
        "pu31_confirm",
        "pu44_delivery_eta",
        "pu47_reply_kb",
        "pu48_payments_mock",
        # եթե պետք է՝ այս պահին կարող ես նաև քաշել router-ը
        "pu00_menu_router",
    ]

    by_name = {n: m for (n, m) in found}
    # Վերադարձնենք միայն priority-ի intersection-ը,
    # մնացած placeholder-ները դեռ չբեռնենք
    result = [by_name[n] for n in priority if n in by_name]
    print("[DEBUG] discovered PUs (active):", result)
    return result

PU_MODULES = _discover_pus()


# ---------- PU attach ----------
def attach_pu(modpath: str) -> bool:
    try:
        m = importlib.import_module(modpath)
    except Exception as ex:
        print(f"[PU] FAIL import: {modpath}: {ex}")
        return False
    reg = getattr(m, "register", None)
    if not callable(reg):
        print(f"[PU] FAIL register(): {modpath} — register(bot, ctx) not found")
        return False
    try:
        reg(bot, CTX)
    except Exception as ex:
        print(f"[PU] FAIL register call: {modpath}: {ex}")
        return False

    # optional healthcheck
    hc = getattr(m, "healthcheck", None)
    if callable(hc):
        try:
            ok = hc(CTX)
            if ok is False:
                print(f"[PU] WARN healthcheck failed: {modpath}")
        except Exception as ex:
            print(f"[PU] WARN healthcheck error: {modpath}: {ex}")

    print(f"[PU] OK: {modpath}")
    return True

# ---------- Run ----------
def run():
    print(f"{APP_NAME} — starting with up to {len(PU_MODULES)} PUs…")

    # allow PU-երը պահեն իրենց API-ները այստեղ
    SHOP_STATE.setdefault("api", {})

    # Webhook cleanup → անցնենք long-polling-ի
    try:
        bot.remove_webhook()
    except Exception:
        pass

    ok_cnt = 0
    for mod in PU_MODULES:
        ok_cnt += 1 if attach_pu(mod) else 0
    print(f"[PU] Attached: {ok_cnt}/{len(PU_MODULES)}")
    print("Bot is running…")

    bot.infinity_polling(
        interval=0,
        timeout=60,
        long_polling_timeout=60,
        skip_pending=True,
        allowed_updates=["message", "callback_query"],
    )
