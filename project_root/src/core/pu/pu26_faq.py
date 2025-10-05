# PU26 — FAQ / Knowledge Base (multi-language + helpful votes)

from collections import defaultdict
from datetime import datetime
import re

def _now_iso():
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def _ensure(shop_state):
    shop_state.setdefault("faq", {
        "entries": {},          # id -> {q, a, lang, tags[], created_at, updated_at, votes:{up,down}}
        "by_lang": defaultdict(set),  # lang -> set(ids)
        "next_id": 1
    })

def init(bot, resolve_lang, catalog, shop_state):
    """
    features['faq'] API
      - add(q, a, lang="hy", tags=None) -> id
      - edit(id, **fields) -> bool
      - delete(id) -> bool
      - get(id) -> dict|None
      - search(query, lang=None, limit=10) -> list[dict]
      - vote(id, up=True) -> dict
      - top(lang=None, limit=10) -> list[dict]
      - import_list(list_of_dicts) / export_list() -> list
    """
    _ensure(shop_state)
    feats = shop_state.setdefault("features", {})
    api = feats.setdefault("faq", {})

    def add(q, a, lang="hy", tags=None):
        st = shop_state["faq"]
        fid = st["next_id"]
        st["next_id"] += 1
        rec = {
            "id": fid,
            "q": str(q or "").strip(),
            "a": str(a or "").strip(),
            "lang": str(lang or "hy"),
            "tags": [str(t) for t in (tags or [])][:10],
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
            "votes": {"up": 0, "down": 0}
        }
        st["entries"][fid] = rec
        st["by_lang"][rec["lang"]].add(fid)
        return fid

    def edit(fid, **fields):
        rec = shop_state["faq"]["entries"].get(int(fid))
        if not rec:
            return False
        for k in ("q", "a", "lang", "tags"):
            if k in fields and fields[k] is not None:
                rec[k] = fields[k] if k != "tags" else [str(t) for t in fields["tags"]][:10]
        rec["updated_at"] = _now_iso()
        return True

    def delete(fid):
        fid = int(fid)
        st = shop_state["faq"]
        rec = st["entries"].pop(fid, None)
        if not rec:
            return False
        try:
            st["by_lang"][rec["lang"]].discard(fid)
        except Exception:
            pass
        return True

    def get(fid):
        return shop_state["faq"]["entries"].get(int(fid))

    def _match_score(rec, q):
        text = f"{rec['q']} {rec['a']} {' '.join(rec.get('tags', []))}".lower()
        score = 0
        for w in re.findall(r"\w+", q.lower()):
            if w in text:
                score += 1
        return score

    def search(query, lang=None, limit=10):
        q = (query or "").strip()
        if not q:
            return []
        st = shop_state["faq"]
        ids = st["by_lang"].get(lang, st["entries"].keys()) if lang else st["entries"].keys()
        scored = []
        for fid in ids:
            rec = st["entries"][fid]
            s = _match_score(rec, q)
            if s > 0:
                scored.append((s, rec))
        scored.sort(key=lambda x: (-x[0], -(x[1]["votes"]["up"] - x[1]["votes"]["down"])))
        return [r for _, r in scored[: int(limit)]]

    def vote(fid, up=True):
        rec = shop_state["faq"]["entries"].get(int(fid))
        if not rec:
            return {}
        if up:
            rec["votes"]["up"] += 1
        else:
            rec["votes"]["down"] += 1
        rec["updated_at"] = _now_iso()
        return dict(rec["votes"])

    def top(lang=None, limit=10):
        st = shop_state["faq"]
        ids = st["by_lang"].get(lang, st["entries"].keys()) if lang else st["entries"].keys()
        arr = [st["entries"][i] for i in ids]
        arr.sort(key=lambda r: (r["votes"]["up"] - r["votes"]["down"], r["votes"]["up"]), reverse=True)
        return arr[: int(limit)]

    def import_list(items):
        count = 0
        for it in (items or []):
            if "q" in it and "a" in it:
                add(it["q"], it["a"], it.get("lang", "hy"), it.get("tags"))
                count += 1
        return count

    def export_list():
        return list(shop_state["faq"]["entries"].values())

    api.update({
        "add": add,
        "edit": edit,
        "delete": delete,
        "get": get,
        "search": search,
        "vote": vote,
        "top": top,
        "import_list": import_list,
        "export_list": export_list,
    })


def init(bot, ctx):
    def feature(bot, m):
        bot.send_message(m.chat.id, "✅ pu26_faq աշխատեց")
    ctx["shop_state"].setdefault("api", {})["faq"] = feature




