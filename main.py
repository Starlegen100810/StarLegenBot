import os, re, time, json, glob, random, textwrap, threading, requests, hashlib, logging
from datetime import datetime
from flask import Flask, request, abort
import telebot
from telebot import types

# ==================== BASE INFO ====================
user_carts = {}  # {user_id: {code: qty}}
cart_timers = {}

STARTED_AT = time.strftime("%Y-%m-%d %H:%M:%S")
FILE_PATH  = os.path.abspath(__file__)
try:
    FILE_HASH = hashlib.md5(open(__file__, "rb").read()).hexdigest()[:8]
except Exception:
    FILE_HASH = "nohash"

# Flask + telebot logger
telebot.logger.setLevel(logging.DEBUG)
app = Flask(__name__)

# ==================== ENV & CONFIG ====================
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Bot token (prefer BOT_TOKEN, fallback TELEGRAM_BOT_TOKEN)
TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN or ":" not in TOKEN:
    raise Exception("BOT_TOKEN is not set (put it in .env)")

# Admin IDs: ADMIN_IDS="123,456" or ADMIN_ID="123"
_admin_env = os.getenv("ADMIN_IDS") or os.getenv("ADMIN_ID", "")
ADMIN_IDS = {int(x) for x in _admin_env.replace(" ", "").split(",") if x.isdigit()}
admin_list = list(ADMIN_IDS)

# ==================== BOT INSTANCE ====================
bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")
# Make sure we're in polling mode (no webhook leftovers)
bot.delete_webhook(drop_pending_updates=True)

# If you ever use webhook hosting, keep the URL here (not used in polling)
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL  = f"https://babyangelsbot08.onrender.com{WEBHOOK_PATH}"

# ==================== HELPERS ====================
def is_admin(m) -> bool:
    """Single unified admin check."""
    try:
        # custom helper if user had one
        if '_is_admin' in globals():
            try:
                if _is_admin(m):
                    return True
            except:
                pass
        # set of ids
        if 'ADMIN_IDS' in globals():
            if int(m.from_user.id) in set(int(x) for x in ADMIN_IDS):
                return True
        # list of ids
        if 'admin_list' in globals():
            if int(m.from_user.id) in [int(x) for x in admin_list]:
                return True
        # single id compatibility
        if 'ADMIN_ID' in globals():
            if int(m.from_user.id) == int(ADMIN_ID):
                return True
    except:
        pass
    return False

def calculate_cart_total(user_id: int) -> int:
    total = 0
    cart = user_carts.get(user_id, {})
    for code, qty in cart.items():
        price = int(PRODUCTS.get(code, {}).get("price", 0))
        total += price * int(qty)
    return total

# --- quick diagnostics (/version, /where) ---
@bot.message_handler(commands=['version','where'])
def _version(m):
    bot.reply_to(
        m,
        f"🧩 path: `{FILE_PATH}`\n"
        f"📦 hash: `{FILE_HASH}`\n"
        f"⏱ started: {STARTED_AT}",
        parse_mode="Markdown"
    )

# ==================== files & dirs ====================
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

def calculate_cart_total(user_id: int) -> int:
    total = 0
    cart = user_carts.get(user_id, {})
    for code, qty in cart.items():
        price = int(PRODUCTS.get(code, {}).get("price", 0))
        total += price * int(qty)
    return total


telebot.logger.setLevel(logging.DEBUG)
app = Flask(__name__)

# ---------- ENV & CONFIG ----------
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# BOT TOKEN from .env (prefer BOT_TOKEN, fallback TELEGRAM_BOT_TOKEN)
TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN or ":" not in TOKEN:
    raise Exception("BOT_TOKEN is not set (use .env)")

# Admin IDs: ADMIN_IDS="123,456" or ADMIN_ID="123"
_admin_env = os.getenv("ADMIN_IDS") or os.getenv("ADMIN_ID", "")
ADMIN_IDS = {int(x) for x in _admin_env.replace(" ", "").split(",") if x.isdigit()}
admin_list = list(ADMIN_IDS)

def is_admin(m) -> bool:
    try:
        return int(m.from_user.id) in ADMIN_IDS
    except Exception:
        return False

# Single bot instance
bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

# Ensure polling mode (no webhook)
bot.delete_webhook(drop_pending_updates=True)

# Webhook (մնա, եթե պետք գա; polling-ը կաշխատի առանց դրա էլ)
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL  = f"https://babyangelsbot08.onrender.com{WEBHOOK_PATH}"


# --- Config / Bot ---
def is_admin(m) -> bool:
    try:
        # your own function (if exists)
        if '_is_admin' in globals(): 
            try: 
                return bool(_is_admin(m))
            except: 
                pass
        # set of ids
        if 'ADMIN_IDS' in globals():
            if int(m.from_user.id) in set(int(x) for x in ADMIN_IDS):
                return True
        # list of ids
        if 'admin_list' in globals():
            if int(m.from_user.id) in [int(x) for x in admin_list]:
                return True
        # single id
        if 'ADMIN_ID' in globals():
            if int(m.from_user.id) == int(ADMIN_ID):
                return True
    except:
        pass
    return False

# --- files & dirs ---
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

USERS_FILE   = os.path.join(DATA_DIR, "users.json")      # [ids]
EVENTS_FILE  = os.path.join(DATA_DIR, "events.jsonl")    # json lines
PAY_FILE     = os.path.join(DATA_DIR, "payments.json")   # {pay_id: {...}}
COUPON_FILE  = os.path.join(DATA_DIR, "coupons.json")    # {user_id: balance}
INVITES_FILE = os.path.join(DATA_DIR, "invites.json")    # {"ref_map":{}, "count":{}}

def _load(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def _save(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def _append_event(kind, uid=None, meta=None):
    rec = {"ts": int(time.time()), "kind": kind, "user_id": int(uid) if uid else None, "meta": meta or {}}
    try:
        with open(EVENTS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except:
        pass
# --- users registry (for broadcast/stats) ---
def _users() -> set: return set(_load(USERS_FILE, []))
def _users_save(s: set): _save(USERS_FILE, sorted(list(s)))
def _touch_user(uid: int):
    s = _users()
    if uid not in s:
        s.add(uid)
        _users_save(s)
        _append_event("user_new", uid)  # event பதிவு
@bot.message_handler(content_types=['text','photo','document','video','audio','voice','sticker','location','contact'])
def __seen__(m):
    try:
        _touch_user(int(m.from_user.id))
        _append_event("msg", m.from_user.id, {"type": m.content_type, "text": (m.text or "")[:120]})
    except:
        pass

# --- coupons ---
def _coupons(): return _load(COUPON_FILE, {})
def _coupons_save(d): _save(COUPON_FILE, d)

def add_coupon(uid:int, amount:float):
    d = _coupons()
    bal = float(d.get(str(uid), 0))
    bal = round(bal + float(amount), 2)
    d[str(uid)] = bal
    _coupons_save(d)
    return bal

def get_coupon(uid:int) -> float:
    return float(_coupons().get(str(uid), 0))

# --- invites (via /start <ref>) ---
def _invites():
    d = _load(INVITES_FILE, {})
    d.setdefault("ref_map", {})
    d.setdefault("count", {})
    return d

def _invites_save(d): _save(INVITES_FILE, d)

def register_invite(invitee:int, referrer:int):
    if invitee == referrer: return
    d = _invites()
    if str(invitee) in d["ref_map"]: return
    d["ref_map"][str(invitee)] = int(referrer)
    d["count"][str(referrer)] = int(d["count"].get(str(referrer), 0)) + 1
    _invites_save(d)
    _append_event("invited", invitee, {"referrer": int(referrer)})
@bot.message_handler(commands=['ping'])
def _ping(m):
    print(f"PING from {m.from_user.id}")
    bot.reply_to(m, "pong")
def __capture_ref__(m):
    try:
        parts = m.text.strip().split(maxsplit=1)
        if len(parts) == 2 and parts[1].isdigit():
            register_invite(int(m.from_user.id), int(parts[1]))
    except:
        pass

# --- helpers ---
def _new_id(prefix="p"): return f"{prefix}{int(time.time()*1000)}"

def parse_number(s: str) -> float:
    s = s.strip().upper().replace("AMD","").replace("USD","").replace("֏","")
    s = s.replace(",", "").replace(" ", "")
    if not re.match(r"^-?\d+(\.\d+)?$", s):
        raise ValueError("number")
    return float(s)

def _today_range():
    dt = datetime.now()
    start = int(datetime(dt.year, dt.month, dt.day).timestamp())
    end   = start + 86400
    return start, end

# --- payments store ---
def _pays(): return _load(PAY_FILE, {})
def _pays_save(d): _save(PAY_FILE, d)

# --------------------------- USER: /pay FLOW ---------------------------
USER_STATE = {}

@bot.message_handler(commands=['pay'])
def pay_start(m):
    USER_STATE[m.from_user.id] = {"mode":"price"}
    bot.reply_to(m, "🧾 Գրիր **ապրանքի գինը** (AMD). Օր.`1240`։\n/cancel՝ չեղարկել")

@bot.message_handler(commands=['cancel'])
def pay_cancel(m):
    if USER_STATE.pop(m.from_user.id, None) is not None:
        bot.reply_to(m, "❎ Չեղարկվեց։")

@bot.message_handler(func=lambda m: USER_STATE.get(m.from_user.id,{}).get("mode")=="price", content_types=['text'])
def pay_price(m):
    try:
        price = parse_number(m.text)
        USER_STATE[m.from_user.id] = {"mode":"sent", "price": price}
        bot.reply_to(m, "💰 Գրիր **փոխանցած գումարը** (AMD). Օր.`1300`։")
    except:
        bot.reply_to(m, "Քանակը գրիր թվերով, օրինակ `1240`։")

@bot.message_handler(func=lambda m: USER_STATE.get(m.from_user.id,{}).get("mode")=="sent", content_types=['text'])
def pay_sent(m):
    st = USER_STATE.get(m.from_user.id, {})
    try:
        sent = parse_number(m.text)
        st["sent"] = sent
        st["mode"] = "receipt"
        USER_STATE[m.from_user.id] = st
        bot.reply_to(m, "📎 Ուղարկիր **անդորագիրը** (ֆոտո կամ փաստաթուղթ)։\n/cancel՝ չեղարկել")
    except:
        bot.reply_to(m, "Քանակը գրիր թվերով, օրինակ `1300`։")

@bot.message_handler(func=lambda m: USER_STATE.get(m.from_user.id,{}).get("mode")=="receipt", content_types=['photo','document'])
def pay_receipt(m):
    st = USER_STATE.get(m.from_user.id, {})
    price = float(st.get("price",0))
    sent  = float(st.get("sent",0))
    pay_id = _new_id("pay_")
    fkind = m.content_type
    fid   = m.photo[-1].file_id if fkind=='photo' else m.document.file_id

    d = _pays()
    d[pay_id] = {
        "id": pay_id,
        "user_id": int(m.from_user.id),
        "username": m.from_user.username,
        "price": price,
        "sent": sent,
        "overpay": round(max(0, sent-price), 2),
        "file_kind": fkind,
        "file_id": fid,
        "status": "pending",
        "ts": int(time.time())
    }
    _pays_save(d)
    USER_STATE.pop(m.from_user.id, None)
    _append_event("payment_created", m.from_user.id, {"id":pay_id,"price":price,"sent":sent})

    bot.reply_to(m, f"✅ Վճարման հայտը գրանցվեց №`{pay_id}`։ Ադմինը կհաստատի մոտակայում։", parse_mode="Markdown")

    # notify admins
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("👁 Տեսված",   callback_data=f"pay:seen:{pay_id}"),
        types.InlineKeyboardButton("✅ Հաստատել", callback_data=f"pay:ok:{pay_id}"),
        types.InlineKeyboardButton("❌ Մերժել",   callback_data=f"pay:no:{pay_id}")
    )
    cap = (f"💳 Նոր վճարում #{pay_id}\n"
           f"• From: @{m.from_user.username or m.from_user.id}\n"
           f"• Price: {price}֏ | Sent: {sent}֏\n"
           f"• Overpay→Coupon: {round(max(0, sent-price),2)}֏")
    # try all admin sources we know
    admin_ids = set()
    try:
        admin_ids |= set(int(x) for x in ADMIN_IDS)  # type: ignore
    except: pass
    try:
        admin_ids |= set(int(x) for x in admin_list)  # type: ignore
    except: pass
    try:
        admin_ids.add(int(ADMIN_ID))  # type: ignore
    except: pass
    for aid in admin_ids:
        try:
            if fkind=='photo':   bot.send_photo(aid, fid, caption=cap, reply_markup=kb)
            else:               bot.send_document(aid, fid, caption=cap, reply_markup=kb)
        except: pass

@bot.callback_query_handler(func=lambda q: q.data.startswith("pay:"))
def cb_pay(q):
    if not is_admin(q): 
        bot.answer_callback_query(q.id, "⛔️"); 
        return
    _, act, pid = q.data.split(":")
    d = _pays(); rec = d.get(pid)
    if not rec:
        bot.answer_callback_query(q.id, "Չկա հայտը"); 
        return

    if act=="seen":
        if rec.get("status")=="pending":
            rec["status"]="seen"; _pays_save(d); _append_event("payment_seen", q.from_user.id, {"id":pid})
        bot.answer_callback_query(q.id, "Տեսված 👁"); 
        return

    if act=="ok":
        if rec.get("status") in ("pending","seen"):
            rec["status"]="approved"; _pays_save(d)
            _append_event("payment_approved", q.from_user.id, {"id":pid})
            over = float(rec.get("overpay",0))
            if over>0:
                new_bal = add_coupon(int(rec["user_id"]), over)
                try:
                    bot.send_message(rec["user_id"], f"✅ Վճարումը հաստատվեց (№{pid}). Ավելցուկ {over}֏ → կուպոններ։ Նոր մնացորդ՝ {new_bal}֏.")
                except: pass
            else:
                try:
                    bot.send_message(rec["user_id"], f"✅ Ձեր վճարումը հաստատվեց (№{pid}).")
                except: pass
        bot.answer_callback_query(q.id, "Հաստատվեց ✅"); 
        return

    if act=="no":
        if rec.get("status") in ("pending","seen"):
            rec["status"]="declined"; _pays_save(d)
            _append_event("payment_declined", q.from_user.id, {"id":pid})
            try:
                bot.send_message(rec["user_id"], f"❌ Վճարումը մերժվեց (№{pid}). Կապ հաստատեք օպերատորի հետ։")
            except: pass
        bot.answer_callback_query(q.id, "Մերժվեց ❌"); 
        return

# manual admin confirm (optional fallback)
@bot.message_handler(commands=['confirm_payment'])
def confirm_payment(m):
    if not is_admin(m): return
    parts = m.text.split()
    if len(parts)<4:
        bot.reply_to(m, "Օգտագործում՝ /confirm_payment user_id amount_sent amount_expected")
        return
    try:
        uid = int(parts[1])
        sent = float(parts[2]); expected = float(parts[3])
    except:
        bot.reply_to(m, "Թվերը ճիշտ նշիր․ օրինակ `/confirm_payment 123 1300 1240`")
        return
    over = max(0.0, sent-expected)
    if over>0:
        new_bal = add_coupon(uid, over)
    else:
        new_bal = get_coupon(uid)
    try:
        txt=(f"✅ Ձեր վճարումը հաստատվեց։\n"
             f"📦 Գինը՝ {expected}֏ | 💸 Փոխանցած՝ {sent}֏")
        if over>0: txt+=f"\n🎁 Ավել {over}֏ → կուպոններ։ Նոր մնացորդ՝ {new_bal}֏"
        bot.send_message(uid, txt)
    except: pass
    bot.reply_to(m, f"OK. User {uid} overpay={over}֏, coupons={new_bal}֏")

# quick lists
@bot.message_handler(commands=['payments'])
def list_pending(m):
    if not is_admin(m): return
    d=_pays()
    arr=[v for v in d.values() if v.get("status") in ("pending","seen")]
    arr=sorted(arr, key=lambda x:x["ts"], reverse=True)[:20]
    if not arr:
        bot.reply_to(m, "💳 Սպասող վճարումներ չկան։"); return
    lines=[f"• #{p['id']}  {p['price']}→{p['sent']} (over {p['overpay']})  @{p.get('username') or p['user_id']}" for p in arr]
    bot.reply_to(m, "💳 Վերջին սպասող վճարներ\n"+"\n".join(lines))

# coupons commands
@bot.message_handler(commands=['my_coupons'])
def my_coupons(m):
    bot.reply_to(m, f"🎟 Ձեր կուպոնների մնացորդը՝ {get_coupon(int(m.from_user.id))}֏")

@bot.message_handler(commands=['coupons'])
def admin_coupons(m):
    if not is_admin(m): return
    parts = m.text.split()
    if len(parts)==1:
        bot.reply_to(m, "Օգտագործում՝ `/coupons <user_id> [add X|sub X]`", parse_mode="Markdown"); return
    uid = int(parts[1])
    if len(parts)==2:
        bot.reply_to(m, f"User {uid} → {get_coupon(uid)}֏"); return
    op = parts[2].lower(); amt = float(parts[3])
    if op=="add": nb=add_coupon(uid, amt)
    elif op=="sub": nb=add_coupon(uid, -amt)
    else: bot.reply_to(m, "Օգտագործում՝ add/sub"); return
    bot.reply_to(m, f"OK. User {uid} նոր մնացորդ՝ {nb}֏")

# admin “send receipt” (free message to user)
@bot.message_handler(commands=['send_receipt'])
def admin_send_receipt(m):
    if not is_admin(m): return
    parts = m.text.split(maxsplit=2)
    if len(parts)<3:
        bot.reply_to(m, "Օգտագործում՝ /send_receipt USER_ID ՏԵԿՍՏ")
        return
    try:
        uid=int(parts[1])
    except:
        bot.reply_to(m, "USER_ID-ը թիվ պետք է լինի"); return
    txt = parts[2]
    try:
        bot.send_message(uid, "📩 Ադմինի հաղորդագրություն\n\n"+txt)
        bot.reply_to(m, "✅ Ուղարկվեց")
    except Exception as e:
        bot.reply_to(m, f"Չստացվեց ուղարկել՝ {e}")

# --- stats / dashboard ---
BOT_START_TS = time.time()
def _uptime():
    s=int(time.time()-BOT_START_TS); h=s//3600; m=(s%3600)//60; ss=s%60
    return f"{h:02d}:{m:02d}:{ss:02d}"

def _today_stats():
    s,e=_today_range()
    users_new=0; pay_cnt=0; pay_sum=0.0; over_sum=0.0
    try:
        with open(EVENTS_FILE,"r",encoding="utf-8") as f:
            for line in f:
                j=json.loads(line)
                ts=int(j.get("ts",0))
                if not(s<=ts<e): continue
                k=j.get("kind")
                if k=="user_new": users_new+=1
                elif k=="payment_created":
                    pay_cnt+=1
                    meta=j.get("meta",{})
                    pay_sum += float(meta.get("sent",0))
                    over_sum+= max(0.0, float(meta.get("sent",0)) - float(meta.get("price",0)))
    except: pass
    pend=len([1 for v in _pays().values() if v.get("status") in ("pending","seen")])
    return {"users_new":users_new,"pay_cnt":pay_cnt,"pay_sum":round(pay_sum,2),"over_sum":round(over_sum,2),"pending":pend}

def _admin_kb():
    kb=types.ReplyKeyboardMarkup(resize_keyboard=True,row_width=2)
    kb.add("🧭 Դեշբորդ","💳 Սպասող վճարումներ","📊 Օրվա վիճակագրություն")
    kb.add("📢 Broadcast","📜 Լոգեր","⬅️ Գլխավոր մենյու")
    return kb

@bot.message_handler(commands=['admin'])
def admin_panel(m):
    if not is_admin(m): return
    bot.send_message(m.chat.id,
        f"👑 Admin panel\n• Users: {len(_users())}\n• Uptime: {_uptime()}\n• Data: ./data/",
        reply_markup=_admin_kb())

@bot.message_handler(func=lambda m: is_admin(m) and m.text=="📊 Օրվա վիճակագրություն")
def btn_stats_today(m):
    s=_today_stats()
    bot.reply_to(m,
        f"📊 Այսօր\n• Նոր user-ներ: {s['users_new']}\n• Վճարումներ: {s['pay_cnt']} (գումար {s['pay_sum']}֏)\n"
        f"• Կուպոն ավելացումներ: {s['over_sum']}֏\n• Սպասող վճարումներ: {s['pending']}")

@bot.message_handler(func=lambda m: is_admin(m) and m.text=="💳 Սպասող վճարումներ")
def btn_pending(m): list_pending(m)

@bot.message_handler(func=lambda m: is_admin(m) and m.text=="🧭 Դեշբորդ")
def btn_dash(m):
    s=_today_stats()
    bot.reply_to(m,
        f"🧭 Դեշբորդ\n• Այսօր նոր user: {s['users_new']}\n• Սպասող վճարումներ: {s['pending']}\n"
        f"• Վճարումներ (քանակ/գումար): {s['pay_cnt']} / {s['pay_sum']}֏\n• Կուպոն ավելցուկ: {s['over_sum']}֏\n"
        f"• Ընդհանուր user-ներ: {len(_users())}")

# --- broadcast to all users ---
ADMIN_STATE={}
@bot.message_handler(commands=['broadcast'])
def bc_start(m):
    if not is_admin(m): return
    ADMIN_STATE[m.from_user.id]={"mode":"broadcast"}
    bot.reply_to(m, "✍️ Ուղարկիր հաղորդագրությունը բոլոր user-ներին։ /cancel՝ դադարեցնել")

@bot.message_handler(func=lambda m: is_admin(m) and ADMIN_STATE.get(m.from_user.id,{}).get("mode")=="broadcast",
                     content_types=['text','photo','video','document','audio','voice','sticker'])
def bc_go(m):
    users=_users(); sent=0; fail=0
    for uid in list(users):
        try:
            if   m.content_type=='text': bot.send_message(uid, m.text)
            elif m.content_type=='photo': bot.send_photo(uid, m.photo[-1].file_id, caption=m.caption or "")
            elif m.content_type=='video': bot.send_video(uid, m.video.file_id, caption=m.caption or "")
            elif m.content_type=='document': bot.send_document(uid, m.document.file_id, caption=m.caption or "")
            elif m.content_type=='audio': bot.send_audio(uid, m.audio.file_id, caption=m.caption or "")
            elif m.content_type=='voice': bot.send_voice(uid, m.voice.file_id)
            elif m.content_type=='sticker': bot.send_sticker(uid, m.sticker.file_id)
            sent+=1; time.sleep(0.03)
        except:
            fail+=1
    ADMIN_STATE.pop(m.from_user.id, None)
    bot.reply_to(m, f"📢 Ուղարկվեց՝ {sent}, չհասավ՝ {fail}")

# --- logs dump (last 300) ---
@bot.message_handler(commands=['logs'])
def send_logs(m):
    if not is_admin(m): return
    N=300; lines=[]
    if os.path.exists(EVENTS_FILE):
        with open(EVENTS_FILE,"r",encoding="utf-8") as f: lines=f.readlines()[-N:]
    path=os.path.join(DATA_DIR,"events_last.txt")
    with open(path,"w",encoding="utf-8") as f: f.writelines(lines)
    with open(path,"rb") as f:
        bot.send_document(m.chat.id,f,visible_file_name="events_last.txt",
                          caption=f"Վերջին {len(lines)} իրադարձություն")
# =================== END ADMIN BLOCK ===================
# --- Webhook setup ---
def set_webhook():
    try:
        # remove old
        requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook", timeout=10)

        # set new
        r = requests.get(
            f"https://api.telegram.org/bot{TOKEN}/setWebhook",
            params={"url": WEBHOOK_URL, "drop_pending_updates": True},
            timeout=10,
        )
        print("setWebhook:", r.json())
    except Exception as e:
        print("Webhook error:", e)


# ---- helpers: safe int casting (avoid .isdigit on non-strings) ----
def to_int(val):
    try:
        return int(str(val).strip())
    except Exception:
        return None


# --- Config / Bot ---


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
    cart_timers[user_id] = time.time()   # ← ԱՅՍ ՏՈՂԸ ԴՐԻՐ
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

# --- Persistent customer counter (stored on disk) ---
import os
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)
COUNTER_FILE = os.path.join(DATA_DIR, "customer_counter.txt")

def load_counter():
    try:
        with open(COUNTER_FILE, "r", encoding="utf-8") as f:
            return int(f.read().strip() or "0")
    except Exception:
        return 0

def save_counter(v: int):
    try:
        with open(COUNTER_FILE, "w", encoding="utf-8") as f:
            f.write(str(v))
    except Exception:
        pass

customer_counter = load_counter()

# ================== START + WELCOME (FINAL) ==================

@bot.message_handler(commands=['start'])
def start_handler(m: types.Message):
    # միայն private chat-ում արձագանքենք (խմբում /start-ը չանենք)
    if getattr(m.chat, "type", "") != "private":
        return

    print(f"START from {m.from_user.id}")

    # referral parameter (օր. /start 12345)
    try:
        parts = (m.text or "").strip().split(maxsplit=1)
        if len(parts) == 2 and parts[1].isdigit():
            register_invite(m.from_user.id, int(parts[1]))
    except Exception:
        pass

    # Welcome UI
    try:
        send_welcome(m)
    except Exception as e:
        import traceback
        print("send_welcome ERROR:", e)
        print(traceback.format_exc())     

def send_welcome(message: types.Message):
    # 고객 համար (customer_no) — ապահով աճեցում, եթե ունես counter
    customer_no = 0
    try:
        global customer_counter
        customer_counter += 1
        try:
            save_counter(customer_counter)
        except Exception:
            pass
        customer_no = customer_counter
    except Exception:
        # եթե չունես վերևի counter-ը, փորձի քո helper-ը
        try:
            customer_no = get_next_customer_no()
        except Exception:
            customer_no = 0

    # ---- քո գլխավոր մենյուն
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🛍 Խանութ", "🛒 Զամբյուղ")
    markup.add("📦 Իմ պատվերները", "🎁 Կուպոններ")
    markup.add("🔍 Որոնել ապրանք", "🎡 Բոնուս անիվ")
    markup.add("🧍 Իմ էջը", "🏆 Լավագույններ")
    markup.add("💱 Փոխարկումներ", "💬 Հետադարձ կապ")
    markup.add("Հրավիրել ընկերների")

    # ---- Քո ԱՆՉՓՈԽ ՈՂՋՈՒՅՆԻ ՏԵՔՍՏԸ (ճիշտ 그대로) ----
    welcome_text = (
        "🐰🌸 Բարի գալուստ BabyAngels 🛍️✨\n\n"
        "💖 Շնորհակալ ենք, որ միացել եք մեր սիրելի ընտանիքին ❤️\n"
        f"Դուք այժմ մեր սիրելի հաճախորդն եք №{customer_no} ✨\n"
        "Մեր խանութում կարող եք գտնել ամեն օր օգտակար ապրանքների գծով լավագույն գները։\n\n"
        "🎁 Ակտիվ շանս՝ առաջին գնմանց հետո կստանաք 10% զեղչ հաջորդ պատվերի համար։\n\n"
        "📦 Ի՞նչ կգտնեք այստեղ\n"
        "• Ժամանակին և օգտակար ապրանքներ՝ ամեն օր թարմացվող տեսականիով\n"
        "• Լոյալ ակցիաներ և արագ արձագանք Telegram աջակցությամբ\n"
        "• Հարմարեցված և արագ առաքում 🚚\n\n"
        "💳 Փոխարկման ծառայություններ\n"
        "• PI ➜ USDT (շուկայական կուրս, +20% սպասարկում)\n"
        "• FTN ➜ AMD (միայն 10% սպասարկում)\n"
        "• Alipay լիցքավորում (1 CNY = 58֏)\n\n"
        "✨ Ավելի արագ՝ պարզապես ուղարկեք հարցը ներքևում 👇"
    )

    # ---- ուղարկում լուսանկարով (եթե կա), այլապես՝ տեքստով
    try:
        img_path = os.path.join(os.path.dirname(__file__), "media", "bunny.jpg")
        if os.path.exists(img_path):
            with open(img_path, "rb") as ph:
                bot.send_photo(
                    message.chat.id,
                    ph,
                    caption=welcome_text,
                    reply_markup=markup
                )
        else:
            bot.send_message(message.chat.id, welcome_text, reply_markup=markup)
    except Exception:
        bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

    # ըստ ցանկության՝ առաջին գնումի բոնուս/օգտատիրոջ state
    try:
        if 'ensure_first_order_bonus' in globals():
            ensure_first_order_bonus(message.from_user.id)
    except Exception:
        pass

# ================== /END START + WELCOME ==================

        
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
def start(m):
    # referral (օգտագործում ենք քո արդեն գրած helper-ը)
    __capture_ref__(m)

    # debug ձև, որ տեսնես հասնում է
    _dbg_start(m)

    # welcome UI և մնացածը
    send_welcome(m)

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
    ...
    cart_timers[c.from_user.id] = time.time()  # ← ԱՅՍ ՏՈՂԸ ԴՐԻՐ

    code = c.data.replace("add_", "")
    if code in PRODUCTS:
        user_carts.setdefault(c.from_user.id, {})
        user_carts[c.from_user.id][code] = user_carts[c.from_user.id].get(code, 0) + 1
        cart_timers[c.from_user.id] = time.time()
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
# ========= Admin & Payments – FULL BLOCK (paste below bot = TeleBot(...)) =========

def is_admin(message) -> bool:
    try:
        return int(message.from_user.id) in ADMIN_IDS
    except Exception:
        return False

# --- very small in-memory storage (DB չկա) ---
USERS = {}              # user_id -> dict(name, username, coupons)
COUPONS = {}            # user_id -> coupons_balance (float / int)
PENDING_PAYMENTS = {}   # payment_id -> dict(user_id, price, sent, overpay, note, photo_file_id, status)
EVENTS = []             # լոգերի փոքր պատմություն admin-ի համար
_ID_SEQ = 1000          # payment seq

def _log(event: str):
    EVENTS.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  {event}")
    if len(EVENTS) > 300:
        del EVENTS[:100]

def _register_user(m):
    uid = m.from_user.id
    if uid not in USERS:
        USERS[uid] = {
            "name": f"{m.from_user.first_name or ''} {m.from_user.last_name or ''}".strip(),
            "username": (m.from_user.username or ""),
        }
        COUPONS.setdefault(uid, 0)
        _log(f"👤 New user: {uid} @{USERS[uid]['username']} {USERS[uid]['name']}")

# --- helpers ---
def send_admin(text, **kw):
    for aid in ADMIN_IDS:
        try:
            bot.send_message(aid, text, **kw)
        except Exception:
            pass

# =======================  ADMIN MENU  =======================
@bot.message_handler(commands=['whoami'])
def whoami(message):
    _register_user(message)
    bot.reply_to(message, f"👤 Քո ID-ն՝ `{message.from_user.id}`")

@bot.message_handler(commands=['admin'])
def admin_menu(message):
    if not is_admin(message):
        return
    mk = types.ReplyKeyboardMarkup(resize_keyboard=True)
    mk.add("📊 Վիճակագրություն", "🧾 Վճարումներ")
    mk.add("🎁 Կուպոններ", "🧑‍🤝‍🧑 Օգտատերեր")
    mk.add("🧹 Մաքրել լոգերը", "🗒 Լոգեր (վերջին 30)")
    bot.send_message(
        message.chat.id,
        "👑 Admin Panel — ընտրիր բաժինը",
        reply_markup=mk
    )

@bot.message_handler(func=lambda m: is_admin(m) and m.text == "📊 Վիճակագրություն")
def admin_stats(message):
    users_count = len(USERS)
    pend = sum(1 for p in PENDING_PAYMENTS.values() if p.get("status") == "pending")
    conf = sum(1 for p in PENDING_PAYMENTS.values() if p.get("status") == "confirmed")
    rej  = sum(1 for p in PENDING_PAYMENTS.values() if p.get("status") == "rejected")
    bot.reply_to(message, f"📊 Օգտատերեր՝ {users_count}\n⏳ Սպասման մեջ՝ {pend}\n✅ Հաստատված՝ {conf}\n❌ Մերժված՝ {rej}")

@bot.message_handler(func=lambda m: is_admin(m) and m.text == "🧾 Վճարումներ")
def admin_payments(message):
    if not PENDING_PAYMENTS:
        bot.reply_to(message, "Դատարկ է։")
        return
    lines = []
    for pid, p in sorted(PENDING_PAYMENTS.items()):
        u = USERS.get(p["user_id"], {})
        lines.append(
            f"#{pid} | 👤 {p['user_id']} @{u.get('username','')} {u.get('name','')}\n"
            f"    Գին: {p['price']} | Ուղարկված: {p['sent']} | Overpay: {p.get('overpay',0)}\n"
            f"    Վիճակ: {p['status']}"
        )
    bot.reply_to(message, "🧾 Վճարումներ\n" + "\n".join(lines[:30]))

@bot.message_handler(func=lambda m: is_admin(m) and m.text == "🎁 Կուպոններ")
def admin_coupons(message):
    if not COUPONS:
        bot.reply_to(message, "Ոչ մի կուպոն դեռ չկա։")
        return
    lines = [f"👤 {uid}: {bal}" for uid, bal in COUPONS.items()]
    bot.reply_to(message, "🎁 Կուպոնների մնացորդներ\n" + "\n".join(lines[:50]))

@bot.message_handler(func=lambda m: is_admin(m) and m.text == "🧑‍🤝‍🧑 Օգտատերեր")
def admin_users(message):
    if not USERS:
        bot.reply_to(message, "Օգտատերեր դեռ չեն եղել։")
        return
    lines = [f"{uid} @{u.get('username','')} {u.get('name','')}" for uid,u in USERS.items()]
    bot.reply_to(message, "🧑‍🤝‍🧑 Օգտատերեր\n" + "\n".join(lines[:50]))

@bot.message_handler(func=lambda m: is_admin(m) and m.text == "🧹 Մաքրել լոգերը")
def admin_clear_logs(message):
    EVENTS.clear()
    bot.reply_to(message, "Լոգերը մաքրվեցին։")

@bot.message_handler(func=lambda m: is_admin(m) and m.text == "🗒 Լոգեր (վերջին 30)")
def admin_last_logs(message):
    if not EVENTS:
        bot.reply_to(message, "Լոգերը դատարկ են։")
        return
    bot.reply_to(message, "Վերջին իրադարձությունները:\n" + "\n".join(EVENTS[-30:]))

# =======================  USER COUPONS  =======================
@bot.message_handler(commands=['my_coupons'])
def my_coupons(message):
    _register_user(message)
    bal = COUPONS.get(message.from_user.id, 0)
    bot.reply_to(message, f"🎁 Քո կուպոնների մնացորդը՝ **{bal}**")

# =======================  PAYMENT FLOW  =======================
# /pay → enter price → enter sent amount → upload receipt (photo) → admin gets buttons
PAY_FLOW = {}  # uid -> {"stage": "...", "price": , "sent": , "note": ""}

@bot.message_handler(commands=['pay'])
def cmd_pay(message):
    _register_user(message)
    PAY_FLOW[message.from_user.id] = {"stage": "price"}
    bot.reply_to(message, "💳 Նշիր ապրանքի գինը (AMD)՝ օրինակ `1240`")

@bot.message_handler(func=lambda m: m.from_user.id in PAY_FLOW and PAY_FLOW[m.from_user.id]["stage"] == "price")
def flow_get_price(message):
    try:
        price = float(str(message.text).strip())
        PAY_FLOW[message.from_user.id]  # intentional error? NO! fix
    except Exception:
        bot.reply_to(message, "Թիվ գրի, օրինակ `1240`")
        return
    PAY_FLOW[message.from_user.id]["price"] = price
    PAY_FLOW[message.from_user.id]["stage"] = "sent"
    bot.reply_to(message, "✉️ Գրիր՝ իրականում որքան ես փոխանցել (AMD)՝ օրինակ `1300`։\nԿարող ես նաև տեքստով նշել հաշվի ստացող/պլատֆորմը։")

@bot.message_handler(func=lambda m: m.from_user.id in PAY_FLOW and PAY_FLOW[m.from_user.id]["stage"] == "sent")
def flow_get_sent(message):
    # պահում ենք նաև user's note-ը
    txt = str(message.text)
    nums = "".join(ch if ch.isdigit() or ch == "." else " " for ch in txt).split()
    if not nums:
        bot.reply_to(message, "Գրիր թիվը՝ օրինակ `1300`")
        return
    sent = float(nums[0])
    PAY_FLOW[message.from_user.id]["sent"] = sent
    # մնացածը՝ որպես նշում
    note = txt if len(nums) == 1 else txt.replace(nums[0], "", 1).strip()
    PAY_FLOW[message.from_user.id]["note"] = note
    PAY_FLOW[message.from_user.id]["stage"] = "wait_receipt"
    bot.reply_to(message, "📸 Ուղարկիր փոխանցման անդորագրի ՍՔՐԻՆ/ԼՈՒՍԱՆԿԱՐԸ (photo)")

@bot.message_handler(content_types=['photo'])
def on_photo(message):
    uid = message.from_user.id
    if uid not in PAY_FLOW or PAY_FLOW[uid].get("stage") != "wait_receipt":
        # Եթե սա անդորագիր չի, պարզապես գրանցենք user-ը ու դուրս գանք
        _register_user(message)
        return

    # պահենք file_id-ը
    file_id = message.photo[-1].file_id
    data = PAY_FLOW[uid]
    price = data["price"]
    sent  = data["sent"]
    over  = max(0, sent - price)
    note  = data.get("note", "")

    global _ID_SEQ
    _ID_SEQ += 1
    pid = _ID_SEQ

    PENDING_PAYMENTS[pid] = {
        "user_id": uid,
        "price": price,
        "sent": sent,
        "overpay": over,
        "note": note,
        "photo_file_id": file_id,
        "status": "pending",
        "created_at": datetime.now().isoformat(timespec="seconds")
    }
    del PAY_FLOW[uid]

    # ուղարկենք ադմիններին հաստատման կոճակներով
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton(text="✅ Հաստատել", callback_data=f"pay_ok:{pid}"),
        types.InlineKeyboardButton(text="❌ Մերժել",  callback_data=f"pay_no:{pid}")
    )
    u = USERS.get(uid, {})
    caption = (
        f"🧾 Վճարման անդորագիր #{pid}\n"
        f"👤 {uid} @{u.get('username','')} {u.get('name','')}\n"
        f"Գին: {price} | Ուղարկված: {sent} | Overpay: {over}\n"
        f"Նշում: {note or '—'}"
    )
    for aid in ADMIN_IDS:
        try:
            bot.send_photo(aid, file_id, caption=caption, reply_markup=kb)
        except Exception:
            pass

    bot.reply_to(message, f"✅ Անդորագիրը ուղարկվեց ադմինին։ Հաստատման սպասում… (#`{pid}`)")
    _log(f"🧾 Payment #{pid} from {uid}: price={price} sent={sent} over={over}")

@bot.callback_query_handler(func=lambda c: c.data and (c.data.startswith("pay_ok:") or c.data.startswith("pay_no:")))
def on_payment_decision(call):
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "Միայն ադմինի համար է։", show_alert=True)
        return
    action, raw = call.data.split(":", 1)
    pid = int(raw)
    payment = PENDING_PAYMENTS.get(pid)
    if not payment:
        bot.answer_callback_query(call.id, "Գործարքը չի գտնվել։", show_alert=True)
        return

    if action == "pay_ok":
        payment["status"] = "confirmed"
        over = float(payment.get("overpay", 0))
        if over > 0:
            COUPONS[payment["user_id"]] = COUPONS.get(payment["user_id"], 0) + over
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=call.message.caption + "\n\n✅ ՀԱՍՏԱՏՎԱԾ",
            reply_markup=None
        )
        # user-ին ծանուցում
        try:
            bot.send_message(payment["user_id"], f"✅ Քո վճարումը #`{pid}` հաստատվեց։ Overpay **{over}** → կուպոնների վրա։")
        except Exception:
            pass
        _log(f"✅ Confirm #{pid} by admin {call.from_user.id}; over={over}")
        bot.answer_callback_query(call.id, "Հաստատվեց ✅")

    elif action == "pay_no":
        payment["status"] = "rejected"
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=call.message.caption + "\n\n❌ ՄԵՐԺՎԱԾ",
            reply_markup=None
        )
        try:
            bot.send_message(payment["user_id"], f"❌ Քո վճարումը #`{pid}` մերժվեց։ Խնդրում ենք կրկին ստուգել տվյալները։")
        except Exception:
            pass
        _log(f"❌ Reject #{pid} by admin {call.from_user.id}")
        bot.answer_callback_query(call.id, "Մերժվեց ❌")

# =======================  SIMPLE WEB ADMIN PAGES  =======================
@app.route("/admin")
def admin_panel():
    pend = sum(1 for p in PENDING_PAYMENTS.values() if p.get("status") == "pending")
    conf = sum(1 for p in PENDING_PAYMENTS.values() if p.get("status") == "confirmed")
    rej  = sum(1 for p in PENDING_PAYMENTS.values() if p.get("status") == "rejected")
    return f"""
    <h1>👑 BabyAngelsBot · Admin Panel</h1>
    <p>Users: {len(USERS)} | Pending: {pend} | Confirmed: {conf} | Rejected: {rej}</p>
    <ul>
        <li><a href='/admin/payments'>🧾 Վճարումներ</a></li>
        <li><a href='/admin/coupons'>🎁 Կուպոններ</a></li>
        <li><a href='/admin/users'>🧑‍🤝‍🧑 Օգտատերեր</a></li>
        <li><a href='/admin/logs'>🗒 Լոգեր</a></li>
    </ul>
    """

@app.route("/admin/payments")
def web_payments():
    rows = []
    for pid, p in sorted(PENDING_PAYMENTS.items()):
        rows.append(
            f"<tr><td>#{pid}</td>"
            f"<td>{p['user_id']}</td>"
            f"<td>{p['price']}</td><td>{p['sent']}</td><td>{p.get('overpay',0)}</td>"
            f"<td>{p['status']}</td><td>{p.get('created_at','')}</td></tr>"
        )
    body = "".join(rows) or "<tr><td colspan=7>Դատարկ է</td></tr>"
    return f"<h2>🧾 Վճարումներ</h2><table border=1 cellpadding=6><tr><th>ID</th><th>User</th><th>Price</th><th>Sent</th><th>Over</th><th>Status</th><th>Time</th></tr>{body}</table>"

@app.route("/admin/coupons")
def web_coupons():
    rows = [f"<tr><td>{uid}</td><td>{bal}</td></tr>" for uid, bal in COUPONS.items()]
    body = "".join(rows) or "<tr><td colspan=2>Դատարկ է</td></tr>"
    return f"<h2>🎁 Կուպոններ</h2><table border=1 cellpadding=6><tr><th>User</th><th>Balance</th></tr>{body}</table>"

@app.route("/admin/users")
def web_users():
    rows = []
    for uid, u in USERS.items():
        rows.append(f"<tr><td>{uid}</td><td>@{u.get('username','')}</td><td>{u.get('name','')}</td><td>{COUPONS.get(uid,0)}</td></tr>")
    body = "".join(rows) or "<tr><td colspan=4>Դատարկ է</td></tr>"
    return f"<h2>🧑‍🤝‍🧑 Օգտատերեր</h2><table border=1 cellpadding=6><tr><th>User</th><th>Username</th><th>Name</th><th>Coupons</th></tr>{body}</table>"

@app.route("/admin/logs")
def web_logs():
    body = "<br>".join(EVENTS[-200:]) if EVENTS else "Դատարկ է"
    return f"<h2>🗒 Վերջին իրադարձություններ</h2><div style='white-space:pre-wrap;font-family:monospace'>{body}</div>"

# ========= /END of Admin & Payments FULL BLOCK =========

# 👤 Հաճախորդներ
# --- Flask routes ---
@app.route("/", methods=["GET"])
def index():
    return "Bot is running!", 200

# --- Webhook route (մնած, եթե Render-ում պետք գա) ---
@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        json_str = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return "", 200
    else:
        abort(403)

print("Bot started successfully")

# --- Simple test commands (մի հատ /start թող՝ եթե ունես send_welcome վերը, դա comment կամ հանի՛ր) ---
@bot.message_handler(commands=['id'])
def _id(m):
    bot.send_message(m.chat.id, f"🆔 Your ID: {m.from_user.id}")

@bot.message_handler(content_types=['text','photo','sticker','video','document','audio','voice'])
def _catch_all(m):
    if getattr(m, "entities", None) and any(e.type == "bot_command" for e in m.entities):
     return
    if m.content_type == 'text':
        bot.send_message(m.chat.id, f"📥 got: {m.text[:50]}")
    else:
        bot.send_message(m.chat.id, f"📥 got {m.content_type}")
def start_cart_reminder():
    def check():
        while True:
            now = time.time()
            for uid, t0 in list(cart_timers.items()):
                if now - t0 >= 24*3600:
                    try:
                        bot.send_message(uid, "🛒 Ձեր զամբյուղը սպասում է ձեզ 😊 Պատվերը ավարտե՛ք, իսկ հարցերի դեպքում գրե՛ք մեզ։")
                    except:
                        pass
                    cart_timers.pop(uid, None)
            time.sleep(3600)
    threading.Thread(target=check, daemon=True).start()
start_cart_reminder()

if __name__ == "__main__":
    bot.delete_webhook(drop_pending_updates=True)
    print("Bot started successfully")
    bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=20)


