from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import logging

# ✅ Քո Token-ն ու Admin ID-ն
TOKEN = "7198636747:AAFIrJruVLD7g64u82r1OnXyYaA-wdlOWnU"
ADMIN_ID = 123456789

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    customer_id = 1008  # ֆեյք հաճախորդի համար
    photo = types.InputFile("bunny.jpg")
    caption = (
        "🐰\n\n"
        "🌸 Շնորհակալ ենք, որ ընտրել եք BabyAngels 🛍️  \n"
        "Մենք ստեղծել ենք մի վայր, որտեղ յուրաքանչյուրը կարող է գտնել օգտակար և գեղեցիկ ապրանքներ՝ հարմար գնով։\n\n"
        "Բացի այդ՝ առաջարկում ենք նաև փոխարկման հարմար ծառայություններ՝\n"
        "🔁 PI ➝ USDT\n"
        "💸 FTN ➝ AMD\n"
        "🇨🇳 AliPay լիցքավորում\n\n"
        f"Դուք արդեն մեր սիրելի հաճախորդն եք՝ №{customer_id} ❤️\n"
        "✨ Բարի գնումներ ենք մաղթում 💕\n"
        "Ընտրեք բաժին 👇"
    )
    await bot.send_photo(chat_id=message.chat.id, photo=photo, caption=caption, reply_markup=main_menu())

def main_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("📦 Կատեգորիա"))
    keyboard.add(KeyboardButton("💱 Փոխարկումներ"), KeyboardButton("🎁 Բոնուս անիվ"))
    keyboard.add(KeyboardButton("📜 Պատվերներ"), KeyboardButton("📞 Կապ մեզ հետ"))
    return keyboard

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)
