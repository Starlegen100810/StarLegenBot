# PU40 – Gamification Levels (Bronze → Platinum)
# User points -> level mapping + API

from typing import Dict, Any

LEVELS = [
    (0, "Bronze"),
    (100, "Silver"),
    (500, "Gold"),
    (1500, "Platinum"),
]

def level_for_points(points: int) -> str:
    lvl = "Bronze"
    for threshold, name in LEVELS:
        if points >= threshold:
            lvl = name
        else:
            break
    return lvl

def init(bot, resolve_lang, catalog, shop_state: Dict[str, Any]):
    """
    API:
      add_points(user_id, pts)
      get_points(user_id) -> int
      get_level(user_id) -> str
      leaderboard(top_n=10) -> List[(user_id, pts, level)]
    """
    gam = shop_state.setdefault("levels", {})
    store = gam.setdefault("_users", {})  # {user_id: points}

    def add_points(user_id: int, pts: int):
        store[user_id] = store.get(user_id, 0) + pts
        return store[user_id]

    def get_points(user_id: int) -> int:
        return store.get(user_id, 0)

    def get_level(user_id: int) -> str:
        return level_for_points(get_points(user_id))

    def leaderboard(top_n: int = 10):
        items = sorted(store.items(), key=lambda kv: kv[1], reverse=True)
        return [(uid, pts, level_for_points(pts)) for uid, pts in items[:top_n]]

    gam["add_points"] = add_points
    gam["get_points"] = get_points
    gam["get_level"] = get_level
    gam["leaderboard"] = leaderboard


def init(bot, ctx):
    def feature(bot, m):
        bot.send_message(m.chat.id, "✅ pu40_gamification_levels աշխատեց")
    ctx["shop_state"].setdefault("api", {})["gamification_levels"] = feature




