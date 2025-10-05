# PU07 – Ratings (1–5 աստղ), aggregate avg + count per SKU
from typing import Dict, Any, List
import math

def _emit(bot, shop_state: Dict[str, Any], event: str, payload: Dict[str, Any]):
    try:
        emit = getattr(bot, "emit", None)
        if callable(emit):
            emit(event, payload)
            return
    except Exception:
        pass
    q = shop_state.setdefault("__events__", [])
    q.append({"event": event, "payload": payload})

def _store(shop_state: Dict[str, Any]):
    """
    ratings = {
      sku: {
        "sum": int,
        "count": int,
        "by_user": { user_id: stars }
      }
    }
    """
    return shop_state.setdefault("ratings", {})

def rate(shop_state: Dict[str, Any], user_id: int, sku: str, stars: int):
    stars = int(max(1, min(5, stars)))
    st = _store(shop_state)
    r = st.setdefault(sku, {"sum": 0, "count": 0, "by_user": {}})
    prev = int(r["by_user"].get(user_id, 0))
    if prev:
        # update
        r["sum"] -= prev
        r["sum"] += stars
        r["by_user"][user_id] = stars
    else:
        r["sum"] += stars
        r["count"] += 1
        r["by_user"][user_id] = stars

def get(shop_state: Dict[str, Any], sku: str) -> Dict[str, Any]:
    r = _store(shop_state).get(sku, {"sum": 0, "count": 0, "by_user": {}})
    avg = (r["sum"] / r["count"]) if r["count"] else 0.0
    return {
        "avg": round(avg, 2),
        "count": int(r["count"]),
    }

def user_rating(shop_state: Dict[str, Any], user_id: int, sku: str) -> int:
    r = _store(shop_state).get(sku, {"by_user": {}})
    return int(r["by_user"].get(user_id, 0))

def summary_line(shop_state: Dict[str, Any], sku: str) -> str:
    stat = get(shop_state, sku)
    if stat["count"] == 0:
        return "⭐️ Վարկանիշ դեռ չկա"
    full = "⭐" * int(round(stat["avg"]))
    return f"{full} ({stat['avg']}/5, {stat['count']} կարծիք)"

def _show_rate_ui(bot, resolve_lang, catalog, shop_state, user_id: int, sku: str):
    # պարզ տեքստային UI՝ 5 աստղ կոճակներով
    getp = getattr(catalog, "get_product", None)
    prod = getp(sku, resolve_lang(user_id)) if callable(getp) else {"name": sku}
    name = prod.get("name", sku)
    already = user_rating(shop_state, user_id, sku)
    head = f"Գնահատիր «{name}» ապրանքը"
    sub = f"Քո ընթացիկ գնահատականը՝ {already}⭐" if already else "Ընտրիր 1–5 ⭐️"
    text = f"{head}\n{sub}"

    ui = getattr(bot, "ui", None)
    if callable(ui):
        rows = [[{"text": f"{i}⭐", "data": f"rating:set:{i}", "data_sku": sku}] for i in range(1, 6)]
        rows.append([{"text": "⬅️ Փակել", "data": "home"}])
        ui(user_id, text, rows=rows)
    else:
        bot.send(user_id, text + "\n(գրի՛ր՝ /rate 5)")

def _register_api(shop_state):
    api = shop_state.setdefault("api", {})
    r_api = api.setdefault("ratings", {})
    r_api.update({
        "rate": rate,
        "get": get,
        "user_rating": user_rating,
        "summary": summary_line,
    })

def init(bot, resolve_lang, catalog, shop_state):
    """
    PU07 Ratings — 1–5 աստղ, aggregate avg + count:
    - API: rate/get/user_rating/summary
    - Events: rating:updated
    - UI hooks: /rate, tap:rating:set:{1..5}
    """
    _register_api(shop_state)

    on = getattr(bot, "on", None)
    if not callable(on):
        return

    @on("cmd:/rate")
    def _cmd_rate(ctx):
        # օգտագործում: /rate <sku> <stars?>
        user_id = ctx["user_id"]
        args = (ctx.get("text") or "").strip().split()
        # սպասում ենք "/rate sku [stars]"
        if len(args) >= 2:
            sku = args[1]
        else:
            bot.send(user_id, "Օգտագործում․ /rate {SKU} [1..5]")
            return
        if len(args) >= 3 and args[2].isdigit():
            stars = int(args[2])
            rate(shop_state, user_id, sku, stars)
            _emit(bot, shop_state, "rating:updated", {"user_id": user_id, "sku": sku, "stars": stars})
            stat = get(shop_state, sku)
            bot.send(user_id, f"Շնորհակալություն 🙏 Վարկանիշը՝ {stat['avg']}/5 ({stat['count']} կարծիք)")
        else:
            _show_rate_ui(bot, resolve_lang, catalog, shop_state, user_id, sku)

    # Tap handlers 1..5
    for i in range(1, 6):
        @on(f"tap:rating:set:{i}")
        def _set(ctx, _i=i):
            user_id = ctx["user_id"]
            sku = ctx.get("sku") or ctx.get("data_sku")
            if not sku:
                return
            rate(shop_state, user_id, sku, _i)
            _emit(bot, shop_state, "rating:updated", {"user_id": user_id, "sku": sku, "stars": _i})
            stat = get(shop_state, sku)
            stars_txt = "⭐" * _i
            msg = f"{stars_txt} Գրանցվեց։ Ընդհանուր՝ {stat['avg']}/5 ({stat['count']})"
            if hasattr(bot, "flash"):
                bot.flash(user_id, msg)
            else:
                bot.send(user_id, msg)
# synced from laptop ✅




