# src/core/pu/pu00_menu_router.py
# Պարզ router, որ մենյուի ոչ-խանութ կոճակները հանգիստ պատասխան տան
from telebot import types

def register(bot, ctx):
    def _has(txt, keys):
        if not isinstance(txt, str):
            return False
        low = txt.lower()
        return any(k in low for k in keys)

    def say(m, text):
        try:
            bot.send_message(m.chat.id, text, parse_mode=None)
        except Exception:
            pass

    # ⚠️ Չենք դիպչում «Խանութ/Զամբյուղ»—ը, դրանք արդեն PU04/PU05-ում են

    @bot.message_handler(func=lambda m: _has(m.text, ["իմ էջ", "profile"]))
    def _(m): say(m, "👤 «Իմ էջ» մոդուլը դեռ չի միացված։")

    @bot.message_handler(func=lambda m: _has(m.text, ["լավագույն", "leaders", "best"]))
    def _(m): say(m, "🏆 «Լավագույններ» կհաղորդակցվի, երբ միացնենք համապատասխան PU-ը։")

    @bot.message_handler(func=lambda m: _has(m.text, ["օրվա", "կուպոն", "coupon"]))
    def _(m): say(m, "🎟 «Օրվա կուպոն» շուտով։")

    @bot.message_handler(func=lambda m: _has(m.text, ["ֆինանս", "finance"]))
    def _(m): say(m, "📊 «Ֆինանսականներ» շուտով։")

    @bot.message_handler(func=lambda m: _has(m.text, ["գործընկեր", "partners"]))
    def _(m): say(m, "🤝 «Գործընկերներ» շուտով։")

    @bot.message_handler(func=lambda m: _has(m.text, ["կապ մեզ հետ", "support", "կապ"]))
    def _(m): say(m, "💬 «Կապ մեզ հետ» շուտով։")

    @bot.message_handler(func=lambda m: _has(m.text, ["որոն", " փնտր"]))
    def _(m): say(m, "🔎 «Որոնել» շուտով։")

    @bot.message_handler(func=lambda m: _has(m.text, ["լեզու", "language"]))
    def _(m): say(m, "🌐 Լեզվի ընտրությունը շուտով։")



def healthcheck(_):
    return True
