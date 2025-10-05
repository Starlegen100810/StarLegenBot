# PU14 – Feedback / Reviews (CRUD, moderation, gallery, verified buyer)
from __future__ import annotations
from typing import Dict, Any, List
from datetime import datetime

def _iso(): return datetime.utcnow().isoformat()

def _db(shop_state):
    root = shop_state.setdefault("reviews", {})
    root.setdefault("items", {})     # id -> review
    root.setdefault("by_product", {})# product_id -> [ids]
    root.setdefault("seq", 1)
    return root

def _new_id(db): 
    rid = db["seq"]; db["seq"] += 1; return rid

def _index_product(db, pid, rid):
    db["by_product"].setdefault(int(pid), []).append(rid)

def add_review(shop_state, uid:int, product_id:int, rating:int, text:str, media:List[str]|None=None, verified=False):
    db = _db(shop_state)
    rid = _new_id(db)
    item = {
        "id": rid, "uid": uid, "product_id": int(product_id),
        "rating": max(1, min(5, int(rating))), "text": text.strip(),
        "media": media or [], "verified": bool(verified),
        "status": "pending",  # pending|approved|rejected
        "created_at": _iso(), "updated_at": _iso(),
        "admin_note": ""
    }
    db["items"][rid] = item
    _index_product(db, product_id, rid)
    return item

def set_status(shop_state, rid:int, status:str, note:str=""):
    db=_db(shop_state); it=db["items"].get(int(rid))
    if not it: return None
    it["status"]=status; it["admin_note"]=note; it["updated_at"]=_iso()
    return it

def edit_review(shop_state, rid:int, new_text:str=None, new_rating:int|None=None):
    db=_db(shop_state); it=db["items"].get(int(rid))
    if not it: return None
    if new_text is not None: it["text"]=new_text.strip()
    if new_rating is not None: it["rating"]=max(1,min(5,int(new_rating)))
    it["updated_at"]=_iso()
    return it

def product_reviews(shop_state, pid:int, only_approved=True)->List[Dict[str,Any]]:
    db=_db(shop_state)
    ids = db["by_product"].get(int(pid), [])
    out=[db["items"][i] for i in ids if i in db["items"]]
    if only_approved: out=[r for r in out if r["status"]=="approved"]
    return out

def sentiment_summary(rows:List[Dict[str,Any]])->Dict[str,Any]:
    if not rows: return {"count":0,"avg":0,"pos_pct":0,"neg_pct":0}
    cnt=len(rows); avg=sum(r["rating"] for r in rows)/cnt
    pos=sum(1 for r in rows if r["rating"]>=4)*100//cnt
    neg=sum(1 for r in rows if r["rating"]<=2)*100//cnt
    return {"count":cnt,"avg":round(avg,2),"pos_pct":pos,"neg_pct":neg}

def _register_api(shop_state):
    api = shop_state.setdefault("api", {})
    api.setdefault("reviews", {}).update({
        "add": add_review,
        "approve": lambda rid, note="": set_status(shop_state, rid, "approved", note),
        "reject":  lambda rid, note="": set_status(shop_state, rid, "rejected", note),
        "edit": edit_review,
        "list_for": product_reviews,
        "sentiment": sentiment_summary,
    })

def init(bot, resolve_lang, catalog, shop_state):
    """
    PU14 Feedback:
    - User: /review <product_id> <rating 1-5> <text...>  → pending
            /gallery <product_id> → show approved reviews summary
    - Verified buyer: event:order:delivered marks matching reviews as verified
    - Admin: /reviews [pending|all] ; /rv_approve <id> ; /rv_reject <id> [reason] ; /rv_edit <id> <new text>
    """
    _register_api(shop_state)
    on = getattr(bot, "on", None)
    if not callable(on): return

    # User – create review
    @on("cmd:/review")
    def _make(ctx):
        uid = ctx["user_id"]
        parts = (ctx.get("text") or "").split(maxsplit=3)
        if len(parts) < 4:
            bot.send(uid, "Օգտ․ /review <PRODUCT_ID> <RATING 1-5> <TEXT>")
            return
        _, pid, rating, text = parts
        rv = add_review(shop_state, uid, int(pid), int(rating), text)
        bot.send(uid, f"🙏 Շնորհակալություն։ Քո կարծիքը #{rv['id']} սպասում է հաստատման։")

    # User – gallery / summary
    @on("cmd:/gallery")
    def _gal(ctx):
        uid = ctx["user_id"]
        parts = (ctx.get("text") or "").split()
        if len(parts) < 2:
            bot.send(uid, "Օգտ․ /gallery <PRODUCT_ID>")
            return
        pid = int(parts[1])
        rows = product_reviews(shop_state, pid, only_approved=True)
        sumr = sentiment_summary(rows)
        head = f"🗂 Կարծիքներ՝ {sumr['count']} հատ | ⭐ {sumr['avg']} | ✅{sumr['pos_pct']}% / ❌{sumr['neg_pct']}%"
        preview = []
        for r in rows[:5]:
            mark = "✅" if r["verified"] else "•"
            preview.append(f"{mark} ⭐{r['rating']} — {r['text'][:80]}")
        bot.send(uid, head + ("\n" + "\n".join(preview) if preview else ""))

    # Admin – list / approve / reject / edit
    @on("cmd:/reviews")
    def _list(ctx):
        uid = ctx["user_id"]
        flt = (ctx.get("text") or "").split()[1:] or ["pending"]
        want = flt[0]
        db = _db(shop_state)
        items = list(db["items"].values())
        if want=="pending": items=[i for i in items if i["status"]=="pending"]
        items = sorted(items, key=lambda x: x["created_at"], reverse=True)[:15]
        if not items:
            bot.send(uid, "Չկան համապատասխան կարծիքներ։")
            return
        lines=[f"#{i['id']} pid={i['product_id']} ⭐{i['rating']} [{i['status']}] {'VER' if i['verified'] else ''} — {i['text'][:60]}" for i in items]
        bot.send(uid, "Վերջին կարծիքներ:\n"+"\n".join(lines))

    @on("cmd:/rv_approve")
    def _ap(ctx):
        parts=(ctx.get("text") or "").split()
        if len(parts)<2: 
            bot.send(ctx["user_id"], "Օգտ․ /rv_approve <ID>")
            return
        it=set_status(shop_state, int(parts[1]), "approved")
        bot.send(ctx["user_id"], f"OK Approved #{it['id']}") if it else bot.send(ctx["user_id"], "Չգտնվեց։")

    @on("cmd:/rv_reject")
    def _rej(ctx):
        parts=(ctx.get("text") or "").split(maxsplit=2)
        if len(parts)<2: 
            bot.send(ctx["user_id"], "Օգտ․ /rv_reject <ID> [REASON]")
            return
        note=parts[2] if len(parts)>2 else ""
        it=set_status(shop_state, int(parts[1]), "rejected", note)
        bot.send(ctx["user_id"], f"Rejected #{it['id']} ({note})") if it else bot.send(ctx["user_id"], "Չգտնվեց։")

    @on("cmd:/rv_edit")
    def _ed(ctx):
        parts=(ctx.get("text") or "").split(maxsplit=2)
        if len(parts)<3:
            bot.send(ctx["user_id"], "Օգտ․ /rv_edit <ID> <NEW_TEXT>")
            return
        it=edit_review(shop_state, int(parts[1]), new_text=parts[2])
        bot.send(ctx["user_id"], f"Edited #{it['id']}") if it else bot.send(ctx["user_id"], "Չգտնվեց।")

    # Hook – verify buyer on delivery
    @on("event:order:delivered")
    def _verify(ctx):
        uid=ctx["user_id"]; prods = ctx.get("product_ids", [])
        if not prods: return
        db=_db(shop_state)
        for pid in prods:
            for rid in db["by_product"].get(int(pid), []):
                r=db["items"].get(rid)
                if r and r["uid"]==uid:
                    r["verified"]=True; r["updated_at"]=_iso()




