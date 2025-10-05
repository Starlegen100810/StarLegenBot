# src/core/pu/pu16_search.py
# PU16 – Product Search (simple)
from __future__ import annotations
from typing import Dict, Any, List, Tuple
from telebot import types

def init(bot, ctx):
    """
    Ստանդարտ ստորագրություն՝ init(bot, ctx)
    ctx = {"resolve_lang": ..., "catalog": ..., "shop_state": ...}
    """
    resolve_lang = ctx["resolve_lang"]
    catalog = ctx["catalog"]
    shop_state: Dict[str, Any] = ctx["shop_state"]

    # ---------- helpers ----------
    def _get_title(pid: str, lang: str) -> str:
        # முயնում ենք օգտագործել քո catalog API-ները՝ fallback-ով
        getp = getattr(catalog, "get_product", None)
        pdata = getp(pid, lang) if callable(getp) else None
        if not pdata:
            pdata = catalog.product_data(pid, lang) or {}
        name = pdata.get("name") or pdata.get("title") or pid
        return str(name)

    def _all_pids(lang: str) -> List[str]:
        # preference: եթե կա catalog.list_products(lang) → օգտագործում ենք
        lp = getattr(catalog, "list_products", None)
        if callable(lp):
            try:
                # սպասում ենք [(pid, title), ...] կամ ["PID", ...]
                items = lp(lang) or []
                if items and isinstance(items[0], (list, tuple)):
                    return [pid for pid, _ in items]
                return [str(x) for x in items]
            except Exception:
                pass
        # fallback՝ catalog.PRODUCTS key-երը
        try:
            return list(catalog.PRODUCTS.keys())
        except Exception:
            return []

    def _search(q: str, lang: str, limit: int = 30) -> List[Tuple[str, str]]:
        qn = (q or "").strip().lower()
        if not qn:
            return []
        # Եթե կա պատրաստի search API
        sp = getattr(catalog, "search_products", None)
        if callable(sp):
            try:
                items = sp(qn, lang) or []
                # սպասվող ֆորմատ՝ [(pid, title)] կամ պարզապես pid-երի list
                out: List[Tuple[str, str]] = []
                if items:
                    if isinstance(items[0], (list, tuple)) and len(items[0]) >= 1:
                        for row in items:
                            pid = str(row[0])
                            title = str(row[1]) if len(row) > 1 else _get_title(pid, lang)
                            out.append((pid, title))
                    else:
                        for pid in items:
                            pid = str(pid)
                            out.append((pid, _get_title(pid, lang)))
                return out[:limit]
            except Exception:
                pass

        # fallback՝ պարզ substring համեմատությամբ
        res: List[Tuple[str, str]] = []
        for pid in _all_pids(lang):
            title = _get_title(pid, lang)
            if qn in title.lower() or qn in str(pid).lower():
                res.append((pid, title))
                if len(res) >= limit:
                    break
        return res

    def _results_text(query: str, items: List[Tuple[str, str]]) -> str:
        if not items:
            return f"🔍 «{query}» — արդյունք չգտնվեց։"
        lines = [f"🔍 Արդյունքներ «{query}» հարցման համար:", ""]
        for i, (pid, title) in enumerate(items, 1):
            lines.append(f"{i}. {title}")
        lines.append("")
        lines.append("💡 Սեղմեք «Բացել»՝ նկարը/մանրամասնությունները դիտելու համար։")
        return "\n".join(lines)

    def _results_kb(items: List[Tuple[str, str]]) -> types.InlineKeyboardMarkup:
        kb = types.InlineKeyboardMarkup()
        for pid, title in items[:10]:  # 10 կոճակից շատը միանգամից պետք չէ
            kb.add(types.InlineKeyboardButton("🔎 Բացել", callback_data=f"pv:{pid}:open:0"))
        return kb

    # ---------- /search [query] ----------
    @bot.message_handler(commands=['search'])
    def _cmd_search(m: types.Message):
        lang = resolve_lang(m.from_user.id)
        # փորձենք քոմանդի հետ գրված տեքստը որպես query
        txt = (m.text or "").split(maxsplit=1)
        query = txt[1].strip() if len(txt) > 1 else ""
        if not query:
            bot.send_message(m.chat.id, "Գրեք՝ /search բառ", parse_mode=None)
            return
        items = _search(query, lang)
        bot.send_message(m.chat.id, _results_text(query, items),
                         reply_markup=_results_kb(items) if items else None,
                         parse_mode=None)

    # ---------- reply-menu «Որոնել» → բացի input հարցնել ----------
    # Եթե քո գլխավոր մենյուից գալիս ա "🔍 Որոնել" (HY/EN/RU), բռնում ենք՝
    SEARCH_KEYS = ["որոն", "поиск", "search"]  # մասամբ համընկնում
    @bot.message_handler(func=lambda m: isinstance(m.text, str) and any(k in m.text.lower() for k in SEARCH_KEYS))
    def _open_search(m: types.Message):
        bot.send_message(m.chat.id, "✍️ Գրեք՝ /search ձեր բառը (օր՝ /search գորգ)", parse_mode=None)

    # Կարող ես նաև ավելացնել callback բացում, եթե UI-դ տալիս է search բացող inline:
    @bot.callback_query_handler(func=lambda c: c.data == "search:open")
    def _search_open_cb(call: types.CallbackQuery):
        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass
        bot.send_message(call.message.chat.id, "✍️ Գրեք՝ /search ձեր բառը (օր՝ /search գորգ)", parse_mode=None)


def init(bot, ctx):
    def feature(bot, m):
        bot.send_message(m.chat.id, "✅ pu16_search աշխատեց")
    ctx["shop_state"].setdefault("api", {})["search"] = feature




