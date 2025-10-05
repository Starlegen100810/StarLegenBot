# src/core/pu/pu20_notifications.py
from __future__ import annotations
import time
from typing import Dict, Any

def register(bot, ctx):
    shop_state = ctx["shop_state"]
    api = shop_state.setdefault("api", {})

    # -------- user notify helpers (կարող ես օգտագործել այլ PU-երից) --------
    def notify(uid: int, chat_id: int, text: str):
        try:
            bot.send_message(chat_id, text, parse_mode=None, disable_web_page_preview=True)
        except Exception:
            pass

    def notify_abandoned_cart(uid: int, chat_id: int):
        notify(uid, chat_id, "⏰ Ձեր զամբյուղը սպասում է ձեզ 🛍️")

    def notify_payment_reminder(uid: int, chat_id: int):
        notify(uid, chat_id, "💳 Մոռացե՞լ եք ավարտել վճարումը։ Կարող եք վերադառնալ և ավարտել հիմա։")

    # -------- Proof inbox storage + admin viewer --------
    proofs = shop_state.setdefault("proofs", [])  # list[dict]

    def log_proof(uid: int, method: str, meta: Dict[str, Any] | None = None):
        proofs.append({
            "uid": uid,
            "method": method or "unknown",
            "meta": meta or {},
            "ts": int(time.time()),
        })

    def admin_proofs_open(chat_id: int, limit: int = 20):
        if not proofs:
            bot.send_message(chat_id, "📷 Proof inbox՝ դատարկ է։", parse_mode=None)
            return
        last = proofs[-limit:]
        lines = ["📷 Վճարման ապացույցների ինբոքս (վերջինները):", ""]
        for i, p in enumerate(reversed(last), 1):
            ts = time.strftime("%Y-%m-%d %H:%M", time.localtime(p.get("ts", 0)))
            lines.append(f"{i:>2}. user:{p['uid']}  •  pay:{p['method']}  •  {ts}")
        bot.send_message(chat_id, "\n".join(lines), parse_mode=None, disable_web_page_preview=True)

    api.update({
        "notify": notify,
        "notify_abandoned_cart": notify_abandoned_cart,
        "notify_payment_reminder": notify_payment_reminder,
        "log_proof": log_proof,
        "admin_proofs_open": admin_proofs_open,
    })
