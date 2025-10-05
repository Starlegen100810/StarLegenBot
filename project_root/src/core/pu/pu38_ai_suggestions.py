# PU38 – AI Suggestions (cross-sell / up-sell helpers)
# Այստեղ placeholder logic է․ իրական AI ինտեգրացիան կավելացվի հետո։

from typing import Dict, Any, List

def init(bot, resolve_lang, catalog, shop_state: Dict[str, Any]):
    """
    API:
      suggest(product_id, limit=3) -> List[str] product_ids
    """
    sugg = shop_state.setdefault("ai_suggestions", {})

    def suggest(product_id: str, limit: int = 3) -> List[str]:
        # Placeholder – վերադարձնում է նույն կատեգորիայի այլ ապրանքներ
        cat = None
        for cslug, prods in catalog.get("products_by_cat", {}).items():
            if product_id in prods:
                cat = cslug
                break
        if not cat:
            return []
        all_ids = list(catalog["products_by_cat"][cat])
        return [pid for pid in all_ids if pid != product_id][:limit]

    sugg["suggest"] = suggest


def init(bot, ctx):
    def feature(bot, m):
        bot.send_message(m.chat.id, "✅ pu38_ai_suggestions աշխատեց")
    ctx["shop_state"].setdefault("api", {})["ai_suggestions"] = feature




