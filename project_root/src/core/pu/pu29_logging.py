# PU29 — Event Logging / Audit (lightweight, in-memory ring buffers + export)

from collections import deque
from datetime import datetime

DEFAULT_LIMIT = 5000

def _now_iso():
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def _ensure(shop_state):
    shop_state.setdefault("log", {
        "events": deque(maxlen=DEFAULT_LIMIT),     # generic events
        "errors": deque(maxlen=2000),              # errors/exceptions
        "orders": deque(maxlen=3000),              # order lifecycle
        "security": deque(maxlen=3000),            # auth, admin actions
        "limit": DEFAULT_LIMIT,
    })

def init(bot, resolve_lang, catalog, shop_state):
    """
    features['log'] API
      - write(channel, kind, message, **fields)
      - error(message, **fields)
      - read(channel, limit=100, kind=None) -> list[dict]
      - export(channel) -> list[dict]
      - set_limit(n) -> int
      - snapshot() -> dict
    channels: events/errors/orders/security
    """
    _ensure(shop_state)
    feats = shop_state.setdefault("features", {})
    api = feats.setdefault("log", {})

    def _write(channel, kind, message, **fields):
        ch = shop_state["log"].get(channel)
        if ch is None:
            return False
        rec = {"ts": _now_iso(), "kind": str(kind), "msg": str(message), **fields}
        ch.append(rec)
        return True

    def write(channel, kind, message, **fields):
        return _write(str(channel), kind, message, **fields)

    def error(message, **fields):
        return _write("errors", "error", message, **fields)

    def read(channel, limit=100, kind=None):
        ch = shop_state["log"].get(str(channel))
        if ch is None:
            return []
        data = list(ch)[-int(limit):]
        if kind:
            data = [r for r in data if r.get("kind") == kind]
        return data

    def export(channel):
        return list(shop_state["log"].get(str(channel), []))

    def set_limit(n):
        n = max(100, int(n))
        shop_state["log"]["limit"] = n
        # recreate deques with new limit for "events" only (others keep own caps)
        shop_state["log"]["events"] = deque(shop_state["log"]["events"], maxlen=n)
        return n

    def snapshot():
        return {
            "sizes": {k: len(v) if hasattr(v, "__len__") else 0 for k, v in shop_state["log"].items() if k != "limit"},
            "limit": shop_state["log"]["limit"]
        }

    api.update({
        "write": write,
        "error": error,
        "read": read,
        "export": export,
        "set_limit": set_limit,
        "snapshot": snapshot,
    })


def init(bot, ctx):
    def feature(bot, m):
        bot.send_message(m.chat.id, "✅ pu29_logging աշխատեց")
    ctx["shop_state"].setdefault("api", {})["logging"] = feature




