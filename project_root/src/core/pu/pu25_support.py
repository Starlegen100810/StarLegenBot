# src/core/pu/pu25_support.py
# PU25 — Support / Helpdesk (tickets + canned replies + SLA)
from datetime import datetime, timedelta
from itertools import count
from typing import Optional, List, Dict, Any

_counter = count(2001)  # ticket IDs

def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def _ensure(shop_state: dict) -> None:
    shop_state.setdefault("support", {
        "tickets": {},        # tid -> record
        "by_user": {},        # uid -> set(tid)
        "queue": [],          # open ticket ids (new/awaiting_admin)
        "canned": {           # id -> text
            "greet": "Շնորհակալություն, դիմումը ստացվել է, շուտով կպատասխանենք։",
            "proof": "Կցեք խնդրում ենք վճարման ապացույցը կամ screenshot-ը։",
            "eta":  "Ձեր հարցումը մշակում ենք, պատասխան՝ մինչև 24 ժամ։",
        },
        "sla_hours": 24,
        "timeline": []        # audit trail (last N)
    })

def _audit(shop_state: dict, tid: int, actor: str|int, action: str, **meta) -> None:
    s = shop_state["support"]
    s["timeline"].append({
        "ts": _now_iso(), "ticket_id": tid, "actor": actor, "action": action, "meta": meta or {}
    })
    s["timeline"] = s["timeline"][-3000:]

def _push_queue(shop_state: dict, tid: int) -> None:
    q = shop_state["support"]["queue"]
    if tid not in q:
        q.append(tid)

def _pop_queue(shop_state: dict, tid: int) -> None:
    q = shop_state["support"]["queue"]
    if tid in q:
        q.remove(tid)

# ---------- Programmatic API ----------
def _create_ticket(shop_state: dict, user_id: int, subject: str, message: str, attachments: Optional[List[str]]=None) -> Dict[str, Any]:
    _ensure(shop_state)
    tid = next(_counter)
    rec = {
        "id": tid,
        "user_id": user_id,
        "subject": (subject or "").strip()[:200],
        "status": "NEW",
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "sla_due": (datetime.utcnow() + timedelta(hours=int(shop_state["support"]["sla_hours"]))).isoformat(timespec="seconds") + "Z",
        "messages": [
            {"ts": _now_iso(), "actor": str(user_id), "role": "user", "text": str(message or ""), "attachments": attachments or []}
        ],
        "private_notes": []
    }
    s = shop_state["support"]
    s["tickets"][tid] = rec
    s["by_user"].setdefault(user_id, set()).add(tid)
    _push_queue(shop_state, tid)
    _audit(shop_state, tid, user_id, "CREATE", subject=rec["subject"])
    return rec

def _set_status(rec: Dict[str, Any], status: str) -> None:
    rec["status"] = status
    rec["updated_at"] = _now_iso()

def _add_reply(shop_state: dict, ticket_id: int, actor: str|int, message: str,
               attachments: Optional[List[str]]=None, private: bool=False) -> bool:
    _ensure(shop_state)
    rec = shop_state["support"]["tickets"].get(int(ticket_id))
    if not rec:
        return False
    if private:
        rec["private_notes"].append({"ts": _now_iso(), "actor": str(actor), "text": str(message or ""), "attachments": attachments or []})
        _audit(shop_state, ticket_id, actor, "NOTE")
    else:
        role = "admin" if (not str(actor).isdigit() or actor != rec["user_id"]) else "user"
        rec["messages"].append({"ts": _now_iso(), "actor": str(actor), "role": role, "text": str(message or ""), "attachments": attachments or []})
        if role == "admin":
            _set_status(rec, "AWAITING_USER"); _pop_queue(shop_state, ticket_id)
        else:
            _set_status(rec, "AWAITING_ADMIN"); _push_queue(shop_state, ticket_id)
        _audit(shop_state, ticket_id, actor, "REPLY", role=role)
    return True

def _close(shop_state: dict, ticket_id: int, actor: str|int) -> bool:
    rec = shop_state["support"]["tickets"].get(int(ticket_id))
    if not rec:
        return False
    _set_status(rec, "CLOSED")
    _pop_queue(shop_state, int(ticket_id))
    _audit(shop_state, ticket_id, actor, "CLOSE")
    return True

def _get(shop_state: dict, ticket_id: int) -> Optional[Dict[str, Any]]:
    return shop_state["support"]["tickets"].get(int(ticket_id))

def _list_user(shop_state: dict, user_id: int) -> List[Dict[str, Any]]:
    ids = sorted(shop_state["support"]["by_user"].get(user_id, []))
    return [shop_state["support"]["tickets"][i] for i in ids]

def _queue_view(shop_state: dict) -> List[int]:
    return list(shop_state["support"]["queue"])

def _set_sla(shop_state: dict, hours: int) -> int:
    try:
        shop_state["support"]["sla_hours"] = int(hours)
    except Exception:
        pass
    return int(shop_state["support"]["sla_hours"])

def _set_canned(shop_state: dict, key: str, text: str) -> bool:
    shop_state["support"]["canned"][str(key)] = str(text or ""); return True

def _get_canned(shop_state: dict, key: str) -> Optional[str]:
    return shop_state["support"]["canned"].get(str(key))

def _suggest_canned(shop_state: dict, text: str) -> List[str]:
    t = (text or "").lower()
    hits = []
    for k, v in shop_state["support"]["canned"].items():
        if any(w in t for w in (k.lower(), *(v.lower().split()[:3]))):
            hits.append(k)
    return hits[:5]

def _stats(shop_state: dict) -> Dict[str, Any]:
    s = {"NEW": 0, "AWAITING_ADMIN": 0, "AWAITING_USER": 0, "RESOLVED": 0, "CLOSED": 0}
    for r in shop_state["support"]["tickets"].values():
        s[r["status"]] = s.get(r["status"], 0) + 1
    return {"by_status": s, "open_queue": len(shop_state["support"]["queue"]), "sla_hours": shop_state["support"]["sla_hours"]}

# ---------- Wiring ----------
def register(bot, ctx):
    """
    PU25 Support
      • features['support'] API (programmatic)
      • reply-menu hook api['support']  → բացում է Support intro + quick actions
    """
    shop_state = ctx["shop_state"]
    _ensure(shop_state)

    # Programmatic feature API, հասանելի՝ shop_state['features']['support']-ից
    feats = shop_state.setdefault("features", {})
    feats.setdefault("support", {}).update({
        "create_ticket": lambda user_id, subject, message, attachments=None: _create_ticket(shop_state, user_id, subject, message, attachments),
        "add_reply":    lambda ticket_id, actor, message, attachments=None, private=False: _add_reply(shop_state, ticket_id, actor, message, attachments, private),
        "close":        lambda ticket_id, actor: _close(shop_state, ticket_id, actor),
        "get":          lambda ticket_id: _get(shop_state, ticket_id),
        "list_user":    lambda user_id: _list_user(shop_state, user_id),
        "queue":        lambda: _queue_view(shop_state),
        "set_sla":      lambda hours: _set_sla(shop_state, hours),
        "set_canned":   lambda key, text: _set_canned(shop_state, key, text),
        "get_canned":   lambda key: _get_canned(shop_state, key),
        "suggest_canned": lambda text: _suggest_canned(shop_state, text),
        "stats":        lambda: _stats(shop_state),
    })

    # Reply-menu hook (FEATURE_MAP → "💬 support" -> "support")
    api = shop_state.setdefault("api", {})
    def _entry(bot2, m):
        uid = m.from_user.id
        st = _stats(shop_state)
        my = _list_user(shop_state, uid)
        # պարզ intro + user tickets snapshot
        lines = [
            "💬 Support / Helpdesk",
            f"Սպասարկման SLA՝ {st['sla_hours']} ժ.",
            f"Բաց հերթ՝ {st['open_queue']} դիմում",
            "",
            "📩 Գրիր թեստ հաղորդագրություն՝ «Ստեղծել դիմում: <քո խնդիրը>»",
            "Օր.` Ստեղծել դիմում: Բուքլետը չի բացվում սմարթֆոնում",
        ]
        if my:
            lines.append("\n👤 Քո վերջին դիմումները (մինչև 5-ը).")
            for rec in my[-5:]:
                lines.append(f" • #{rec['id']} — {rec['subject']} [{rec['status']}]")
        bot2.send_message(m.chat.id, "\n".join(lines), parse_mode=None)

    api["support"] = _entry




