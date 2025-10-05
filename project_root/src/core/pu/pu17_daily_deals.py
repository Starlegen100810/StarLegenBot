# PU17 – Daily Deal (safe discount cap, countdown, 1 per user, bonus points, schedule)
from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

def _iso(): return datetime.utcnow().isoformat()
def _today(): return datetime.utcnow().date().isoformat()

def _db(shop_state):
    root = shop_state.setdefault("daily_deal", {})
    root.setdefault("config", {"max_safe_pct": 15, "bonus_pts": 150, "limit_per_user": 1})
    root.setdefault("today", {})
    root.setdefault("purchases", {})
    root.setdefault("schedule", [])
    return root

def set_today(shop_state, pid:int, pct:int, title:str="Daily Deal"):
    db=_db(shop_state)
    db["today"] = {"date": _today(), "pid": int(pid), "pct": min(int(pct), db["config"]["max_safe_pct"]), "title":title}
    return db["today"]

def get_today(shop_state)->Dict[str,Any]|None:
    db=_db(shop_state); t=db["today"]
    if not t or t.get("date")!=_today():
        for row in list(db["schedule"]):
            if row.get("date")==_today():
                return set_today(shop_state, row["pid"], row["pct"], row.get("title","Daily Deal"))
        return None
    return t

def schedule(shop_state, rows:List[Dict[str,Any]]):
    db=_db(shop_state); db["schedule"]=rows; return len(rows)

def eligible(shop_state, uid:int)->bool:
    db=_db(shop_state); limit=db["config"]["limit_per_user"]
    cnt=db["purchases"].setdefault(_today(), {}).get(int(uid), 0)
    return cnt < limit

def mark_purchase(shop_state, uid:int):
    db=_db(shop_state); day=db["purchases"].setdefault(_today(), {})
    day[int(uid)] = day.get(int(uid), 0) + 1
    return day[int(uid)]

def price_after(shop_state, price:int)->int:
    t=get_today(shop_state)
    if not t: return price
    return max(0, price - (price*int(t["pct"])//100))

def countdown()->Dict[str,int]:
    now=datetime.utcnow()
    end=datetime.combine(now.date()+timedelta(days=1), datetime.min.time())
    left=end-now
    return {"hours": left.seconds//3600, "minutes": (left.seconds%3600)//60}

def init(bot, resolve_lang, catalog, shop_state):
    api=shop_state.setdefault("api", {}).setdefault("daily_deal", {})
    api.update({
        "get_today": lambda: get_today(shop_state),
        "eligible": lambda uid: eligible(shop_state, uid),
        "mark_purchase": lambda uid: mark_purchase(shop_state, uid),
        "price_after": lambda price: price_after(shop_state, price),
        "schedule": lambda rows: schedule(shop_state, rows),
        "set_today": lambda pid,pct,title="Daily Deal": set_today(shop_state, pid,pct,title),
        "countdown": countdown,
        "config": lambda: _db(shop_state)["config"],
    })


def init(bot, ctx):
    def feature(bot, m):
        bot.send_message(m.chat.id, "✅ pu17_daily_deals աշխատեց")
    ctx["shop_state"].setdefault("api", {})["daily_deals"] = feature




