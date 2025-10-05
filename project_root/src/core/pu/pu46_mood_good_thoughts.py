# PU46 – Mood / Good Thoughts (positive quotes with categories + likes)

from typing import Dict, Any, List, Optional
import time
import random

DEFAULTS = {
    "spiritual": [
        "Խաղաղ սիրտը լավագույն ուղեկիցն է։",
        "Շնչիր խորը. ամեն ինչ կարգին է լինելու։",
    ],
    "business": [
        "Փոքր կայուն քայլերը մեծ հաղթանակի ճանապարհն են։",
        "Արժեք ստեղծելն է միշտ հաղթում զեղչերին։",
    ],
    "humor": [
        "Սուրճից հետո ես upgrade եմ 😀",
        "Բարի ժպիտը լավագույն filter-ն է։",
    ],
}

def init(bot, resolve_lang, catalog, shop_state: Dict[str, Any]):
    """
    API:
      add_thought(cat, text, lang='hy') -> id
      random_thought(lang='hy', cat=None) -> dict
      like(id, user_id)
      top(cat=None, limit=10) -> List[dict]
    """
    gm = shop_state.setdefault("mood_good_thoughts", {})
    store: List[Dict[str, Any]] = gm.setdefault("_items", [])
    likes = gm.setdefault("_likes", {})  # id -> set(user_ids)
    seq = gm.setdefault("_seq", 1)

    # seed once
    if not store:
        for cat, arr in DEFAULTS.items():
            for t in arr:
                _add = {"cat": cat, "text": t, "lang": "hy"}

                # emulate local add
                _add["id"] = seq
                seq += 1
                _add["ts"] = time.time()
                store.append(_add)
                likes[_add["id"]] = set()

    def add_thought(cat: str, text: str, lang: str = "hy") -> int:
        nonlocal seq
        cat = (cat or "general").lower()
        entry = {"id": seq, "cat": cat, "text": text.strip(), "lang": lang, "ts": time.time()}
        store.append(entry)
        likes[seq] = set()
        seq += 1
        return entry["id"]

    def random_thought(lang: str = "hy", cat: Optional[str] = None) -> Dict[str, Any]:
        pool = [e for e in store if (not cat or e["cat"] == cat) and (e["lang"] == lang)]
        if not pool:
            pool = store[:]  # fallback any
        e = random.choice(pool)
        return {**e, "likes": len(likes.get(e["id"], set()))}

    def like(tid: int, user_id: int):
        likes.setdefault(tid, set()).add(user_id)

    def top(cat: Optional[str] = None, limit: int = 10):
        items = store if not cat else [e for e in store if e["cat"] == cat]
        items = sorted(items, key=lambda e: len(likes.get(e["id"], set())), reverse=True)
        out = []
        for e in items[:limit]:
            out.append({**e, "likes": len(likes.get(e["id"], set()))})
        return out

    gm["add_thought"] = add_thought
    gm["random_thought"] = random_thought
    gm["like"] = like
    gm["top"] = top


def init(bot, ctx):
    def feature(bot, m):
        bot.send_message(m.chat.id, "✅ pu46_mood_good_thoughts աշխատեց")
    ctx["shop_state"].setdefault("api", {})["mood_good_thoughts"] = feature




