# PU30 — Performance & Cache (TTL cache + simple memo + timings)

import time
from functools import wraps
from datetime import datetime

def _now_iso():
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def _ensure(shop_state):
    shop_state.setdefault("perf", {
        "cache": {},           # key -> {value, expire_at}
        "timings": {},         # name -> {count, total_ms, last_ms, last_ts}
        "hits": 0,
        "miss": 0
    })

def init(bot, resolve_lang, catalog, shop_state):
    """
    features['perf'] API
      - set(key, value, ttl_sec=60)
      - get(key, default=None)
      - memo(ttl_sec=60) -> decorator
      - timeit(name) -> decorator
      - stats() -> dict
      - purge(prefix=None)
    """
    _ensure(shop_state)
    feats = shop_state.setdefault("features", {})
    api = feats.setdefault("perf", {})

    def set_(key, value, ttl_sec=60):
        shop_state["perf"]["cache"][str(key)] = {
            "value": value,
            "expire_at": time.time() + max(1, int(ttl_sec))
        }
        return True

    def get(key, default=None):
        rec = shop_state["perf"]["cache"].get(str(key))
        if not rec:
            shop_state["perf"]["miss"] += 1
            return default
        if rec["expire_at"] < time.time():
            shop_state["perf"]["cache"].pop(str(key), None)
            shop_state["perf"]["miss"] += 1
            return default
        shop_state["perf"]["hits"] += 1
        return rec["value"]

    def purge(prefix=None):
        if prefix is None:
            shop_state["perf"]["cache"].clear()
            return 0
        to_del = [k for k in shop_state["perf"]["cache"].keys() if str(k).startswith(str(prefix))]
        for k in to_del:
            shop_state["perf"]["cache"].pop(k, None)
        return len(to_del)

    def memo(ttl_sec=60):
        def deco(fn):
            @wraps(fn)
            def wrapper(*args, **kwargs):
                key = f"memo::{fn.__module__}.{fn.__name__}::{args}::{tuple(sorted(kwargs.items()))}"
                val = get(key, None)
                if val is not None:
                    return val
                res = fn(*args, **kwargs)
                set_(key, res, ttl_sec=ttl_sec)
                return res
            return wrapper
        return deco

    def timeit(name):
        def deco(fn):
            @wraps(fn)
            def wrapper(*args, **kwargs):
                t0 = time.time()
                try:
                    return fn(*args, **kwargs)
                finally:
                    ms = int((time.time() - t0) * 1000)
                    t = shop_state["perf"]["timings"].setdefault(str(name), {"count": 0, "total_ms": 0, "last_ms": 0, "last_ts": _now_iso()})
                    t["count"] += 1
                    t["total_ms"] += ms
                    t["last_ms"] = ms
                    t["last_ts"] = _now_iso()
            return wrapper
        return deco

    def stats():
        return {
            "cache_size": len(shop_state["perf"]["cache"]),
            "hits": shop_state["perf"]["hits"],
            "miss": shop_state["perf"]["miss"],
            "timings": dict(shop_state["perf"]["timings"]),
        }

    api.update({
        "set": set_,
        "get": get,
        "memo": memo,
        "timeit": timeit,
        "stats": stats,
        "purge": purge,
    })


def init(bot, ctx):
    def feature(bot, m):
        bot.send_message(m.chat.id, "✅ pu30_perf_cache աշխատեց")
    ctx["shop_state"].setdefault("api", {})["perf_cache"] = feature



