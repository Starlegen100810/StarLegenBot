# src/core/pu/pu19_analytics.py
# PU19 — Lightweight Analytics & Events
# Պահում է event-ների հոսք, գումարում պարզ KPI-ներ, տալիս ամփոփ հաշվետվություն։

from datetime import datetime
from collections import defaultdict
from typing import Dict, Any, List, Optional

EVENT_TYPES = (
    "product_view",      # {product_id}
    "add_to_cart",       # {product_id, qty}
    "search",            # {q}
    "order_created",     # {order_id, total, currency}
    "order_paid",        # {order_id, total, currency, product_ids?}
    "deal_view",         # {deal_id}
    "page",              # {name}
)

def _now_iso():
    # seconds+Z, որ մաքուր տեսք ունենա
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def _ensure_structs(shop_state: dict) -> dict:
    a = shop_state.setdefault("analytics", {})
    a.setdefault("events", [])               # պահում ենք վերջին N իրադարձությունները
    a.setdefault("limits", {"max_events": 5000})
    k = a.setdefault("kpi", {})
    k.setdefault("views", 0)
    k.setdefault("adds", 0)
    k.setdefault("searches", 0)
    k.setdefault("orders", 0)
    k.setdefault("paid_orders", 0)
    k.setdefault("revenue", 0.0)
    # defaultdict-ը pickle-friendly չի լինում միշտ, պահենք պարզ dict-ով
    k.setdefault("by_product", {})          # product_id(str) -> views
    return a

def _push_event(shop_state: dict, evt_type: str, user_id: Optional[int] = None, **payload) -> bool:
    if evt_type not in EVENT_TYPES:
        return False
    a = _ensure_structs(shop_state)
    ev = {"ts": _now_iso(), "type": evt_type, "user_id": user_id, "data": payload}
    a["events"].append(ev)

    # trim ring-buffer
    maxn = int(a["limits"].get("max_events", 5000))
    if len(a["events"]) > maxn:
        a["events"] = a["events"][-maxn:]

    # KPI update
    k = a["kpi"]
    if evt_type == "product_view":
        k["views"] += 1
        pid = str(payload.get("product_id") or "")
        if pid:
            k["by_product"][pid] = int(k["by_product"].get(pid, 0)) + 1
    elif evt_type == "add_to_cart":
        k["adds"] += 1
    elif evt_type == "search":
        k["searches"] += 1
    elif evt_type == "order_created":
        k["orders"] += 1
    elif evt_type == "order_paid":
        k["paid_orders"] += 1
        try:
            k["revenue"] = float(k.get("revenue", 0.0)) + float(payload.get("total") or 0)
        except Exception:
            pass
    return True

def _kpis(shop_state: dict) -> Dict[str, Any]:
    a = _ensure_structs(shop_state)
    k = a["kpi"]
    # copy/derived
    top_products = sorted(
        [(pid, cnt) for pid, cnt in (k.get("by_product") or {}).items()],
        key=lambda x: x[1],
        reverse=True
    )[:10]
    return {
        "views": k.get("views", 0),
        "adds": k.get("adds", 0),
        "searches": k.get("searches", 0),
        "orders": k.get("orders", 0),
        "paid_orders": k.get("paid_orders", 0),
        "revenue": round(float(k.get("revenue", 0.0)), 2),
        "top_products": top_products,
    }

def _last(shop_state: dict, n: int = 50, evt_type: Optional[str] = None) -> List[dict]:
    a = _ensure_structs(shop_state)
    rows = a["events"][-int(n):]
    if evt_type:
        rows = [e for e in rows if e.get("type") == evt_type]
    return rows

def _inc_view(shop_state: dict, product_id, user_id: Optional[int] = None) -> bool:
    return _push_event(shop_state, "product_view", user_id, product_id=str(product_id))

def register(bot, ctx):
    """
    PU19 Analytics:
      • Public feature API (ctx['shop_state']['features']['analytics']): track/kpis/last/inc_view
      • Reply-menu hook: api['analytics']  -> KPI ամփոփ ցուցադրություն
      • Optional bot.on hooks:
          - /kpi    -> KPI summary
          - /events -> վերջին 20 իրադարձությունը
    """
    shop_state = ctx["shop_state"]
    _ensure_structs(shop_state)

    # ---- Feature API (programmatic access) ----
    feats = shop_state.setdefault("features", {})
    feats.setdefault("analytics", {}).update({
        "track":     lambda evt_type, user_id=None, **payload: _push_event(shop_state, evt_type, user_id, **payload),
        "kpis":      lambda: _kpis(shop_state),
        "last":      lambda n=50, evt_type=None: _last(shop_state, n, evt_type),
        "inc_view":  lambda product_id, user_id=None: _inc_view(shop_state, product_id, user_id),
    })

    # ---- Reply-menu hook (📊 օրվա կուրս / analytics) ----
    api = shop_state.setdefault("api", {})
    def _entry(bot2, m):
        k = _kpis(shop_state)
        lines = [
            "📊 Analytics (վերջնական ամփոփ)",
            f"👁 Դիտումներ: {k['views']}",
            f"➕ Զամբյուղ ավելացումներ: {k['adds']}",
            f"🔎 Որոնումներ: {k['searches']}",
            f"🧾 Պատվերներ: {k['orders']}",
            f"✅ Վճարված պատվերներ: {k['paid_orders']}",
            f"💰 Շահույթ: {k['revenue']}",
        ]
        tp = k.get("top_products") or []
        if tp:
            lines.append("🏆 Թոփ ապրանքներ ըստ դիտումների:")
            for pid, cnt in tp[:5]:
                lines.append(f"  • #{pid} — {cnt}")
        bot2.send_message(m.chat.id, "\n".join(lines), parse_mode=None)
    api["analytics"] = _entry

    # ---- Optional command/event hooks if supported ----
    on = getattr(bot, "on", None)
    if not callable(on):
        return

    @on("cmd:/kpi")
    def _cmd_kpi(ctx2):
        k = _kpis(shop_state)
        lines = [
            "📊 KPI ամփոփ",
            f"👁 Դիտումներ: {k['views']}",
            f"➕ Զամբյուղ ավելացումներ: {k['adds']}",
            f"🔎 Որոնումներ: {k['searches']}",
            f"🧾 Պատվերներ: {k['orders']}",
            f"✅ Վճարված պատվերներ: {k['paid_orders']}",
            f"💰 Շահույթ: {k['revenue']}",
        ]
        bot.send(ctx2["user_id"], "\n".join(lines))

    @on("cmd:/events")
    def _cmd_events(ctx2):
        rows = _last(shop_state, n=20)
        if not rows:
            bot.send(ctx2["user_id"], "Դատարկ է։")
            return
        lines = ["🧩 Վերջին իրադարձությունները (20):"]
        for e in rows:
            lines.append(f"• {e['ts']} • {e['type']} • {e.get('data',{})}")
        bot.send(ctx2["user_id"], "\n".join(lines))

    # օրինակ՝ վճարման պահին գրանցել order_paid event (եթե ուրիշ PU-երը emit են անում)
    @on("event:order:paid")
    def _evt_paid(ctx2):
        total = ctx2.get("total", 0)
        currency = ctx2.get("currency", "AMD")
        _push_event(shop_state, "order_paid", ctx2.get("user_id"), order_id=ctx2.get("order_id"), total=total, currency=currency)




