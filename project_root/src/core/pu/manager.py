# src/core/pu/manager.py
from __future__ import annotations
import importlib
import pkgutil
from types import ModuleType
from typing import Callable

PACKAGE = "src.core.pu"   # որտեղ են puXX_*.py ֆայլերը


def _wrap_handler(key: str, fn: Callable) -> Callable:
    """
    Փաթեթավորում ենք PU handler-ը, որ միշտ լինի անվտանգ վարքագիծը։
    - ջնջում է օգտվողի սեղմած մեսիջը (եթե կա)
    - կանչում է իրական handler-ը
    - եթե handler-ը ոչինչ չուղարկի/քաշվի՝ ցույց է տալիս fallback հաղորդագրություն
    """
    def safe(bot, m):
        # փորձենք մաքրել user's bubble-ը
        try:
            if getattr(m, "chat", None) and getattr(m, "message_id", None):
                bot.delete_message(m.chat.id, m.message_id)
        except Exception:
            pass

        sent_ok = True
        try:
            r = fn(bot, m)
            # եթե handler-ը վերադարձնում է "False", հասկանում ենք՝ ինքը չուզեց պատասխանել
            if r is False:
                sent_ok = False
        except Exception as e:
            sent_ok = False
            try:
                bot.send_message(m.chat.id, f"❌ PU «{key}» սխալվեց: {e}", parse_mode=None)
            except Exception:
                pass

        if not sent_ok:
            try:
                bot.send_message(
                    m.chat.id,
                    f"⚙️ PU «{key}» դեռ development է, բայց կոճակը աշխատում է ✅",
                    parse_mode=None
                )
            except Exception:
                pass

    return safe


def _safe_call_register(mod: ModuleType, bot, ctx, api: dict) -> list[str]:
    """
    Փորձում է մոդուլում գտնել գրանցող ֆունկցիա և կանչել այն.
    Նախընտրելի վերնագրեր՝ register(bot, ctx), register(ctx), register(api), init/attach/setup
    Վերադարձնում է այն api key-երի ցուցակը, որ մոդուլը ավելացրեց (եթե կարողացանք որոշել)
    """
    added_before = set(api.keys())

    # 1) ամենատարածված տարբերակ — register(bot, ctx)
    fn: Callable | None = getattr(mod, "register", None)
    if callable(fn):
        try:
            try:
                fn(bot=bot, ctx=ctx)
            except TypeError:
                try:
                    fn(ctx)
                except TypeError:
                    try:
                        fn(api)
                    except TypeError:
                        fn()
        except Exception as e:
            print(f"[PU] register failed in {mod.__name__}: {e}")

    # 2) fallback անուններ
    for alt in ("init", "attach", "setup"):
        fn = getattr(mod, alt, None)
        if callable(fn):
            try:
                try:
                    fn(bot=bot, ctx=ctx, api=api)
                except TypeError:
                    try:
                        fn(bot, ctx, api)
                    except TypeError:
                        try:
                            fn(bot, ctx)
                        except TypeError:
                            fn(api)
            except Exception as e:
                print(f"[PU] {alt} failed in {mod.__name__}: {e}")

    # --- ավելացած բանալիների հաշվառումը + փաթեթավորում ---
    added_after = set(api.keys())
    new_keys = sorted(list(added_after - added_before))

    # բոլոր նոր գրանցվածների վրա դնենք wrapper, որ auto-delete + fallback լինի
    for k in new_keys:
        if callable(api.get(k)):
            api[k] = _wrap_handler(k, api[k])

    # եթե ոչինչ չավելացվեց, գոնե փորձենք file-name-ից գուշակել key և դնել fallback
    if not new_keys:
        guessed = mod.__name__.split(".")[-1]    # pu23_history
        if guessed.startswith("pu"):
            guessed = guessed.split("_", 1)[-1]  # history
        if guessed and guessed not in api:
            def _fallback(bot, m, g=guessed):
                try:
                    # delete user bubble
                    if getattr(m, "chat", None) and getattr(m, "message_id", None):
                        bot.delete_message(m.chat.id, m.message_id)
                except Exception:
                    pass
                try:
                    bot.send_message(
                        m.chat.id,
                        f"⚙️ PU «{g}» դեռ development է, բայց կոճակը աշխատում է ✅",
                        parse_mode=None
                    )
                except Exception:
                    pass
            api[guessed] = _wrap_handler(guessed, _fallback)
            new_keys = [guessed]

    return new_keys

def register_all(bot, ctx):
    api = ctx["shop_state"].setdefault("api", {})

    # Վերցնում ենք src.core.pu փաթեթի իրական __path__ արժեքը
    from . import __path__ as PKG_PATH

    loaded = 0
    for _finder, name, _ispkg in pkgutil.iter_modules(PKG_PATH):
        if not name.startswith("pu"):
            continue
        try:
            mod = importlib.import_module(f"{PACKAGE}.{name}")
        except Exception as e:
            print(f"[PU] import failed: {name}: {e}")
            continue

        added_keys = _safe_call_register(mod, bot, ctx, api)
        loaded += 1
        if added_keys:
            print(f"[PU] {name}: + {', '.join(added_keys)}")
        else:
            print(f"[PU] {name}: registered (keys unknown)")

    print(f"[PU] Done. Modules loaded: {loaded}, API keys: {len(api)}")


