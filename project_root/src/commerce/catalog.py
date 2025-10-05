from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import random

# ===== ABSOLUTE PATHS (քո կառուցվածքի համաձայն) =====
# project_root/      -> C:\StarLegenBot\project_root
# արտաքին media/     -> C:\StarLegenBot\media
PROJECT_ROOT      = Path(__file__).resolve().parents[2]
MEDIA_DIR         = (PROJECT_ROOT.parent / "media").resolve()   # << ԱՐՏԱՔԻՆ media
PRODUCT_IMG_DIR   = (MEDIA_DIR / "PRODUCT").resolve()           # << Քո պանակը՝ PRODUCT (մեծատառ)

# ---------- Data: Categories / Subcategories ----------
_CATEGORIES = {
    "hy": [
        ("carpets", "🧶 Գորգեր"),
        ("auto",    "🚗 Ավտո"),
        ("women",   "👗 Կանացի"),
        ("men",     "👕 Տղամարդու"),
        ("kids",    "👶 Մանկական"),
    ],
    "ru": [
        ("carpets", "🧶 Ковры"),
        ("auto",    "🚗 Авто"),
        ("women",   "👗 Женские"),
        ("men",     "👕 Мужские"),
        ("kids",    "👶 Детские"),
    ],
    "en": [
        ("carpets", "🧶 Carpets"),
        ("auto",    "🚗 Auto"),
        ("women",   "👗 Women"),
        ("men",     "👕 Men"),
        ("kids",    "👶 Kids"),
    ],
}

_SUBCATS = {
    "carpets": ["home"],
    "auto":    ["vacuum"],
    "women":   ["tshirt", "leggings", "tights", "socks", "underwear", "nightwear"],
    "men":     ["tshirt", "underwear"],
    "kids":    ["tshirt", "socks"],
}

_SUBCAT_TITLES = {
    "hy": {
        ("carpets","home"):      "🏠 Տան համար",
        ("auto","vacuum"):       "🧹 Փոշեկուլ",
        ("women","tshirt"):      "👚 Շապիկներ",
        ("women","leggings"):    "🩳 Բանտաժներ (լեգինս)",
        ("women","tights"):      "🧦 Զուգագուլպաներ",
        ("women","socks"):       "🧦 Գուլպաներ",
        ("women","underwear"):   "🩲 Ներքնազգեստ",
        ("women","nightwear"):   "🌙 Գիշերազգեստ",
        ("men","tshirt"):        "👕 Շապիկներ",
        ("men","underwear"):     "🩲 Ներքնազգեստ",
        ("kids","tshirt"):       "👕 Շապիկներ",
        ("kids","socks"):        "🧦 Գուլպաներ",
    },
    "ru": {
        ("carpets","home"):      "🏠 Для дома",
        ("auto","vacuum"):       "🧹 Пылесос",
        ("women","tshirt"):      "👚 Футболки",
        ("women","leggings"):    "🩳 Леггинсы",
        ("women","tights"):      "🧦 Колготки",
        ("women","socks"):       "🧦 Носки",
        ("women","underwear"):   "🩲 Бельё",
        ("women","nightwear"):   "🌙 Ночнушки",
        ("men","tshirt"):        "👕 Футболки",
        ("men","underwear"):     "🩲 Трусы",
        ("kids","tshirt"):       "👕 Футболки",
        ("kids","socks"):        "🧦 Носки",
    },
    "en": {
        ("carpets","home"):      "🏠 For Home",
        ("auto","vacuum"):       "🧹 Vacuum",
        ("women","tshirt"):      "👚 T-Shirts",
        ("women","leggings"):    "🩳 Leggings",
        ("women","tights"):      "🧦 Tights",
        ("women","socks"):       "🧦 Socks",
        ("women","underwear"):   "🩲 Underwear",
        ("women","nightwear"):   "🌙 Nightwear",
        ("men","tshirt"):        "👕 T-Shirts",
        ("men","underwear"):     "🩲 Underwear",
        ("kids","tshirt"):       "👕 T-Shirts",
        ("kids","socks"):        "🧦 Socks",
    },
}

# Map (cat_id, sub_id) -> list of product IDs
_PROD_INDEX = {
    ("carpets","home"): ["P001","P013","P014","P015","P016","P017","P018","P019","P020","P021"],
    ("auto","vacuum"):  ["P002"],
    ("women","tshirt"): ["P003"],
    ("women","leggings"): ["P005"],
    ("women","tights"): ["P006"],
    ("women","socks"): ["P007"],
    ("women","underwear"): ["P009"],
    ("women","nightwear"): ["P010"],
    ("men","tshirt"): ["P004"],
    ("men","underwear"): ["P008"],
    ("kids","tshirt"): ["P011"],
    ("kids","socks"): ["P012"],
}

# ---------- Products ----------
PRODUCTS: Dict[str, Dict] = {
    # --- Rugs P001 + P013..P021 (all 40×60, 3250 → 1690) ---
    "P001": {
        "code": "BA100810",
        "title": {"hy":"Գորգ №1","ru":"Ковёр №1","en":"Carpet #1"},
        "short": {"hy":"Չսահող հիմք • Հեշտ մաքրում • 40×60 սմ",
                  "ru":"Анти-скольз. основа • Лёгкий уход • 40×60 см",
                  "en":"Anti-slip base • Easy care • 40×60 cm"},
        "long": {
            "hy":"• Բարձր հյուսվածք…\n• Չափ՝ 40×60 սմ • Առաքում՝ 14 օր\n• Կոդ՝ BA100810",
            "ru":"• Высокая плотность…\n• 40×60 см • Доставка 14 дней\n• Код: BA100810",
            "en":"• High pile density…\n• Size 40×60 cm • Delivery 14d\n• Code: BA100810",
        },
        "price_new": 1690, "price_old": 3250,
        "best_seller": True, "stock": 12,
        "badges": ["Premium","Eco"],
        "variants": ["40×60"],
        "video": None,
        "images": [
            str(PRODUCT_IMG_DIR/"rugs"/"BA100810.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"advantages.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"interior.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"layers.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"absorb.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"care.jpg"),
        ],
    },

    "P013": {
        "code":"BA100811",
        "title":{"hy":"Գորգ №2","ru":"Ковёр №2","en":"Carpet #2"},
        "short":{"hy":"Փափուկ քայլք • Արագ մաքրում • 40×60",
                 "ru":"Мягкий шаг • Быстрый уход • 40×60",
                 "en":"Soft step • Quick clean • 40×60"},
        "long":{
            "hy":"• Միկրոֆիբրա…\n• Կոդ՝ BA100811",
            "ru":"• Микрофибра…\n• Код: BA100811",
            "en":"• Microfiber…\n• Code: BA100811",
        },
        "price_new": 1690, "price_old": 3250,
        "best_seller": True, "stock": 11,
        "badges":["Eco"], "variants":["40×60"], "video": None,
        "images":[
            str(PRODUCT_IMG_DIR/"rugs"/"BA100811.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"advantages.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"interior.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"layers.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"absorb.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"care.jpg"),
        ],
    },

    "P014": {
        "code":"BA100812",
        "title":{"hy":"Գորգ №3","ru":"Ковёр №3","en":"Carpet #3"},
        "short":{"hy":"Դիմացկուն մանրաթել • 40×60",
                 "ru":"Прочное волокно • 40×60",
                 "en":"Resilient fiber • 40×60"},
        "long":{
            "hy":"• Խիտ, էլաստիկ մանրաթել…\n• Կոդ՝ BA100812",
            "ru":"• Плотное, упругое волокно…\n• Код: BA100812",
            "en":"• Dense, resilient fiber…\n• Code: BA100812",
        },
        "price_new": 1690, "price_old": 3250,
        "best_seller": False, "stock": 13,
        "badges":["Premium"], "variants":["40×60"], "video": None,
        "images":[
            str(PRODUCT_IMG_DIR/"rugs"/"BA100812.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"advantages.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"interior.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"layers.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"absorb.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"care.jpg"),
        ],
    },

    "P015": {
        "code":"BA100813",
        "title":{"hy":"Գորգ №4","ru":"Ковёр №4","en":"Carpet #4"},
        "short":{"hy":"Հակասահող հիմք • 40×60","ru":"Антискользящая основа • 40×60","en":"Anti-slip base • 40×60"},
        "long":{
            "hy":"• Մանրաթելերի խիտ հյուսք…\n• Կոդ՝ BA100813",
            "ru":"• Плотное переплетение…\n• Код: BA100813",
            "en":"• Dense weave…\n• Code: BA100813",
        },
        "price_new": 1690, "price_old": 3250,
        "best_seller": False, "stock": 15,
        "badges":["Eco"], "variants":["40×60"], "video": None,
        "images":[
            str(PRODUCT_IMG_DIR/"rugs"/"BA100813.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"advantages.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"interior.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"layers.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"absorb.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"care.jpg"),
        ],
    },

    "P016": {
        "code":"BA100814",
        "title":{"hy":"Գորգ №5","ru":"Ковёр №5","en":"Carpet #5"},
        "short":{"hy":"Փոշին չի կպչում • 40×60","ru":"Меньше пыли • 40×60","en":"Low dust • 40×60"},
        "long":{
            "hy":"• Միկրոֆիբրա…\n• Կոդ՝ BA100814",
            "ru":"• Микрофибра…\n• Код: BA100814",
            "en":"• Microfiber…\n• Code: BA100814",
        },
        "price_new": 1690, "price_old": 3250,
        "best_seller": False, "stock": 17, "badges":[], "variants":["40×60"], "video": None,
        "images":[
            str(PRODUCT_IMG_DIR/"rugs"/"BA100814.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"advantages.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"interior.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"layers.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"absorb.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"care.jpg"),
        ],
    },

    "P017": {
        "code":"BA100815",
        "title":{"hy":"Գորգ №6","ru":"Ковёр №6","en":"Carpet #6"},
        "short":{"hy":"Հեշտ մաքրում • 40×60","ru":"Лёгкий уход • 40×60","en":"Easy care • 40×60"},
        "long":{
            "hy":"• Բազմաշերտ հիմք…\n• Կոդ՝ BA100815",
            "ru":"• Многослойная основа…\n• Код: BA100815",
            "en":"• Multi-layer base…\n• Code: BA100815",
        },
        "price_new": 1690, "price_old": 3250,
        "best_seller": False, "stock": 16, "badges":["Premium"], "variants":["40×60"], "video": None,
        "images":[
            str(PRODUCT_IMG_DIR/"rugs"/"BA100815.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"advantages.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"interior.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"layers.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"absorb.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"care.jpg"),
        ],
    },

    "P018": {
        "code":"BA100816",
        "title":{"hy":"Գորգ №7","ru":"Ковёр №7","en":"Carpet #7"},
        "short":{"hy":"Շնչող կառուցվածք • 40×60","ru":"Дышащая структура • 40×60","en":"Breathable • 40×60"},
        "long":{
            "hy":"• Շնչող հիմք…\n• Կոդ՝ BA100816",
            "ru":"• Дышащая основа…\n• Код: BA100816",
            "en":"• Breathable base…\n• Code: BA100816",
        },
        "price_new": 1690, "price_old": 3250,
        "best_seller": False, "stock": 18, "badges":[], "variants":["40×60"], "video": None,
        "images":[
            str(PRODUCT_IMG_DIR/"rugs"/"BA100816.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"advantages.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"interior.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"layers.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"absorb.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"care.jpg"),
        ],
    },

    "P019": {
        "code":"BA100817",
        "title":{"hy":"Գորգ №8","ru":"Ковёр №8","en":"Carpet #8"},
        "short":{"hy":"Դիմացկուն • 40×60","ru":"Прочный • 40×60","en":"Durable • 40×60"},
        "long":{
            "hy":"• Խիտ հյուսք…\n• Կոդ՝ BA100817",
            "ru":"• Плотное плетение…\n• Код: BA100817",
            "en":"• Dense weave…\n• Code: BA100817",
        },
        "price_new": 1690, "price_old": 3250,
        "best_seller": False, "stock": 14, "badges":["Eco"], "variants":["40×60"], "video": None,
        "images":[
            str(PRODUCT_IMG_DIR/"rugs"/"BA100817.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"advantages.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"interior.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"layers.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"absorb.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"care.jpg"),
        ],
    },

    "P020": {
        "code":"BA100818",
        "title":{"hy":"Գորգ №9","ru":"Ковёр №9","en":"Carpet #9"},
        "short":{"hy":"Օրական օգտագործում • 40×60","ru":"На каждый день • 40×60","en":"Everyday use • 40×60"},
        "long":{
            "hy":"• Օպտիմալ հաստություն…\n• Կոդ՝ BA100818",
            "ru":"• Оптимальная толщина…\n• Код: BA100818",
            "en":"• Optimal thickness…\n• Code: BA100818",
        },
        "price_new": 1690, "price_old": 3250,
        "best_seller": False, "stock": 12, "badges":[], "variants":["40×60"], "video": None,
        "images":[
            str(PRODUCT_IMG_DIR/"rugs"/"BA100818.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"advantages.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"interior.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"layers.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"absorb.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"care.jpg"),
        ],
    },

    "P021": {
        "code":"BA100819",
        "title":{"hy":"Գորգ №10","ru":"Ковёр №10","en":"Carpet #10"},
        "short":{"hy":"Տնային ինտերիեր • 40×60","ru":"Для интерьера • 40×60","en":"Home interior • 40×60"},
        "long":{
            "hy":"• Ժամանակակից կառուցվածք…\n• Կոդ՝ BA100819",
            "ru":"• Современная структура…\n• Код: BA100819",
            "en":"• Modern construction…\n• Code: BA100819",
        },
        "price_new": 1690, "price_old": 3250,
        "best_seller": False, "stock": 10, "badges":["Premium"], "variants":["40×60"], "video": None,
        "images":[
            str(PRODUCT_IMG_DIR/"rugs"/"BA100819.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"advantages.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"interior.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"layers.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"absorb.jpg"),
            str(PRODUCT_IMG_DIR/"shared"/"care.jpg"),
        ],
    },

    # --- Auto P002 (video + images) ---
    "P002": {
        "code": "AUTO-VAC01",
        "title": {"hy":"Ավտո փոշեկուլ • TurboClean","ru":"Авто-пылесос • TurboClean","en":"Car Vacuum • TurboClean"},
        "short": {"hy":"Ուժեղ քաշող ուժ • USB-C","ru":"Мощное всасывание • USB-C","en":"Strong suction • USB-C"},
        "long": {
            "hy":"• 120W շարժիչ…\n• Վերադարձ՝ 14 օր • Կոդ՝ AUTO-VAC01",
            "ru":"• Мотор 120W…\n• Возврат 14 дней • Код: AUTO-VAC01",
            "en":"• 120W motor…\n• 14-day returns • Code: AUTO-VAC01",
        },
        "price_new": 16900, "price_old": 19900,
        "best_seller": True, "stock": 34, "badges": ["Hot","Premium"],
        "variants": ["Black","White"],
        "video": str(PRODUCT_IMG_DIR/"car_cleaner"/"video.mp4"),
        "images": [
            str(PRODUCT_IMG_DIR/"car_cleaner"/"CAR001_1.jpg"),
            str(PRODUCT_IMG_DIR/"car_cleaner"/"CAR001_2.jpg"),
            str(PRODUCT_IMG_DIR/"car_cleaner"/"CAR001_3.jpg"),
            str(PRODUCT_IMG_DIR/"car_cleaner"/"CAR001_4.jpg"),
            str(PRODUCT_IMG_DIR/"car_cleaner"/"CAR001_5.jpg"),
        ],
    },

    # --- Women T-shirt P003 (sizes+colors) ---
    "P003": {
        "code": "wtsh-001",
        "title": {"hy":"Կանացի շապիկ • Cotton Premium","ru":"Женская футболка • Cotton Premium","en":"Women T-Shirt • Cotton Premium"},
        "short": {"hy":"100% բամբակ • S–3XL • 6 գույն","ru":"100% хлопок • S–3XL • 6 цветов","en":"100% cotton • S–3XL • 6 colors"},
        "long": {
            "hy":"• Բարձրորակ 100% բամբակ…\n• Կոդ՝ wtsh-001",
            "ru":"• 100% хлопок премиум…\n• Код: wtsh-001",
            "en":"• Premium 100% cotton…\n• Code: wtsh-001",
        },
        "price_new": 7900, "price_old": 9500,
        "best_seller": True, "stock": 28, "badges": ["Premium"],
        "variants": ["S","M","L","XL","2XL","3XL","⚪️","⚫️","🩶","🟥","🟦","🟩"],
        "video": None,
        "images": [
            str(PRODUCT_IMG_DIR/"women"/"wtsh-001_1.jpg"),
            str(PRODUCT_IMG_DIR/"women"/"wtsh-001_2.jpg"),
            str(PRODUCT_IMG_DIR/"women"/"wtsh-001_3.jpg"),
            str(PRODUCT_IMG_DIR/"women"/"wtsh-001_4.jpg"),
            str(PRODUCT_IMG_DIR/"women"/"wtsh-001_5.jpg"),
        ],
    },
}

# ---------- Fake Metrics (sold/likes/ratings) ----------
_SOLD   : Dict[str, int] = {}
_LIKES  : Dict[str, int] = {}
_RATING : Dict[str, Tuple[int,int]] = {}  # pid -> (sum_stars, count)

def _init_metrics(pid: str):
    if pid not in _SOLD:
        _SOLD[pid] = random.randint(120, 380)
    if pid not in _LIKES:
        _LIKES[pid] = random.randint(30, 150)
    if pid not in _RATING:
        _RATING[pid] = (random.randint(15, 25)*4, random.randint(4, 6))  # sum,count

# ---------- Public API ----------
def categories(lang: str) -> List[Tuple[str,str]]:
    return _CATEGORIES.get(lang, _CATEGORIES["hy"])

def subcategories(lang: str, cat_id: str) -> List[Tuple[str,str]]:
    ids = _SUBCATS.get(cat_id, [])
    out = []
    for sid in ids:
        title = _SUBCAT_TITLES.get(lang, _SUBCAT_TITLES["hy"]).get((cat_id, sid))
        if title:
            out.append((sid, title))
    return out

def products(lang: str, cat_id: str, sub_id: str) -> List[Tuple[str,str]]:
    ids = _PROD_INDEX.get((cat_id, sub_id), [])
    out = []
    for pid in ids:
        p = PRODUCTS.get(pid, {})
        title = p.get("title", {}).get(lang) or p.get("title", {}).get("hy") or pid
        out.append((pid, title))
    return out

def product_data(pid: str, lang: str) -> Optional[Dict]:
    p = PRODUCTS.get(pid)
    if not p: return None
    _init_metrics(pid)
    return {
        "pid": pid,
        "code": p["code"],
        "title": p["title"].get(lang) or p["title"]["hy"],
        "short": p["short"].get(lang) or p["short"]["hy"],
        "long":  p["long"].get(lang)  or p["long"]["hy"],
        "price_new": p["price_new"],
        "price_old": p["price_old"],
        "best_seller": p["best_seller"],
        "stock": p["stock"],
        "badges": p.get("badges", []),
        "variants": p.get("variants", []),
        "video": p.get("video"),
        "images": p.get("images", []),
        "sold": _SOLD[pid],
        "likes": _LIKES[pid],
        "rating_avg": (_RATING[pid][0] / max(1,_RATING[pid][1])),
        "rating_count": _RATING[pid][1],
    }

def _discount_percent(p_old: int, p_new: int) -> int:
    if not p_old or p_old <= p_new: return 0
    return int(round((p_old - p_new) * 100.0 / p_old))

def product_caption(pid: str, lang: str) -> str:
    p = product_data(pid, lang)
    if not p: return ""
    disc = _discount_percent(p["price_old"], p["price_new"])
    badges = " • ".join(p["badges"]) if p["badges"] else ""
    avg = p["rating_avg"]
    stars = "⭐" * int(round(min(5, max(1, avg))))
    texts = {
        "hy": (
            f"*{p['title']}*  \n"
            f"🏷️ Կոդ՝ {p['code']}\n"
            f"✔️ {p['short']}\n"
            f"❌ Հին գին՝ {p['price_old']:,}֏  |  ✅ Նոր՝ *{p['price_new']:,}֏*  ({disc}%)\n"
            f"📊 Վաճառված՝ {p['sold']} • ❤️ {p['likes']} • {stars} ({p['rating_count']})\n"
            f"{'🏅 ' + badges if badges else ''}"
        ),
        "ru": (
            f"*{p['title']}*  \n"
            f"🏷️ Код: {p['code']}\n"
            f"✔️ {p['short']}\n"
            f"❌ Старая: {p['price_old']:,}֏  |  ✅ Новая: *{p['price_new']:,}֏*  ({disc}%)\n"
            f"📊 Продано: {p['sold']} • ❤️ {p['likes']} • {stars} ({p['rating_count']})\n"
            f"{'🏅 ' + badges if badges else ''}"
        ),
        "en": (
            f"*{p['title']}*  \n"
            f"🏷️ Code: {p['code']}\n"
            f"✔️ {p['short']}\n"
            f"❌ Old: {p['price_old']:,}֏  |  ✅ New: *{p['price_new']:,}֏*  ({disc}%)\n"
            f"📊 Sold: {p['sold']} • ❤️ {p['likes']} • {stars} ({p['rating_count']})\n"
            f"{'🏅 ' + badges if badges else ''}"
        ),
    }
    return texts.get(lang, texts["hy"])

def product_long(pid: str, lang: str) -> str:
    p = PRODUCTS.get(pid)
    if not p: return ""
    return p["long"].get(lang) or p["long"]["hy"]

def gallery_len(pid: str) -> int:
    p = PRODUCTS.get(pid, {})
    imgs = p.get("images", []) or []
    vid  = p.get("video")
    return len(imgs) + (1 if vid else 0)

def slide_info(pid: str, idx: int) -> Tuple[str, str]:
    p = PRODUCTS.get(pid, {})
    vid = p.get("video")
    imgs = p.get("images", []) or []
    if vid:
        if idx == 0:
            return "video", vid
        return "image", imgs[(idx-1) % max(1, len(imgs))] if imgs else ("image","")
    return "image", imgs[idx % max(1, len(imgs))] if imgs else ("image","")

def inc_sales(pid: str, best_seller: bool=False):
    _init_metrics(pid)
    bump = random.randint(10, 100) + (2 if best_seller else 0)
    _SOLD[pid] += bump
    if pid in PRODUCTS:
        PRODUCTS[pid]["stock"] = max(0, PRODUCTS[pid]["stock"] - max(0, bump // 50))

def inc_like(pid: str):
    _init_metrics(pid)
    _LIKES[pid] += 1

def rate(pid: str, stars: int):
    _init_metrics(pid)
    stars = max(1, min(5, int(stars)))
    s, c = _RATING[pid]
    _RATING[pid] = (s + stars, c + 1)
def get_product(pid: str, lang: str) -> Optional[Dict]:
    """Պարզ հարմարեցված view՝ Cart/Checkout PU-երի համար."""
    p = PRODUCTS.get(pid)
    if not p:
        return None
    title = p["title"].get(lang) or p["title"]["hy"]
    imgs = p.get("images") or []
    return {
        "sku": pid,
        "name": title,
        "price": float(p.get("price_new", 0)),
        "thumb": imgs[0] if imgs else None,
    }
