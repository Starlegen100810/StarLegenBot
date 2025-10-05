from telebot import types

LANGS = ["hy", "ru", "en"]

# Քո երկար ողջույնը՝ HY (ինչպես ուղարկել ես), + իմ համարժեք RU/EN
WELCOME_LONG = {
    "hy": (
     "🐰🌸 **Բարի գալուստ StarLegen** 🛍✨\n\n"
"💖 Մենք ուրախ ենք ողջունել Ձեզ մեր աշխարհում,\n"
"որտեղ ամեն մանրուք ստեղծված է սիրով։\n"
"Դուք արդեն մեր մեծ ընտանիքի սիրելի անդամն եք՝ №{customer_no} ✨\n\n"

"🎁 **Ի՞նչ է սպասվում**\n"
"• Ժամանակակից և որակյալ ապրանքներ\n"
"• Հատուկ զեղչեր ու անհատական առաջարկներ\n"
"• Արագ առաքում ամբողջ ՀՀ տարածքում 🚚\n"
"• Նորություններ ու անակնկալներ՝ Ձեզ զարմացնելու համար\n\n"

"📊 **Ֆինանսական հնարավորություններ**\n"
"• Օրվա թարմացված փոխարժեքներ 📈\n"
"• Անվտանգ և շահավետ փոխարկումներ\n"
"  PI ⇄ USDT · FTN ⇄ AMD · Alipay ⇄ CNY 💱\n\n"

"🌟 **Մեր առաքելությունը պարզ է**\n"
"Յուրաքանչյուր այց մեզ մոտ ոչ թե պարզապես գնում է,\n"
"այլ բացառիկ ճանապարհորդություն։\n"
"👇 Ընտրեք բաժինը և սկսեք ձեր ուղին մեզ հետ 🛍️✨"

    ),
    "ru": (
      "🐰🌸 **Добро пожаловать в StarLegen** 🛍✨\n\n"
"💖 Мы рады видеть вас в нашем мире,\n"
"где каждая деталь создана с любовью.\n"
"Вы уже член нашей большой семьи — №{customer_no} ✨\n\n"

"🎁 **Что вас ждёт**\n"
"• Современные и качественные товары\n"
"• Специальные скидки и персональные предложения\n"
"• Быстрая доставка по всей Армении 🚚\n"
"• Постоянные новинки и сюрпризы\n\n"

"📊 **Финансовые возможности**\n"
"• Ежедневно обновляемые курсы 📈\n"
"• Надёжные и выгодные обмены\n"
"  PI ⇄ USDT · FTN ⇄ AMD · Alipay ⇄ CNY 💱\n\n"

"🌟 **Наша миссия проста**\n"
"Каждый визит — это не просто покупка,\n"
"а уникальное путешествие.\n"
"👇 Выберите раздел и начните свой путь с нами 🛍️✨"

    ),
    "en": (
       "🐰🌸 **Welcome to StarLegen** 🛍✨\n\n"
"💖 We are happy to welcome you\n"
"to a world made with love and care.\n"
"You are already part of our family — №{customer_no} ✨\n\n"

"🎁 **What awaits you**\n"
"• Modern, high-quality items\n"
"• Special discounts and personal offers\n"
"• Fast delivery across Armenia 🚚\n"
"• Constant updates and surprises\n\n"

"📊 **Financial options**\n"
"• Daily updated exchange rates 📈\n"
"• Safe and profitable exchanges\n"
"  PI ⇄ USDT · FTN ⇄ AMD · Alipay ⇄ CNY 💱\n\n"

"🌟 **Our mission is simple**\n"
"Each visit is not just a purchase,\n"
"but a special journey.\n"
"👇 Choose a section and start your way with us 🛍️✨"

    ),
}

TEXTS = {
    "welcome_short": {
        "hy": "🐰🌸 Բարի գալուստ **StarLegen** 🛍✨",
        "ru": "🐰🌸 Добро пожаловать в **StarLegen** 🛍✨",
        "en": "🐰🌸 Welcome to **StarLegen** 🛍✨",
    },
    "choose_language": {
        "hy": "Ընտրեք լեզուն ⬇️", "ru": "Выберите язык ⬇️", "en": "Choose your language ⬇️",
    },
    "menu_hint": {
        "hy": "Ընտրեք մենյուից 👇", "ru": "Выберите пункт меню 👇", "en": "Choose from the menu 👇",
    },
    "back_main": {
        "hy": "🏠 Գլխավոր մենյու", "ru": "🏠 Главное меню", "en": "🏠 Main Menu",
    },
    "go_back": {
        "hy": "🔙 Վերադառնալ", "ru": "🔙 Назад", "en": "🔙 Back",
    },
    
}

# Միշտ առկա նավիգացիայի կոճակներ (քո ցանկով)
MENU = {
    "hy": {
        "shop":"🛍 Խանութ","mypage":"👤 Իմ էջ","support":"💬 Կապ մեզ հետ","partners":"🤝 Գործընկերներ",
        "exchange":"💱 Փոխարկումներ","rates":"📊 Օրվա կուրս","cart":"🛒 Զամբյուղ","search":"🔍 Որոնել",
        "invite":"🤝 Հրավիրել ընկերների","lang":"🌐 Լեզու","back":"🔙 Վերադառնալ","home":"🏠 Գլխավոր մենյու","best":"🏆 Լավագույններ",
    },
    "ru": {
        "shop":"🛍 Магазин","mypage":"👤 Моя страница","support":"💬 Поддержка","partners":"🤝 Партнёры",
        "exchange":"💱 Обмен","rates":"📊 Курс дня","cart":"🛒 Корзина","search":"🔍 Поиск",
        "invite":"🤝 Пригласить друзей","lang":"🌐 Язык","back":"🔙 Назад","home":"🏠 Главное меню","best":"🏆 Лучшее",
    },
    "en": {
        "shop":"🛍 Shop","mypage":"👤 My Page","support":"💬 Support","partners":"🤝 Partners",
        "exchange":"💱 Exchange","rates":"📊 Daily Rate","cart":"🛒 Cart","search":"🔍 Search",
        "invite":"🤝 Invite Friends","lang":"🌐 Language","back":"🔙 Back","home":"🏠 Main Menu","best":"🏆 Best",
    },
}

def t(lang: str, key: str, **kwargs) -> str:
    lang = (lang or "hy").lower()
    raw = (TEXTS.get(key, {}) or {}).get(lang, "")
    return raw.format(**kwargs) if kwargs else raw

def welcome_long(lang: str, customer_no: int) -> str:
    lang = (lang or "hy").lower()
    raw = WELCOME_LONG[lang]
    return raw.format(customer_no=customer_no)

def lang_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.row("Հայերեն 🇦🇲", "Русский 🇷🇺", "English 🇬🇧")
    return kb

def main_menu_keyboard(lang: str):
    lang = (lang or "hy").lower()
    m = MENU.get(lang, MENU["hy"])
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(m["shop"], m["cart"])
    kb.row(m["mypage"], m["best"])
    kb.row(m["exchange"], m["rates"])
    kb.row(m["support"], m["partners"])
    kb.row(m["search"], m["invite"])
    kb.row(m["lang"], m["back"], m["home"])
    return kb
 