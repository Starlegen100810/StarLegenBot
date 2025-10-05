# PU36 – Video-first slider ordering helper
# Մեզ պետք է մեդիա ցուցակը վերադասավորել՝ video → images, առանց UI intrusive փոփոխության։

from typing import Dict, Any, List

VIDEO_EXTS = {".mp4", ".mov", ".webm", ".m4v"}

def _is_video(item: Any) -> bool:
    # Աջակցում է երկու ձևի տվյալների.
    # 1) dict with "type": "video"/"image"
    # 2) string/url filename -> ըստ ընդլայնման
    if isinstance(item, dict):
        t = str(item.get("type", "")).lower()
        if t in ("video", "mp4", "webm"):
            return True
        src = str(item.get("src") or item.get("url") or "")
    else:
        src = str(item)
    src_lower = src.lower()
    for ext in VIDEO_EXTS:
        if src_lower.endswith(ext):
            return True
    return False

def order_media(media: List[Any]) -> List[Any]:
    vids = [m for m in media if _is_video(m)]
    imgs = [m for m in media if not _is_video(m)]
    return vids + imgs

def init(bot, resolve_lang, catalog, shop_state: Dict[str, Any]):
    """
    API:
      order_for_slider(product_or_media) -> List[Any]
      enabled_for(category_slug) -> bool
    Config:
      config["video_first"] = {"enabled": True, "categories": ["rugs","auto"]}
    """
    config  = shop_state.setdefault("config", {})
    media_s = shop_state.setdefault("media", {})
    features = shop_state.setdefault("features", {})
    features.setdefault("video_first_slider", True)

    vf = config.setdefault("video_first", {})
    vf.setdefault("enabled", True)
    # Ցանկ이면 սահմանես՝ կոնկրետ կատեգորիաներում ակտիվ:
    vf.setdefault("categories", [])  # դատարկ՝ նշանակում է՝ բոլոր կատեգորիաների համար

    def enabled_for(category_slug: str = None) -> bool:
        if not (features.get("video_first_slider", True) and vf.get("enabled", True)):
            return False
        cats = vf.get("categories") or []
        if not cats:
            return True
        return (category_slug or "") in cats

    def order_for_slider(product_or_media: Any, category_slug: str = None) -> List[Any]:
        # ընդունում է կամ product dict {"media":[...]} կամ ուղղակի media list
        media_list: List[Any]
        if isinstance(product_or_media, dict):
            media_list = list(product_or_media.get("media") or [])
        else:
            media_list = list(product_or_media or [])
        if not enabled_for(category_slug):
            return media_list
        return order_media(media_list)

    media_s["order_for_slider"] = order_for_slider
    media_s["enabled_for"] = enabled_for


def init(bot, ctx):
    def feature(bot, m):
        bot.send_message(m.chat.id, "✅ pu36_video_first_slider աշխատեց")
    ctx["shop_state"].setdefault("api", {})["video_first_slider"] = feature



