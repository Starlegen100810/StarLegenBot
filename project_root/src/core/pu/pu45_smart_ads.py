# PU45 – Smart Ads (sponsored slots, simple targeting)

from typing import Dict, Any, List, Optional
import time
import itertools

def init(bot, resolve_lang, catalog, shop_state: Dict[str, Any]):
    """
    API:
      add_ad(ad:dict) -> id
        # ad = {title, product_id?, image?, url?, lang?, tags?, weight?, expires?}
      get_ads(ctx:dict=None, max_n=3) -> List[dict]
      click(ad_id) -> None
      stats(ad_id) -> dict
    """
    adsmod = shop_state.setdefault("smart_ads", {})
    ads: List[Dict[str, Any]] = adsmod.setdefault("_ads", [])
    seq = adsmod.setdefault("_seq", 1)

    metrics = adsmod.setdefault("_metrics", {})  # ad_id -> {impr, clicks}

    def add_ad(ad: Dict[str, Any]) -> int:
        nonlocal seq
        item = ad.copy()
        item["id"] = seq
        item.setdefault("weight", 1)
        item.setdefault("tags", [])
        item.setdefault("lang", None)
        item.setdefault("expires", None)  # ts
        item["created"] = time.time()
        ads.append(item)
        metrics[item["id"]] = {"impr": 0, "clicks": 0}
        seq += 1
        return item["id"]

    def _eligible(a: Dict[str, Any], ctx: Optional[Dict[str, Any]]):
        if a.get("expires") and a["expires"] < time.time():
            return False
        if ctx and ctx.get("lang") and a.get("lang") and a["lang"] != ctx["lang"]:
            return False
        if ctx and ctx.get("tag"):
            want = ctx["tag"]
            if a.get("tags") and want not in a["tags"]:
                return False
        return True

    def get_ads(ctx: Optional[Dict[str, Any]] = None, max_n: int = 3) -> List[Dict[str, Any]]:
        pool = [a for a in ads if _eligible(a, ctx)]
        # simple weight-based expansion
        expanded = list(itertools.chain.from_iterable([[a]*max(1,int(a.get("weight",1))) for a in pool]))
        expanded.sort(key=lambda x: x.get("created", 0), reverse=True)
        result = []
        for a in expanded:
            if len(result) >= max_n: break
            if a not in result:
                result.append(a)
        for a in result:
            metrics[a["id"]]["impr"] += 1
        return [a.copy() for a in result]

    def click(ad_id: int):
        if ad_id in metrics:
            metrics[ad_id]["clicks"] += 1

    def stats(ad_id: int):
        return metrics.get(ad_id, {"impr": 0, "clicks": 0})

    adsmod["add_ad"] = add_ad
    adsmod["get_ads"] = get_ads
    adsmod["click"] = click
    adsmod["stats"] = stats


def init(bot, ctx):
    def feature(bot, m):
        bot.send_message(m.chat.id, "✅ pu45_smart_ads աշխատեց")
    ctx["shop_state"].setdefault("api", {})["smart_ads"] = feature




