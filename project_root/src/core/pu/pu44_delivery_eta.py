# src/core/pu/pu44_eta.py
from __future__ import annotations
from datetime import datetime
from typing import Dict, Any, Tuple

# ---- Նախնական քարտեզներ (կարող ես խմբագրել) --------------------
CITY_ZONES = {
    "Երևան": "yerevan",
    "Աբովյան": "near",
    "Արտաշատ": "near",
    "Էջմիածին": "near",
    "Գյումրի": "far",
    "Վանաձոր": "far",
    "Կապան": "far",
}

# Base ETA օրերով ըստ գոտու (lo, hi)
BASE_ETA_BY_ZONE = {
    #   standard     express       pickup
    "yerevan": {"standard": (1, 2), "express": (0, 1), "pickup": (0, 1)},
    "near":    {"standard": (2, 3), "express": (1, 2), "pickup": (1, 2)},
    "far":     {"standard": (3, 5), "express": (2, 3), "pickup": (2, 3)},
}

# Ժամային կտրուկ. եթե հիմա > 17:00, +1 օր
CUTOFF_HOUR = 17

# weekend bump (շբթ/կրկ) → +1 օր
WEEKEND_BUMP = True

# Տոն օրերի YYYY-MM-DD ցուցակ (ցանկின் անդամ হলে +1 օր)
HOLIDAYS = set()  # օրինակ՝ {"2025-01-01", "2025-01-06"}

# ---------------------- ներքին utility-ներ -----------------------
def _zone_for_city(city: str, store: Dict[str, Any]) -> str:
    city = (city or "").strip()
    cfg = store.setdefault("eta_cfg", {})
    # allow runtime overrides via /setetazone
    overrides: Dict[str, str] = cfg.setdefault("city_zones", {})
    if city in overrides:
        return overrides[city]
    return CITY_ZONES.get(city, "yerevan")

def _bump_for_time(now: datetime) -> int:
    bump = 0
    if now.hour >= CUTOFF_HOUR:
        bump += 1
    if WEEKEND_BUMP and now.weekday() in (5, 6):  # 5=Saturday, 6=Sunday
        bump += 1
    if now.strftime("%Y-%m-%d") in HOLIDAYS:
        bump += 1
    return bump

def _sum_tuple(tpl: Tuple[int, int], add: int) -> Tuple[int, int]:
    return (tpl[0] + add, tpl[1] + add)

# ---------------------- հանրային API callable --------------------
def eta(store: Dict[str, Any], city: str, method: str) -> Tuple[int, int]:
    """Վերադարձնում է (lo_days, hi_days)."""
    method = (method or "standard").lower()
    if method not in ("standard", "express", "pickup"):
        method = "standard"

    zone = _zone_for_city(city, store)
    base = BASE_ETA_BY_ZONE.get(zone, BASE_ETA_BY_ZONE["yerevan"]).get(method, (2, 4))

    bump = _bump_for_time(datetime.now())
    return _sum_tuple(base, bump)

# --------------------------- register -----------------------------
def register(bot, ctx):
    """
    Գրանցում է api['eta'] callable-ը, որը օգտագործում է PU13-delivery-ը.
      api['eta'](city='Երևան', method='standard') -> (lo, hi)
    Սակայն PU13-ը ինքն է կանչում սա իր «estimate_eta» fallback-ի փոխարեն։
    """
    shop_state = ctx["shop_state"]
    api = shop_state.setdefault("api", {})
    api["eta"] = lambda city="Երևան", method="standard": eta(shop_state, city, method)

    # ---- Օգնական հրամաններ (փոքր debug/կարգավորում) -------------
    try:
        @bot.message_handler(commands=["eta"])
        def _cmd_eta(m):
            # օրինակ՝ /eta express Գյումրի
            parts = (m.text or "").split(maxsplit=2)
            method = parts[1] if len(parts) > 1 else "standard"
            city = parts[2] if len(parts) > 2 else "Երևան"
            lo, hi = eta(shop_state, city, method)
            bot.send_message(m.chat.id, f"ETA for {city} · {method}: {lo}–{hi} օր", parse_mode=None)

        @bot.message_handler(commands=["setetazone"])
        def _cmd_setzone(m):
            # օրինակ՝ /setetazone Դիլիջան near
            parts = (m.text or "").split(maxsplit=2)
            if len(parts) < 3:
                bot.send_message(m.chat.id, "Օրինակ՝ /setetazone Դիլիջան near  (yerevan|near|far)", parse_mode=None)
                return
            city, zone = parts[1].strip(), parts[2].strip().lower()
            if zone not in ("yerevan", "near", "far"):
                bot.send_message(m.chat.id, "Սխալ գոտի. օգտագործիր yerevan|near|far", parse_mode=None)
                return
            cfg = shop_state.setdefault("eta_cfg", {})
            overrides: Dict[str, str] = cfg.setdefault("city_zones", {})
            overrides[city] = zone
            bot.send_message(m.chat.id, f"✅ {city} → {zone} պահպանվեց", parse_mode=None)
    except Exception:
        # production-ում լուռ անցնում ենք, եթե bot-ի վրա command-ները չպետք է լինեն
        pass

