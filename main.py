import random
import os
import time
import textwrap
import threading
import datetime
from datetime import datetime as dt
import os, json, glob
import telebot
from telebot import types
import requests
from flask import Flask, request, abort
# ---- helpers: safe int casting (avoid .isdigit on non-strings) ----

def to_int(val):
    try:
        return int(str(val).strip())
    except Exception:
        return None


# --- Config / Bot ---
TOKEN = "7198636747:AAEUNsaiMZXweWcLZoQcxocZKKLhxapCszM"  # եթե արդեն վերևում ունես, սա պահիր նույնը
ADMIN_ID = 6822052289
admin_list = [ADMIN_ID]

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

# ---------------- Products loader ----------------
def load_products(folder="products"):
    """Կարդում է products/*.json–երը, վերադարձնում dict՝ {code: {...}}"""
    products = {}
    for path in glob.glob(os.path.join(folder, "*.json")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            code = str(item.get("code") or os.path.splitext(os.path.basename(path))[0])
            products[code] = {
                "code": code,
                "title": item.get("title", code),
                "price": int(item.get("price", 0)),
                "old_price": int(item.get("old_price", 0)),
                "description": item.get("description", ""),
                "photo": item.get("photo") or item.get("images", [None])[0],
                "sold": int(item.get("sold", 0)),
            }
    return products

# պահում ենք հիշողության մեջ
PRODUCTS = load_products()

# /reload — json-ներից նորից կարդալու համար
@bot.message_handler(commands=['reload'])
def reload_products(msg):
    global PRODUCTS, CATEGORIES
    PRODUCTS = load_products()
    # վերակառուցենք կատեգորիան (պարզ all-in-one, կարող ես խմբավորել հետո)
    CATEGORIES = {"Բոլոր ապրանքներ": list(PRODUCTS.keys())}
    bot.reply_to(msg, f"Ապրանքների ցանկը թարմացվեց ✅ ({len(PRODUCTS)} հատ)")

# ---------------- Utils ----------------
def kb_back(text="⬅️ Վերադառնալ հիմնական մենյու", data="back_main_menu"):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text, callback_data=data))
    return kb

def build_caption(p: dict) -> str:
    lines = [f"*{p.get('title', p['code'])}*"]
    if p.get("description"):
        lines.append(p["description"])
        lines.append("")
    old = int(p.get("old_price", 0)); new = int(p.get("price", 0))
    if old > 0:
        disc = f" (-{round((old-new)*100/old)}%)" if new and old>new else ""
        lines.append(f"❌ Հին գին — ~~{old}֏~~{disc}")
    lines.append(f"✅ Նոր գին — *{new}֏*")
    if p.get("sold"):
        lines.append(f"🔥 Վաճառված՝ *{p['sold']}+ հատ*")
    return "\n".join(lines)

def send_main_menu(chat_id: int):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🛍 Խանութ", "🛒 Զամբյուղ")
    kb.row("📦 Իմ պատվերները", "🎁 Կուպոններ")
    kb.row("🔍 Որոնել ապրանք", "🎡 Բոնուս անիվ")
    kb.row("👤 Իմ էջը", "🏆 Լավագույններ")
    kb.row("⚙️ Փոխարկումներ", "💬 Հետադարձ կապ")
    bot.send_message(chat_id, "Ընտրեք սեղմակ👇", reply_markup=kb)

# ---------------- Categories ----------------
CATEGORIES = {"Բոլոր ապրանքներ": list(PRODUCTS.keys())}

@bot.message_handler(func=lambda m: m.text and "խանութ" in m.text.lower())
def open_shop(message):
    if not PRODUCTS:
        bot.send_message(message.chat.id, "🙈 Ապրանքների ցանկը հիմա հասանելի չէ։")
        return
    kb = types.InlineKeyboardMarkup(row_width=2)
    for cat in CATEGORIES.keys():
        kb.add(types.InlineKeyboardButton(cat, callback_data=f"cat::{cat}"))
    kb.add(types.InlineKeyboardButton("⬅️ Վերադառնալ հիմնական մենյու", callback_data="back_main_menu"))
    bot.send_message(message.chat.id, "🛍 Ընտրեք բաժինը ⬇️", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("cat::"))
def open_category(c):
    _, cat = c.data.split("::", 1)
    codes = CATEGORIES.get(cat, [])
    kb = types.InlineKeyboardMarkup(row_width=1)
    for code in codes:
        title = PRODUCTS.get(code, {}).get("title", f"Ապրանք — {code}")
        kb.add(types.InlineKeyboardButton(title, callback_data=f"prod::{code}"))
    kb.add(types.InlineKeyboardButton("⬅️ Վերադառնալ խանութ", callback_data="back_shop"))
    try:
        bot.edit_message_text("Ընտրեք ապրանքը ⬇️", c.message.chat.id, c.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(c.message.chat.id, "Ընտրեք ապրանքը ⬇️", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data=="back_shop")
def back_shop(c):
    kb = types.InlineKeyboardMarkup(row_width=2)
    for cat in CATEGORIES.keys():
        kb.add(types.InlineKeyboardButton(cat, callback_data=f"cat::{cat}"))
    kb.add(types.InlineKeyboardButton("⬅️ Վերադառնալ հիմնական մենյու", callback_data="back_main_menu"))
    try:
        bot.edit_message_text("🛍 Ընտրեք բաժինը ⬇️", c.message.chat.id, c.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(c.message.chat.id, "🛍 Ընտրեք բաժինը ⬇️", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data=="back_main_menu")
def back_main_menu(c):
    send_main_menu(c.message.chat.id)

# ---------------- Product card ----------------
@bot.callback_query_handler(func=lambda c: c.data.startswith("prod::"))
def show_product(c):
    code = c.data.split("::",1)[1]
    p = PRODUCTS.get(code)
    if not p:
        bot.answer_callback_query(c.id, "Չգտնվեց 😕"); return
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("➕ Ավելացնել զամբյուղ", callback_data=f"add::{code}"))
    kb.add(types.InlineKeyboardButton("⬅️ Վերադառնալ խանութ", callback_data="back_shop"))
    try:
        with open(p["photo"], "rb") as ph:
            bot.send_photo(c.message.chat.id, ph, caption=build_caption(p), parse_mode="Markdown", reply_markup=kb)
    except Exception:
        bot.send_message(c.message.chat.id, build_caption(p), parse_mode="Markdown", reply_markup=kb)

# ---------------- Cart ----------------
user_cart = {}          # {user_id: [{"code": "...", "price": 1690, "qty": 1}]}
checkout_state = {}     # {user_id: {"step":1.., ...}}

def cart_subtotal_amd(user_id:int)->int:
    items = user_cart.get(user_id, [])
    return sum(i["price"]*i["qty"] for i in items)

@bot.callback_query_handler(func=lambda c: c.data.startswith("add::"))
def add_to_cart(c):
    user_id = c.from_user.id
    code = c.data.split("::",1)[1]
    p = PRODUCTS.get(code)
    if not p:
        bot.answer_callback_query(c.id, "Չգտնվեց"); return
    user_cart.setdefault(user_id, [])
    for it in user_cart[user_id]:
        if it["code"] == code:
            it["qty"] += 1
            break
    else:
        user_cart[user_id].append({"code": code, "price": int(p.get("price",0)), "qty": 1})
    bot.answer_callback_query(c.id, "Ավելացվեց ✅")

@bot.message_handler(func=lambda m: m.text and "զամբյուղ" in m.text.lower())
def show_cart(m):
    uid = m.from_user.id
    items = user_cart.get(uid, [])
    if not items:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("⬅️ Վերադառնալ խանութ", callback_data="back_shop"))
        bot.send_message(m.chat.id, "🧺 Զամբյուղը դատարկ է։", reply_markup=kb)
        return
    subtotal = cart_subtotal_amd(uid)
    lines = ["🧺 Ձեր զամբյուղը:\n"]
    for idx,i in enumerate(items,1):
        title = PRODUCTS[i["code"]]["title"]
        lines.append(f"{idx}. {title} — {i['price']}֏ × {i['qty']} = {i['price']*i['qty']}֏")
    lines.append(f"\n💵 Ընդհանուր՝ *{subtotal}֏*")
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✅ Պատվիրել", callback_data="checkout"))
    kb.add(types.InlineKeyboardButton("⬅️ Վերադառնալ խանութ", callback_data="back_shop"))
    first_photo = PRODUCTS[items[0]["code"]].get("photo")
    if first_photo:
        try:
            with open(first_photo,"rb") as ph:
                bot.send_photo(m.chat.id, ph, caption="\n".join(lines), parse_mode="Markdown", reply_markup=kb)
                return
        except: pass
    bot.send_message(m.chat.id, "\n".join(lines), parse_mode="Markdown", reply_markup=kb)

# --------- Checkout steps (name -> phone -> address -> receipt) ----------
@bot.callback_query_handler(func=lambda c: c.data=="checkout")
def start_checkout(c):
    uid = c.from_user.id
    subtotal = cart_subtotal_amd(uid)
    if subtotal<=0:
        bot.answer_callback_query(c.id, "Զամբյուղը դատարկ է"); return
    checkout_state[uid] = {"step": 1, "subtotal": subtotal}
    bot.send_message(c.message.chat.id, "👤 Գրեք ձեր ԱՆՈՒՆ/ԱԶԳԱՆՈՒՆ-ը:")

@bot.message_handler(func=lambda m: m.from_user.id in checkout_state and checkout_state[m.from_user.id]["step"]==1)
def take_name(m):
    st = checkout_state[m.from_user.id]; st["name"]=m.text; st["step"]=2
    bot.reply_to(m, "📞 Գրեք ՀԵՌԱԽՈՍԱՀԱՄԱՐ-ը:")

@bot.message_handler(func=lambda m: m.from_user.id in checkout_state and checkout_state[m.from_user.id]["step"]==2)
def take_phone(m):
    st = checkout_state[m.from_user.id]; st["phone"]=m.text; st["step"]=3
    bot.reply_to(m, "📦 Գրեք ՀԱՍՑԵ/ՄԱՆՐԱՄԱՍՆԵՐ-ը:")

@bot.message_handler(func=lambda m: m.from_user.id in checkout_state and checkout_state[m.from_user.id]["step"]==3)
def take_address(m):
    st = checkout_state[m.from_user.id]; st["addr"]=m.text; st["step"]=4
    text = (
        "🧾 Պատվերի ամփոփում\n"
        f"Անուն՝ {st['name']}\nՀեռ․ {st['phone']}\nՀասցե՝ {st['addr']}\n"
        f"Գումար՝ *{st['subtotal']}֏*\n\n"
        "📤 Խնդրում ենք ուղարկել ՎՃԱՐՄԱՆ ՍՏԱՑԱԿԱՆԸ (ֆոտո/ֆայլ):"
    )
    bot.reply_to(m, text, parse_mode="Markdown")

@bot.message_handler(content_types=['photo','document'])
def take_receipt(m):
    uid = m.from_user.id
    st = checkout_state.get(uid)
    if not st or st.get("step")!=4:
        return
    st["step"]=5
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅️ Վերադառնալ խանութ", callback_data="back_shop"))
    bot.reply_to(m, f"Շնորհակալություն 🌟 Պատվերի գումար՝ {st['subtotal']}֏։ Մեր օպերատորը կհաստատի մոտակա ժամանակում։", reply_markup=kb)
    user_cart[uid] = []  # մաքրենք զամբյուղը
    checkout_state.pop(uid, None)

# ---------------- Exchanges (3 sub menus) ----------------
@bot.message_handler(func=lambda m: m.text and "փոխարկում" in m.text.lower())
def exchange_menu(m):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("PI ➜ USDT", callback_data="ex::pi_usdt"),
        types.InlineKeyboardButton("FTN ➜ AMD", callback_data="ex::ftn_amd"),
        types.InlineKeyboardButton("Alipay ➜ CNY", callback_data="ex::alipay_cny"),
    )
    kb.add(types.InlineKeyboardButton("⬅️ Վերադառնալ հիմնական մենյու", callback_data="back_main_menu"))
    bot.send_message(m.chat.id, "⚙️ Փոխարկումներ և վճարումներ․ ընտրեք ուղղությունը 👇", reply_markup=kb)

EX_TEXTS = {
    "pi_usdt": "💎 *PI ➜ USDT*\n• Արագ peer-to-peer փոխարկում\n• Մին. գումար — 50 PI\n• Գործողություն՝ 10–30 րոպե\n\nՊատվիրելու համար գրեք «Փոխարկում PI» և օպերատորը կապ կհաստատի։",
    "ftn_amd": "🏦 *FTN ➜ AMD*\n• Հարմար փոխարկում՝ պայմանավորված տեմպերով\n\nՊատվիրելու համար գրեք «Փոխարկում FTN»։",
    "alipay_cny": "🇨🇳 *Alipay ➜ CNY*\n• Չինաստան ներսում արագ վճարում Alipay-ով\n\nՊատվիրելու համար գրեք «Alipay վճարում»։",
}

@bot.callback_query_handler(func=lambda c: c.data.startswith("ex::"))
def exchange_details(c):
    key = c.data.split("::",1)[1]
    text = EX_TEXTS.get(key, "Տվյալ ուղղությունը շուտով։")
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("PI ➜ USDT", callback_data="ex::pi_usdt"),
        types.InlineKeyboardButton("FTN ➜ AMD", callback_data="ex::ftn_amd"),
        types.InlineKeyboardButton("Alipay ➜ CNY", callback_data="ex::alipay_cny"),
    )
    kb.add(types.InlineKeyboardButton("⬅️ Վերադառնալ ֆինանսական մենյու", callback_data="back_exchange"))
    bot.send_message(c.message.chat.id, text, parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data=="back_exchange")
def back_exchange(c):
    exchange_menu(c.message)

# ---------------- My page (simple) ----------------
USERS_FILE = "data/users.json"
os.makedirs("data", exist_ok=True)
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False)

def get_user(uid:int)->dict:
    try:
        with open(USERS_FILE,"r",encoding="utf-8") as f:
            d = json.load(f)
    except: d = {}
    u = d.get(str(uid), {})
    u.setdefault("orders_count", 0)
    u.setdefault("coupon_balance", 0)
    return u

def save_user(uid:int, u:dict):
    try:
        with open(USERS_FILE,"r",encoding="utf-8") as f:
            d = json.load(f)
    except: d = {}
    d[str(uid)] = u
    with open(USERS_FILE,"w",encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

@bot.message_handler(func=lambda m: m.text and "իմ էջ" in m.text.lower())
def my_page(m):
    u = get_user(m.from_user.id)
    text = (
        "👤 *Իմ էջ*\n"
        f"Պատվերներ՝ {u.get('orders_count',0)} հատ\n"
        f"Կուպոնների մնացորդ՝ {u.get('coupon_balance',0)}֏\n"
        "\nԵթե ունեք հարց — գրեք «Հետադարձ կապ» բաժնով։"
    )
    bot.send_message(m.chat.id, text, parse_mode="Markdown", reply_markup=kb_back())


user_orders = {}
user_invites = {}
user_levels = {}
user_coupons = {}
user_referrers = {}
user_referrals = {}
user_invitation_coupons = {}
user_referral_total = {}
user_referral_used = {}
user_coupon_balance = {} 
user_coupon_used = {} 
user_feedbacks = {}
user_cart_time = {} 
user_markup_add = {}
user_profile_photos = {}
user_data = {}
best_selling_products = ["BA100818", "BA100820", "BA100821"]

def calculate_coupon_discount(user_id, total_price):
    # 1. Նոր օգտատիրոջ 5%
    first_login_discount = 0
    if user_first_coupon.get(user_id, True):
        first_login_discount = total_price * 0.05

    # 2. Հրավիրվածների քանակով կուպոն (5% կամ 10%)
    invitation_discount = 0
    invitation_percent = user_invitation_coupons.get(user_id, 0)
    if invitation_percent:
        invitation_discount = total_price * (invitation_percent / 100)

    # 3. Հրավիրյալների գնումից կուտակված կուպոն
    total = user_referral_total.get(user_id, 0)
    used = user_referral_used.get(user_id, 0)
    available = total - used

    # Կարելի է օգտագործել՝ իր կուտակվածի 20%, բայց ոչ ավել գնման 10%-ից
    max_from_accumulated = min(available * 0.20, total_price * 0.10)

    # Ընդհանուր զեղչ և վերջնական գին
    total_discount = first_login_discount + invitation_discount + max_from_accumulated
    final_price = total_price - total_discount

    # Տեքստ՝ ամփոփում
    breakdown = f"""💸 Զեղչերի ամփոփում:
🔹 Նոր հաճախորդի զեղչ — {int(first_login_discount)}֏
🔹 Հրավերային զեղչ — {int(invitation_discount)}֏
🔹 Կուտակվածից կիրառված — {int(max_from_accumulated)}֏
📉 Ընդհանուր զեղչ — {int(total_discount)}֏
💰 Վերջնական գին — {int(final_price)}֏
"""

    return int(final_price), breakdown, {
        "first_login_discount": first_login_discount,
        "invitation_discount": invitation_discount,
        "accumulated_used": max_from_accumulated
    }

def apply_coupon_usage(user_id, discount_details):
    if discount_details["first_login_discount"] > 0:
        user_first_coupon[user_id] = False

    if discount_details["invitation_discount"] > 0:
        user_invitation_coupons[user_id] = 0

    if discount_details["accumulated_used"] > 0:
        used = user_referral_used.get(user_id, 0)
        user_referral_used[user_id] = used + int(discount_details["accumulated_used"])
def reward_referrer_on_purchase(buyer_id, order_amount):
    referrer_id = user_referrers.get(buyer_id)
    if referrer_id:
        bonus = int(order_amount * 0.05)
        current = user_referral_total.get(referrer_id, 0)
        user_referral_total[referrer_id] = current + bonus


def register_referrer(new_user_id, referrer_id):
    if new_user_id == referrer_id:
        return  # Չի կարելի ինքն իրեն հրավիրել

    if new_user_id not in user_referrers:
        user_referrers[new_user_id] = referrer_id

        if referrer_id not in user_referrals:
            user_referrals[referrer_id] = []
        if new_user_id not in user_referrals[referrer_id]:
            user_referrals[referrer_id].append(new_user_id)

            if referrer_id not in user_coupon_balance:
                user_coupon_balance[referrer_id] = 0
            user_coupon_balance[referrer_id] += 5  # Յուրաքանչյուր գրանցվածի համար 5%

            count = len(user_referrals[referrer_id])
            if count % 10 == 0:
                user_invitation_coupons[referrer_id] = 10
            elif count % 5 == 0:
                user_invitation_coupons[referrer_id] = 5
    if count == 10:
        user_loyalty[user_id] = user_loyalty.get(user_id, 0) + 10

    if referrer_id not in user_referral_used:
        user_referral_used[referrer_id] = 0

    if referrer_id not in user_referral_total:
        user_referral_total[referrer_id] = 0

    user_referral_total[referrer_id] += 5

def get_user_discount(user_id):
    total = user_referral_total.get(user_id, 0)
    used = user_referral_used.get(user_id, 0)
    return max(0, total - used)

@bot.message_handler(func=lambda message: message.text == "🔖 Կիրառել կուպոն")
def apply_coupon(message):
    user_id = message.from_user.id
    cart = user_carts.get(user_id, {})
    if not cart:
        bot.send_message(user_id, "🛒 Ձեր զամբյուղը դատարկ է։")
        return

    total_price = calculate_cart_total(user_id)
    final_price, breakdown, discount_details = calculate_coupon_discount(user_id, total_price)

    apply_coupon_usage(user_id, discount_details)

    bot.send_message(user_id, f"""
💰 Զեղչեր կիրառված են.

Առաջին գնումի զեղչ՝ {breakdown['first_login_discount']}֏  
Հրավերի կուպոն՝ {breakdown['invitation_discount']}֏  
Կուտակված կուպոն՝ {breakdown['accumulated_used']}֏  

💵 Վճարելու եք՝ {final_price}֏
""")

    show_cart(message)
@bot.message_handler(func=lambda message: message.text == "💌 Հրավիրիր ընկերոջդ")
def invite_friend(message):
    user_id = message.from_user.id
    invite_link = f"https://t.me/{bot.get_me().username}?start={user_id}"
    bot.send_message(user_id, f"""
📣 Ուզու՞մ եք զեղչ ստանալ։  
🚀 Ուղարկեք այս հղումը ձեր ընկերներին և ստացեք կուպոն յուրաքանչյուր գրանցման համար։

🔗 Ձեր հրավերի հղումը՝  
{invite_link}
""")

@bot.message_handler(commands=["start"])
def on_start(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # ակտիվացնենք առաջին գնումի բոնուսը (եթե պետք է)
    ensure_first_order_bonus(user_id)

    # Գլխավոր մենյու
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🛍 Խանութ", "🛒 Զամբյուղ")
    markup.add("📦 Իմ պատվերները", "🎁 Կուպոններ")
    markup.add("🔍 Որոնել ապրանք", "🎡 Բոնուս անիվ")
    markup.add("🧍 Իմ էջը", "🏆 Լավագույններ")
    markup.add("💱 Փոխարկումներ", "💬 Հետադարձ կապ")
    markup.add("Հրավիրել ընկերների")

    # Հաճախորդի համար / user տվյալներ
    customer_no = get_next_customer_no()
    u = get_user(user_id)
    first_bonus_active = (u.get("orders_count", 0) == 0 and not u.get("first_order_bonus_used", False))
    bonus_pct = u.get("first_order_bonus_pct", 5)

    # 📝 մարկետինգային ողջույն (միայն բառերը փոփոխված)
    top = (
        "🐰🌸 **Բարի գալուստ BabyAngels** 🛍️\n\n"
        f"💖 Շնորհակալ ենք, որ ընտրեցիք մեզ ❤️ Դուք արդեն մեր սիրելի հաճախորդն եք՝ **№{customer_no}**։\n\n"
    )
    discount = (
        f"🎁 **Լավ լուր․ առաջին պատվերի համար ունեք {bonus_pct}% զեղչ** — "
        "կկիրառվի ավտոմատ վճարման պահին։\n\n"
    ) if first_bonus_active else ""
    body = (
        "📦 Ինչ կգտնեք մեզ մոտ՝\n"
        "• Ժամանակակից ու ոճային ապրանքներ ամեն օր թարմացվող տեսականուց\n"
        "• Հատուկ ակցիաներ և անակնկալ առաջարկներ\n"
        "• Անվճար առաքում Հայաստանի ողջ տարածքում\n\n"
        "💱 Բացի խանութից՝ տրամադրում ենք հուսալի և արագ **փոխարկման ծառայություններ**՝\n"
        "PI ➜ USDT | FTN ➜ AMD | Alipay ➜ CNY — միշտ շահավետ և արագ 🌟\n\n"
        "👇 Ընտրեք բաժին և սկսեք գնումները հիմա"
    )
    welcome_text = top + discount + body

    # Ուղարկում՝ լուսանկարով, եթե կա
    try:
        with open("media/bunny.jpg", "rb") as photo:
            bot.send_photo(chat_id, photo, caption=welcome_text, reply_markup=markup, parse_mode="Markdown")
    except Exception:        
        bot.send_message(chat_id, welcome_text, reply_markup=markup, parse_mode="Markdown")
        
@bot.message_handler(func=lambda m: m.text and m.text.strip().endswith("Խանութ"))
def open_shop(message):
    try:
        kb = household_menu()  # քո արդեն գոյություն ունեցող InlineKeyboardMarkup-ն
        bot.send_message(
            message.chat.id,
            "🛍 Ընտրեք ապրանքը ⬇️",
            reply_markup=kb
        )
    except Exception as e:
        bot.send_message(message.chat.id, "🙈 Ապրանքների ցանկը հիմա հասանելի չէ։")
# --- ԲՈԼՈՐ ԿՈՃԱԿՆԵՐԻ ՌՈՒՏԵՐ (մի տեղից կառավարում) ---
def _norm(t: str) -> str:
    if not t:
        return ""
    return t.replace("\u200d", "").replace("\ufe0f", "").strip()

MENU_HANDLERS = {
    "🛍 Խանութ": lambda m: open_shop(m),  # ՔԱՅԼ 1-ով արդեն ունես open_shop
    "🛒 Զամբյուղ": lambda m: bot.send_message(m.chat.id, "🛒 Զամբյուղը բացվեց"),
    "📦 Իմ պատվերները": lambda m: bot.send_message(m.chat.id, "📦 Այստեղ կլինեն ձեր պատվերները"),
    "🎁 Կուպոններ": lambda m: bot.send_message(m.chat.id, "🎁 Կուպոնների բաժին"),
    "🔍 Որոնել ապրանք": lambda m: bot.send_message(m.chat.id, "🔎 Գրեք ապրանքի անունը"),
    "🎡 Բոնուս անիվ": lambda m: bot.send_message(m.chat.id, "🎡 Շուտով կակտիվացնենք"),
    "🧍 Իմ էջը": lambda m: bot.send_message(m.chat.id, "👤 Ձեր պրոֆիլը"),
    "🏆 Լավագույններ": lambda m: bot.send_message(m.chat.id, "🏆 Թոփ ապրանքներ"),
    "💱 Փոխարկումներ": lambda m: bot.send_message(m.chat.id, "💱 Փոխարկումների տեղեկություն"),
    "💬 Հետադարձ կապ": lambda m: bot.send_message(m.chat.id, "💬 Գրեք ձեր հարցը"),
    "Հրավիրել ընկերների": lambda m: bot.send_message(m.chat.id, "🤝 Հրավիրելու հղումը շուտով"),
}

@bot.message_handler(func=lambda m: _norm(m.text) in {_norm(k) for k in MENU_HANDLERS})
def _route_menu(message):
    key = [k for k in MENU_HANDLERS if _norm(k) == _norm(message.text)][0]
    MENU_HANDLERS[key](message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("prod_"))
def show_product(call):
    # այստեղ բացում ես prod քարտը. հիմա՝ պարզ հաստատում
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, f"📦 Բացել ես ապրանքը՝ {call.data}")

# ========== ԲԸԺԱԿՆԵՐԻ ՀԱՆԴԼԵՐՆԵՐ (ReplyKeyboard) ==========
def send_pretty(chat_id: int, title: str, body: str = "", kb=None):
    text = f"{title}\n\n{body}" if body else title
    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "🛍 Խանութ")
def open_shop(message):
    body = (
        "✨ Թերթիր տեսականին, սեղմիր ապրանքի վրա և ավելացրու **Զամբյուղ**։\n"
        "📦 Առաքումը՝ ՀՀ ամբողջ տարածքում, հաճախ՝ *անվճար*։\n"
        "👇 Սկսելու համար գրիր՝ *Որոնել ապրանք* կամ անցիր բաժիններին։"
    )
    send_pretty(message.chat.id, "🛍 **Խանութ — նոր տեսականի**", body)

@bot.message_handler(func=lambda m: m.text == "🛒 Զամբյուղ")
def open_cart(message):
    try:
        show_cart(message)  # եթե ունես ֆունկցիան
    except NameError:
        send_pretty(message.chat.id, "🛒 **Զամբյուղ**", "Զամբյուղը ժամանակավորապես դատարկ է 🙈")

@bot.message_handler(func=lambda m: m.text == "📦 Իմ պատվերները")
def my_orders(message):
    body = "Կտեսնես քո բոլոր պատվերների կարգավիճակները։ Շուտով՝ ծանուցումներ 📬"
    send_pretty(message.chat.id, "📦 **Իմ պատվերները**", body)

@bot.message_handler(func=lambda m: m.text == "🎁 Կուպոններ")
def coupons(message):
    body = (
        "🏷 Այստեղ կհայտնվեն քո կուպոններն ու բոնուս միավորները։\n"
        "💡 Առաջին պատվերին հաճախորդները ունեն **5% զեղչ**։"
    )
    send_pretty(message.chat.id, "🎁 **Կուպոններ և բոնուսներ**", body)

@bot.message_handler(func=lambda m: m.text == "🔍 Որոնել ապրանք")
def search_product(message):
    body = "Գրի՛ր ապրանքի անունը կամ բանալի բառ (օր․ *շոր, խաղալիք, կրեմ*)."
    send_pretty(message.chat.id, "🔍 **Որոնել ապրանք**", body)

@bot.message_handler(func=lambda m: m.text == "🎡 Բոնուս անիվ")
def bonus_wheel(message):
    body = "Շուտով կհայտնվի 🎡 խաղարկային անիվը՝ նվերներով ու զեղչերով։ Մնա՛ հետապնդման մեջ 😉"
    send_pretty(message.chat.id, "🎡 **Բոնուս անիվ**", body)

@bot.message_handler(func=lambda m: m.text == "🧍 Իմ էջը")
def my_profile(message):
    body = "Այստեղ կհավաքվեն քո տվյալները, բոնուսները և նախընտրությունները։"
    send_pretty(message.chat.id, "🧍 **Իմ էջը**", body)

@bot.message_handler(func=lambda m: m.text == "🏆 Լավագույններ")
def bestsellers(message):
    body = "Տես մեր ամենապահանջված ապրանքները ⭐️ Վստահված որակ, սիրելի գներ։"
    send_pretty(message.chat.id, "🏆 **Լավագույններ**", body)

@bot.message_handler(func=lambda m: m.text == "💱 Փոխարկումներ")
def exchange_menu(message):
    body = (
        "Փոխարկում ենք արագ ու հուսալի՝\n"
        "• PI ➜ USDT\n• FTN ➜ AMD\n• Alipay ➜ CNY\n\n"
        "✍️ Ուղարկի՛ր գումարը/ուղղությունը, ՁԵԶ կվերադարձնեմ հստակ առաջարկով։"
    )
    send_pretty(message.chat.id, "💱 **Փոխարկումներ**", body)

@bot.message_handler(func=lambda m: m.text == "💬 Հետադարձ կապ")
def feedback_menu(message):
    body = "Գրեք ձեր հարցը/մտահոգությունը, պատասխան եմ տալիս հնարավորինս արագ 🙌"
    send_pretty(message.chat.id, "💬 **Հետադարձ կապ**", body)

@bot.message_handler(func=lambda m: m.text == "Հրավիրել ընկերների")
def invite_friends_btn(message):
    try:
        invite_friend(message)  # եթե ունես այս ֆունկցիան
    except Exception:
        send_pretty(message.chat.id, "🤝 **Հրավիրել ընկերների**",
                    "Ստացիր հղում և տարածիր․ յուրաքանչյուր ակտիվ հրավերի համար՝ բոնուս 🎁")


# ---------- Խանութի մենյուն (քո տարբերակը լավն է, թող 그대로 մնա)
# ===================== PRODUCTS: Load/Save + Show (FULL) =====================
import os, json, random
from telebot import types

PRODUCTS_DIR = "products"           # JSON-ների պանակը
MEDIA_DIR    = "media/products"     # Նկարների պանակը
PRODUCTS     = {}                   # { "BA100810": {...}, ... }

def _ensure_dirs():
    os.makedirs(PRODUCTS_DIR, exist_ok=True)
    os.makedirs(MEDIA_DIR, exist_ok=True)

from telebot import types

@bot.callback_query_handler(func=lambda c: c.data in PRODUCTS)
def show_product(c):
    p = PRODUCTS[c.data]
    bot.answer_callback_query(c.id)
    try:
        with open(p["photo"], "rb") as ph:
            kb = types.InlineKeyboardMarkup()
            kb.add(
                types.InlineKeyboardButton("➕ Ավելացնել զամբյուղ", callback_data=f"add_{p['code']}"),
                types.InlineKeyboardButton("⬅️ Վերադառնալ խանութ", callback_data="back_shop"),
            )
            bot.send_photo(c.message.chat.id, ph, caption=build_caption(p),
                           parse_mode="Markdown", reply_markup=kb)
    except Exception:
        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton("➕ Ավելացնել զամբյուղ", callback_data=f"add_{p['code']}"),
            types.InlineKeyboardButton("⬅️ Վերադառնալ խանութ", callback_data="back_shop"),
        )
        bot.send_message(c.message.chat.id, build_caption(p), parse_mode="Markdown", reply_markup=kb)


def save_product(p):
    """Պահպանում է մեկ ապրանքի json-ը products/ պանակում"""
    _ensure_dirs()
    path = os.path.join(PRODUCTS_DIR, f"{p['code']}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(p, f, ensure_ascii=False, indent=2)

def build_caption(p):
    """Կազմում է ապրանքի քարտի նկարագրությունը"""
    lines = []
    lines.append(f"**{p['title']}**")
    if p.get("description"):
        lines.append(p["description"])
        lines.append("")  # դատարկ տող
    # գնի մասն
    try:
        discount = 0
        if p["old_price"] and p["old_price"] > p["price"]:
            discount = round((p["old_price"] - p["price"]) * 100 / p["old_price"])
        old_line = f"❌ Հին գին — ~~{p['old_price']}֏~~" + (f" (-{discount}%)" if discount else "")
    except Exception:
        old_line = f"❌ Հին գին — ~~{p.get('old_price','')}֏~~"
    lines.append(old_line)
    lines.append(f"✅ Նոր գին — **{p['price']}֏**")
    lines.append(f"🔥 Վաճառված՝ **{p.get('fake_sales', 0)}+ հատ**")
    return "\n".join(lines)


# ---------- Ապրանքի բացում (մԻԱԿ handler՝ աշխատում է թե 'BA…', թե 'prod_BA…')
@bot.callback_query_handler(
    func=lambda c: (c.data in PRODUCTS) or (c.data.startswith('prod_') and c.data.replace('prod_', '') in PRODUCTS)
)
def show_product(c):
    code = c.data.replace("prod_", "")
    if code not in PRODUCTS:
        bot.answer_callback_query(c.id, text="Չգտնվեց")
        return
    p = PRODUCTS[code]
    bot.answer_callback_query(c.id)

    # Inline կոճակներ
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("➕ Ավելացնել զամբյուղ", callback_data=f"add_{code}"),
        types.InlineKeyboardButton("⬅️ Վերադառնալ խանութ", callback_data="back_shop"),
    )

    # Փորձենք ուղարկել 1-ին նկարը, այլապես՝ միայն տեքստ
    sent = False
    if p.get("images"):
        img_name = p["images"][0]
        img_path = os.path.join(MEDIA_DIR, img_name)  # ՆԿԱՐԸ media/products/ պանակում
        if os.path.isfile(img_path):
            try:
                with open(img_path, "rb") as ph:
                    bot.send_photo(
                        c.message.chat.id, ph,
                        caption=build_caption(p),
                        parse_mode="Markdown",
                        reply_markup=kb
                    )
                    sent = True
            except Exception:
                sent = False
    if not sent:
        bot.send_message(
            c.message.chat.id,
            build_caption(p),
            parse_mode="Markdown",
            reply_markup=kb
        )

# ---------- Վերադառնալ խանութ
@bot.callback_query_handler(func=lambda c: c.data == "back_shop")
def back_shop(c):
    bot.answer_callback_query(c.id)
    try:
        bot.edit_message_reply_markup(c.message.chat.id, c.message.message_id)
    except Exception:
        pass
    bot.send_message(c.message.chat.id, "🛍 Ընտրեք ապրանքը ⬇️", reply_markup=household_menu())

# ---------- Ավելացնել զամբյուղ (+1 fake sales և պահպանում JSON-ում)
@bot.callback_query_handler(func=lambda c: c.data.startswith("add_"))
def add_to_cart(c):
    code = c.data.replace("add_", "")
    if code in PRODUCTS:
        PRODUCTS[code]["fake_sales"] = PRODUCTS[code].get("fake_sales", 0) + 1
        save_product(PRODUCTS[code])  # պահպանում ենք products/BAxxxxx.json-ում
    bot.answer_callback_query(c.id, text="Ապրանքը ավելացվեց զամբյուղ 👌")


# ---------------------- Քայլ 16. Ֆեյք վաճառքի քանակի պահպանում ----------------------

fake_sales = {
    "BA100810": 65,
    "BA100811": 61,
    "BA100812": 75,
    "BA100813": 19,
    "BA100814": 108,
    "BA100815": 182,
    "BA100816": 35,
    "BA100817": 157,
    "BA100818": 62,
    "BA100819": 209,
    "BA100820": 178,
    "BA100821": 25,
}

# ---------------------- Քայլ 17. Վաճառքից հետո ֆեյք քանակի թարմացում ----------------------

def increase_fake_sales(product_code):
    if product_code in best_selling_products:
        fake_sales[product_code] += 2
    elif product_code in fake_sales:
        fake_sales[product_code] += random.randint(2, 6)

# ---------------------- Քայլ 18. Ֆիդբեքից հետո թարմացում ----------------------

@bot.message_handler(func=lambda m: m.text.startswith("⭐ Հետադարձ կապ"))
def handle_feedback(message):
    user_id = message.from_user.id
    feedback_text = message.text.replace("⭐ Հետադարձ կապ", "").strip()

    if not feedback_text:
        bot.send_message(user_id, "Խնդրում ենք գրել ձեր կարծիքը։")
        return

    # պահենք մեր dict–ում (պահեստավորում, եթե քեզ պետք է)
    user_feedbacks[user_id] = feedback_text

    # ուղարկենք ադմին(ներ)ին
    for admin_id in admin_list:
        bot.send_message(
            admin_id,
            f"💬 Նոր կարծիք @{message.from_user.username or user_id}:\n{feedback_text}"
        )

    # հաստատում օգտվողին
        bot.send_message(
        user_id,
        "🌸 Շնորհակալություն, որ կիսվեցիք ձեր կարծիքով 🥰\n"
        "Ձեր արձագանքը մեզ օգնում է դառնալ ավելի լավ 💕")

@bot.message_handler(func=lambda message: message.text == "🎁 Բոնուս անիվ")
def bonus_wheel(message):
    user_id = message.from_user.id
    text = (
        "🎁 Բարի գալուստ **Բոնուս անիվ** բաժին ։\n\n"
        "Շուտով դուք այստեղ կկարողանաք պտտել անիվը և շահել զեղչեր, նվերներ, կտրոններ և այլ հաճելի անակնկալներ։\n\n"
        "📌 Այս պահի դրությամբ այս բաժինը պատրաստման փուլում է։"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Վերադառնալ", callback_data="back_to_main"))
    bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=markup)
@bot.message_handler(func=lambda message: message.text == "🚚 Առաքման մանրամասներ")
def delivery_info(message):
    user_id = message.from_user.id
    text = (
        "🚚 **Առաքման պայմաններ**\n\n"
        "✅ Առաքումը ամբողջ Հայաստանի տարածքում՝ **ԱՆՎՃԱՐ**։\n"
        "📦 Պատվերների առաքումը կատարվում է 1–3 աշխատանքային օրվա ընթացքում։\n"
        "📬 Առաքումը կատարվում է ՀայՓոստի միջոցով՝ ձեր նշած հասցեով։\n"
        "🕓 Առաքման ժամանակը կախված է ձեր մարզից կամ քաղաքի վայրից։\n"
        "🔎 Պատվերից հետո դուք կստանաք ձեր առաքման հետևման համար tracking կոդ։"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Վերադառնալ", callback_data="back_to_main"))
    bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=markup)
@bot.message_handler(func=lambda message: message.text == "💳 Վճարման ձևեր")
def payment_methods(message):
    user_id = message.from_user.id
    text = (
        "💳 **Վճարման տարբերակներ**\n\n"
        "📱 **IDram / TelCell Wallet** — փոխանցում մեր համարին\n"
        "🏧 **Կանխիկ** — վճարում ստանալիս (միայն Երևանում)\n"
        "💸 **USDT (TRC20)** — փոխանցում կրիպտո հաշվին\n"
        "🇨🇳 **AliPay** — լիցքավորում ըստ հաշվեհամարի\n\n"
        "❗ Վճարումը հաստատելու համար ուղարկեք ստացականի նկար կամ տեքստ։\n"
        "✅ Մենք կստուգենք և կհաստատենք պատվերը։"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Վերադառնալ", callback_data="back_to_main"))
    bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=markup)
@bot.message_handler(func=lambda message: message.text == "🚚 Առաքման հետևում")
def order_tracking(message):
    user_id = message.from_user.id
    text = (
        "📦 **Պատվերի հետևում**\n\n"
        "Եթե դուք ստացել եք հետևելու համար **Հայփոստ tracking code** (օրինակ՝ RR123456789AM),\n"
        "կարող եք հետևել ձեր առաքմանը՝ սեղմելով այս հղումը 👇\n\n"
        "🌐 https://www.haypost.am/en/track\n\n"
        "Եթե դուք դեռ չեք ստացել ձեր tracking code, ապա սպասեք մեր հաստատմանը 📩"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Վերադառնալ", callback_data="back_to_main"))
    bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=markup)
@bot.message_handler(func=lambda message: message.text == "🔐 Վճարման անվտանգություն")
def payment_security(message):
    user_id = message.from_user.id
    text = (
        "🔐 **Վճարման անվտանգություն և վստահություն**\n\n"
        "🛡️ Մեր բոտը պաշտպանում է ձեր տվյալները և վճարները՝ ապահովելով անվտանգ գործընթաց։\n"
        "✅ Մենք ընդունում ենք միայն ստուգված վճարման եղանակներ՝ Telcell, Idram, USDT (քրիպտո), բանկային քարտ (Visa / MasterCard):\n"
        "📦 Ձեր պատվերը հաստատվում է միայն ստացականը ստանալուց հետո։\n"
        "🧾 Դուք միշտ կարող եք ուղարկել ապացույց և ստանալ հաստատում։\n\n"
        "Եթե հարցեր ունեք՝ գրեք մեզ 📩"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Վերադառնալ", callback_data="back_to_main"))
    bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=markup)
@bot.message_handler(func=lambda message: message.text == "📢 Գովազդային առաջարկ")
def ad_space(message):
    user_id = message.from_user.id
    photo = open("media/ads/promo_banner.jpg", "rb")  # Ձեր գովազդային նկարի ուղին
    caption = (
        "📢 **Հատուկ առաջարկ մեր գործընկերներից**\n\n"
        "🎁 Այցելեք մեր գործընկերների խանութ և ստացեք 10% զեղչ մեր կողմից։\n"
        "🌐 [Դիտել առաջարկը](https://example.com)"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Վերադառնալ", callback_data="back_to_main"))
    bot.send_photo(user_id, photo=photo, caption=caption, parse_mode="Markdown", reply_markup=markup)
@bot.message_handler(func=lambda message: message.text == "💡 Լավ մտքեր")
def good_thoughts(message):
    user_id = message.from_user.id
    text = (
        "💡 **Օրվա լավ միտքը**\n\n"
        "👉 «Միշտ հիշիր՝ ամենամութ գիշերը նույնիսկ անցնում է և լույս է գալիս»\n\n"
        "Կիսվիր այս մտքով քո ընկերների հետ՝ ոգեշնչելու նրանց 😊"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📤 Կիսվել", switch_inline_query="💡 Լավ միտք հենց քեզ համար!"))
    markup.add(types.InlineKeyboardButton("🔙 Վերադառնալ", callback_data="back_to_main"))
@bot.message_handler(func=lambda message: message.text == "💡 Լավ մտքեր")
def good_thoughts(message):
    user_id = message.from_user.id
    text = "Սիրով կիսվենք ոգեշնչող մտքերով 😊"

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Վերադառնալ", callback_data="back_to_main"))

    if user_id in user_profile_photos:
        bot.send_photo(user_id, user_profile_photos[user_id], caption=text, parse_mode="Markdown", reply_markup=markup)
    else:
        bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(content_types=["photo"])
def handle_profile_photo(message):
    user_id = message.from_user.id
    if message.caption == "👤 Իմ ֆոտոն":
        photo_id = message.photo[-1].file_id
        user_profile_photos[user_id] = photo_id
        bot.send_message(user_id, "📸 Ձեր ֆոտոն հաջողությամբ պահպանվեց։")
@bot.callback_query_handler(func=lambda call: call.data.startswith("reorder_"))
def reorder_product(call):
    user_id = call.from_user.id
    code = call.data.split("_", 1)[1]
    user_carts.setdefault(user_id, {})
    user_carts[user_id][code] = user_carts[user_id].get(code, 0) + 1
    bot.answer_callback_query(call.id, "Ավելացվեց զամբյուղում։")
    bot.send_message(user_id, "✅ Ապրանքը կրկին ավելացվեց ձեր զամբյուղ։")
def apply_first_order_coupon(user_id, total_price):
    if user_id not in user_orders or len(user_orders[user_id]) == 0:
        user_first_coupon[user_id] = True
        discount = total_price * 0.05
        return round(discount)
    return 0
def check_cart_reminders():
    while True:
        current_time = time.time()
        for user_id, added_time in list(user_cart_time.items()):
            if current_time - added_time > 86400:  # 24 ժամ անցել է
                bot.send_message(user_id, "📌 Մոռացե՞լ եք ձեր զամբյուղի մասին։ Այն դեռ սպասում է ձեզ։🛒")
                del user_cart_time[user_id]
        time.sleep(600)  # ստուգի ամեն 10 րոպեն մեկ
threading.Thread(target=check_cart_reminders, daemon=True).start()
if __name__ == "__main__":
    print("Bot started…")
    bot.remove_webhook()
    time.sleep(1)

    # keep polling, auto-retry on errors
# ---- 24/7 Webhook for Render ----

# եթե TOKEN-ը վերևում ունես, սա անտեսիր.
# TOKEN = os.getenv("TELEGRAM_TOKEN", "Քո_Token-ը_այստեղ")

app = Flask(__name__)
WEBHOOK_PATH = f"/webhook/{TOKEN}"                 # գաղտնի ուղի
BASE_URL = f"https://{os.getenv('RENDER_EXTERNAL_URL','localhost')}"  # Render-ը սա տալիս է env-ում
WEBHOOK_URL = BASE_URL + WEBHOOK_PATH

# առողջության ստուգում Render-ի համար
@app.get("/")
def health():
    return "ok", 200

# Telegram-ը POST է ուղարկելու հենց այստեղ
@app.post(WEBHOOK_PATH)
def telegram_webhook():
    if request.headers.get("content-type") != "application/json":
        abort(403)
    update = request.get_data().decode("utf-8")
    bot.process_new_updates([telebot.types.Update.de_json(update)])
    return "ok", 200

def set_webhook():
    try:
        # նախ հներին անջատենք
        requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook", timeout=10)
        # նոր webhook՝
        r = requests.get(
            f"https://api.telegram.org/bot{TOKEN}/setWebhook",
            params={"url": WEBHOOK_URL, "drop_pending_updates": True},
            timeout=10,
        )
        print("setWebhook:", r.json())
    except Exception as e:
        print("setWebhook error:", e)

if name == "main":
    print(f"Бот запустился с WEBHOOK: {WEBHOOK_URL}")
    set_webhook()
    приложение.бегать(хозяин="0.0.0.0", порт=порт)

