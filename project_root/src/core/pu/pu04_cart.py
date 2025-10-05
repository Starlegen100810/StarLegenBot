# PU04 – Cart (core state & math)
from typing import Dict, Any, List

def _emit(bot, shop_state: Dict[str, Any], event: str, payload: Dict[str, Any]):
    try:
        emit = getattr(bot, "emit", None)
        if callable(emit):
            emit(event, payload)
            return
    except Exception:
        pass
    shop_state.setdefault("__events__", []).append({"event": event, "payload": payload})

def _user_cart(shop_state: Dict[str, Any], user_id: int) -> Dict[str, Any]:
    carts = shop_state.setdefault("cart", {})
    return carts.setdefault(user_id, {"items": []})  # items: [{sku, qty}]

def _find_item(items: List[Dict[str, Any]], sku: str):
    for it in items:
        if it.get("sku") == sku:
            return it
    return None

def add_item(shop_state: Dict[str, Any], user_id: int, sku: str, qty: int = 1):
    cart = _user_cart(shop_state, user_id)
    items = cart["items"]
    exist = _find_item(items, sku)
    if exist:
        exist["qty"] = max(1, int(exist.get("qty", 1)) + int(qty))
    else:
        items.append({"sku": sku, "qty": max(1, int(qty))})
    cart["items"] = [i for i in items if i["qty"] > 0]

def set_qty(shop_state: Dict[str, Any], user_id: int, sku: str, qty: int):
    cart = _user_cart(shop_state, user_id)
    items = cart["items"]
    exist = _find_item(items, sku)
    if exist:
        exist["qty"] = max(0, int(qty))
    cart["items"] = [i for i in items if i["qty"] > 0]

def remove_item(shop_state: Dict[str, Any], user_id: int, sku: str):
    cart = _user_cart(shop_state, user_id)
    cart["items"] = [i for i in cart["items"] if i.get("sku") != sku]

def clear_cart(shop_state: Dict[str, Any], user_id: int):
    _user_cart(shop_state, user_id)["items"] = []

def breakdown(resolve_lang, catalog, shop_state: Dict[str, Any], user_id: int) -> Dict[str, Any]:
    """Return:
      items: [{sku, name, price, qty, total, thumb}]
      subtotal, discount, final_total
    """
    lang = resolve_lang(user_id)
    items_out: List[Dict[str, Any]] = []
    subtotal = 0.0

    cart = _user_cart(shop_state, user_id)
    for row in cart["items"]:
        sku = row["sku"]
        qty = int(row.get("qty", 1))

        prod = None
        # փորձել get_product
        getp = getattr(catalog, "get_product", None)
        if callable(getp):
            try:
                prod = getp(sku, lang)
            except Exception:
                prod = None
        # fallback՝ product_data
        if not prod:
            gpd = getattr(catalog, "product_data", None)
            if callable(gpd):
                try:
                    prod = gpd(sku, lang)
                except Exception:
                    prod = None

        prod = prod or {"name": sku, "price": 0, "thumb": None}

        price = float(prod.get("price", 0))
        total = price * qty
        subtotal += total
        items_out.append({
            "sku": sku,
            "name": prod.get("name", sku),
            "price": price,
            "qty": qty,
            "total": total,
            "thumb": prod.get("thumb"),
        })

    cart_meta = _user_cart(shop_state, user_id)
    discount = float(cart_meta.get("applied_discount", 0.0))
    final_total = max(0.0, subtotal - discount)

    return {
        "items": items_out,
        "subtotal": round(subtotal, 2),
        "discount": round(discount, 2),
        "final_total": round(final_total, 2),
    }

def _register_api(shop_state):
    api = shop_state.setdefault("api", {})
    cart_api = api.setdefault("cart", {})
    cart_api.update({
        "add": add_item,
        "set_qty": set_qty,
        "remove": remove_item,
        "clear": clear_cart,
        "breakdown": breakdown,
    })

def register(bot, ctx):
    """Called by PU manager; exposes only the API."""
    shop_state = ctx["shop_state"]
    _register_api(shop_state)

    on = getattr(bot, "on", None)
    if callable(on):
        @on("cart:add")
        def _h_add(ctx2):
            uid = ctx2["user_id"]; sku = ctx2["sku"]; qty = int(ctx2.get("qty", 1))
            add_item(shop_state, uid, sku, qty)
            _emit(bot, shop_state, "cart:changed", {"user_id": uid})

        @on("cart:clear")
        def _h_clear(ctx2):
            uid = ctx2["user_id"]
            clear_cart(shop_state, uid)
            _emit(bot, shop_state, "cart:changed", {"user_id": uid})
