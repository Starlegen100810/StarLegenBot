# src/core/pu/pu48_payments_mock.py
# -*- coding: utf-8 -*-
# PU48 — Payments Mock (IDram/Telcell/Card/Alipay/USDT/Cash placeholders)

from datetime import datetime

SUPPORTED = ("idram", "telcell", "card", "alipay", "usdt", "cash")

def _now_iso():
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def _ensure_structs(shop_state):
    shop_state.setdefault("payments", {})   # order_id -> payment dict
    shop_state.setdefault("features", {}).setdefault("orders", {})  # dependency

def init(bot, resolve_lang, catalog, shop_state):
    """
    Ավելացնում է shop_state['features']['payments'] API․
      - init_payment(order_id, method) -> payment_request
      - confirm_payment(order_id, proof_text_or_url) -> payment
      - get(order_id) -> payment|None
    """
    _ensure_structs(shop_state)
    features = shop_state.setdefault("features", {})
    payments_api = features.setdefault("payments", {})
    orders_api = features.get("orders", {})

    def init_payment(order_id, method):
        method = (method or "").lower()
        if method not in SUPPORTED:
            raise ValueError(f"Unsupported method: {method}")
        order = orders_api.get(order_id) if callable(orders_api.get) else None
        if not order:
            # fallback՝ orders_api.get(order_id) չէ, ուղղակի թեստային հոսք
            order_obj = shop_state.get("orders", {}).get(order_id)
        else:
            order_obj = order(order_id)  # call the function

        if not order_obj:
            raise ValueError("Order not found")

        req = {
            "order_id": order_id,
            "method": method,
            "amount": order_obj["total"],
            "currency": order_obj["currency"],
            "status": "pending_proof",  # սպասում է user-ի ապացույցին
            "details": _payment_details_placeholder(method),
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
            "proofs": [],  # user/admin attached texts/urls
        }
        shop_state["payments"][order_id] = req

        # պատվերը տանում ենք pending_payment վիճակ
        if isinstance(orders_api, dict) and orders_api.get("set_status"):
            orders_api["set_status"](order_id, "pending_payment", note=f"init {method}")
        return req

    def confirm_payment(order_id, proof_text_or_url):
        pay = shop_state["payments"].get(order_id)
        if not pay:
            return None
        pay["proofs"].append({"ts": _now_iso(), "by": "user", "data": str(proof_text_or_url or "")})
        pay["status"] = "awaiting_admin_confirm"
        pay["updated_at"] = _now_iso()
        return pay

    def get(order_id):
        return shop_state["payments"].get(order_id)

    payments_api.update({
        "init_payment": init_payment,
        "confirm_payment": confirm_payment,
        "get": get,
    })

def _payment_details_placeholder(method):
    if method == "idram":
        return {"type": "wallet", "account": "IDram: 123456", "hint": "Transfer and send check."}
    if method == "telcell":
        return {"type": "terminal", "account": "Telcell: 987654", "hint": "Attach receipt photo."}
    if method == "card":
        return {"type": "card", "masked": "**** **** **** 1122", "hint": "Use QR or bank app."}
    if method == "alipay":
        return {"type": "wallet", "qr": "ALIPAY_QR_PLACEHOLDER", "hint": "Scan QR in Alipay."}
    if method == "usdt":
        return {"type": "crypto", "network": "TRC20", "address": "TXYZ...MOCK", "hint": "Send exact amount."}
    if method == "cash":
        return {"type": "cod", "note": "Pay to courier", "hint": "Cash on delivery."}
    return {"type": "other"}

# ---------------- ADAPTER ----------------
def register(bot, ctx):
    """
    Adapter՝ որ քո mock-ը միանա PU համակարգին առանց այլ կախվածությունների։
    """
    shop_state = ctx.setdefault("shop_state", {})
    user_lang = ctx.setdefault("user_lang", {})
    default_lang = (ctx.get("config", {}) or {}).get("DEFAULT_LANG", "hy")

    # resolve_lang fallback, եթե ctx-ում առանձին չի տրված
    def _resolve_lang(uid: int, default=default_lang):
        lang = user_lang.get(uid, default)
        return lang if lang else default

    # catalog այստեղ պարտադիր չէ mock-ի համար
    catalog = ctx.get("catalog")

    # init միացնենք քո mock API-ն
    init(bot, _resolve_lang, catalog, shop_state)
    print("[PU48] payments_mock attached")

def healthcheck(_):
    return True
