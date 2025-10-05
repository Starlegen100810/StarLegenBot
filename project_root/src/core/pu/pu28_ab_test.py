# PU28 — A/B Test Manager (feature flags + experiments + metrics hooks)

from collections import defaultdict
from hashlib import sha1
from datetime import datetime

def _now_iso():
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def _ensure(shop_state):
    shop_state.setdefault("ab", {
        "flags": {},            # flag -> {"enabled": bool, "variant":"A/B/..."}
        "experiments": {},      # key -> { name, variants:{A:50,B:50}, started_at, ended_at }
        "assignments": {},      # user_id -> {exp_key: "A"}
        "metrics": defaultdict(lambda: defaultdict(int)),  # exp_key -> { "A:click": 10, "B:conv": 2 }
        "timeline": []
    })

def _audit(shop_state, action, **meta):
    shop_state["ab"]["timeline"].append({"ts": _now_iso(), "action": action, "meta": meta})
    shop_state["ab"]["timeline"] = shop_state["ab"]["timeline"][-1000:]

def _weighted_pick(uid, variants):
    # deterministic hash → percent
    seed = int(sha1(str(uid).encode()).hexdigest(), 16) % 100
    total = 0
    for name, pct in variants.items():
        total += int(pct)
        if seed < total:
            return name
    return list(variants.keys())[0]

def init(bot, resolve_lang, catalog, shop_state):
    """
    features['ab'] API
      - flag_set(name, enabled:bool, variant=None)
      - flag_get(name) -> dict|None
      - exp_define(key, name, variants:dict) -> dict
      - exp_assign(user_id, key) -> "A"/"B"/...
      - track(key, user_id, event:str) -> None        (event e.g. "view", "click", "conv")
      - stats(key) -> dict
      - all() -> snapshot
    """
    _ensure(shop_state)
    feats = shop_state.setdefault("features", {})
    api = feats.setdefault("ab", {})

    def flag_set(name, enabled, variant=None):
        shop_state["ab"]["flags"][str(name)] = {"enabled": bool(enabled), "variant": variant}
        _audit(shop_state, "flag_set", name=name, enabled=enabled, variant=variant)
        return shop_state["ab"]["flags"][str(name)]

    def flag_get(name):
        return shop_state["ab"]["flags"].get(str(name))

    def exp_define(key, name, variants):
        # variants: {"A":50,"B":50} (sum≈100)
        shop_state["ab"]["experiments"][str(key)] = {
            "name": name,
            "variants": {k: int(v) for k, v in variants.items()},
            "started_at": _now_iso(),
            "ended_at": None
        }
        _audit(shop_state, "exp_define", key=key, name=name, variants=variants)
        return shop_state["ab"]["experiments"][str(key)]

    def exp_assign(user_id, key):
        key = str(key)
        asg = shop_state["ab"]["assignments"].setdefault(str(user_id), {})
        if key not in asg:
            exp = shop_state["ab"]["experiments"].get(key)
            if not exp:
                return None
            asg[key] = _weighted_pick(user_id, exp["variants"])
        return asg[key]

    def track(key, user_id, event):
        var = exp_assign(user_id, key)
        if var is None:
            return
        shop_state["ab"]["metrics"][str(key)][f"{var}:{event}"] += 1

    def stats(key):
        m = shop_state["ab"]["metrics"].get(str(key), {})
        # roll up totals per variant
        roll = defaultdict(lambda: defaultdict(int))
        for k, v in m.items():
            var, evt = k.split(":", 1)
            roll[var][evt] += int(v)
        return {var: dict(evts) for var, evts in roll.items()}

    def all_snapshot():
        return {
            "flags": dict(shop_state["ab"]["flags"]),
            "experiments": dict(shop_state["ab"]["experiments"]),
            "metrics": {k: dict(v) for k, v in shop_state["ab"]["metrics"].items()},
        }

    api.update({
        "flag_set": flag_set,
        "flag_get": flag_get,
        "exp_define": exp_define,
        "exp_assign": exp_assign,
        "track": track,
        "stats": stats,
        "all": all_snapshot,
    })


def init(bot, ctx):
    def feature(bot, m):
        bot.send_message(m.chat.id, "✅ pu28_ab_test աշխատեց")
    ctx["shop_state"].setdefault("api", {})["ab_test"] = feature




