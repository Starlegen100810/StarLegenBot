from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InputMediaPhoto
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import logging

# ✅ Քո Token-ն ու Admin ID-ն
TOKEN = "7198636747:AAH935iIyifn79jNueXiGaYzcjf7d7shaQo"
ADMIN_ID = 6822052289

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# 🛒 Զամբյուղի տվյալներ
cart = {}
user_data = {}

# 🏆 Լավագույն վաճառվող ապրանքներ
best_selling_products = {
    "BA100810": 79,
    "BA100811": 104,
    "BA100812": 92
}

def update_best_selling_sales():
    for product_code in best_selling_products:
        best_selling_products[product_code] += 2

# 🧾 Պատվերի ընթացքի վիճակներ
class OrderInfo(StatesGroup):
    country = State()
    name = State()
    surname = State()
    phone = State()

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    customer_id = 1008
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
    keyboard.add(KeyboardButton("🛒 Զամբյուղ"), KeyboardButton("📞 Կապ մեզ հետ"))
    keyboard.add(KeyboardButton("👤 Իմ էջը"))
    return keyboard

@dp.message_handler(lambda message: message.text == "📦 Կատեգորիա")
async def show_categories(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("🏠 Տուն & Կենցաղ"))
    keyboard.add(KeyboardButton("🔙 Վերադառնալ"))
    await message.answer("🧭 Ընտրեք ապրանքների բաժինը 👇", reply_markup=keyboard)

@dp.message_handler(lambda message: message.text == "🏠 Տուն & Կենցաղ")
async def show_household_products(message: types.Message):
    sales = best_selling_products.get("BA100810", 79)
    media = types.MediaGroup()
    media.attach_photo(types.InputFile("media/products/BA100810.jpg"), f"🌸 Գորգ - Ծաղկավոր & Թիթեռներով\n\n"
                          "🏆 Լավագույն վաճառվող\n"
                          "🔹 Չափս՝ 40x60 սմ\n"
                          "🔹 Հին գին — 2560֏ (−34%)\n"
                          "🔸 Նոր գին — 1690֏\n"
                          f"🛍️ Վաճառված՝ {sales} հատ\n\n"
                          "➡️ Սեղմեք «Ավելացնել Զամբյուղ»՝ գնելուն անցնելու համար:")
    await bot.send_media_group(chat_id=message.chat.id, media=media)

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("➕ Ավելացնել Զամբյուղ"), KeyboardButton("🔙 Վերադառնալ"))
    await message.answer("✅ Ապրանքը ցուցադրված է վերևում:", reply_markup=keyboard)

@dp.message_handler(lambda message: message.text == "➕ Ավելացնել Զամբյուղ")
async def add_to_cart(message: types.Message):
    user_id = message.from_user.id
    product_code = "BA100810"
    if user_id not in cart:
        cart[user_id] = []
    cart[user_id].append(product_code)
    await message.answer("✅ Ապրանքը ավելացվել է զամբյուղում։", reply_markup=main_menu())

@dp.message_handler(lambda message: message.text == "🛒 Զամբյուղ")
async def view_cart(message: types.Message):
    user_id = message.from_user.id
    if user_id not in cart or not cart[user_id]:
        await message.answer("🛒 Ձեր զամբյուղը դեռ դատարկ է։")
        return

    text = "🧺 Ձեր զամբյուղում կա հետևյալ ապրանքը․\n\n"
    for product_code in cart[user_id]:
        if product_code == "BA100810":
            text += (
                "🌸 Գորգ - Ծաղկավոր & Թիթեռներով\n"
                "🔸 Գին՝ 1690֏\n"
                "🛍️ Քանակ՝ 1 հատ\n\n"
            )

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("✅ Անցնել պատվերին"), KeyboardButton("🔙 Վերադառնալ"))
    await message.answer(text, reply_markup=keyboard)

@dp.message_handler(lambda message: message.text == "✅ Անցնել պատվերին")
async def start_order(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("🇦🇲 Հայաստան"), KeyboardButton("🇷🇺 Ռուսաստան"))
    keyboard.add(KeyboardButton("🔙 Վերադառնալ"))
    await message.answer("📍 Ընտրեք երկիրը՝", reply_markup=keyboard)
    await OrderInfo.country.set()

@dp.message_handler(state=OrderInfo.country)
async def ask_name(message: types.Message, state: FSMContext):
    await state.update_data(country=message.text)
    await message.answer("👤 Մուտքագրեք Ձեր անունը՝", reply_markup=ReplyKeyboardRemove())
    await OrderInfo.name.set()

@dp.message_handler(state=OrderInfo.name)
async def ask_surname(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("👤 Մուտքագրեք Ձեր ազգանունը՝")
    await OrderInfo.surname.set()

@dp.message_handler(state=OrderInfo.surname)
async def ask_phone(message: types.Message, state: FSMContext):
    await state.update_data(surname=message.text)
    await message.answer("📞 Մուտքագրեք Ձեր հեռախոսահամարը՝")
    await OrderInfo.phone.set()

@dp.message_handler(state=OrderInfo.phone)
async def finish_order(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    data = await state.get_data()
    user_data[message.from_user.id] = {
        "country": data['country'],
        "name": data['name'],
        "surname": data['surname'],
        "phone": data['phone'],
        "orders": user_data.get(message.from_user.id, {}).get("orders", 0) + 1,
        "discount": min(user_data.get(message.from_user.id, {}).get("discount", 0) + 5, 20)
    }
    update_best_selling_sales()  # ✅ Քայլ 15 – Auto increment
    summary = (
        f"📦 Պատվերի ամփոփում՝\n\n"
        f"🌍 Երկիր: {data['country']}\n"
        f"👤 Անուն: {data['name']}\n"
        f"👤 Ազգանուն: {data['surname']}\n"
        f"📞 Հեռախոս: {data['phone']}\n\n"
        "💳 Հիմա ընտրեք վճարման եղանակը:"
    )
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("💵 Կանխիկ"), KeyboardButton("📱 IDram"), KeyboardButton("💳 TelCell"))
    keyboard.add(KeyboardButton("🔙 Վերադառնալ"))
    await message.answer(summary, reply_markup=keyboard)
    await state.finish()

@dp.message_handler(lambda message: message.text in ["💵 Կանխիկ", "📱 IDram", "💳 TelCell"])
async def payment_method_selected(message: types.Message):
    await message.answer(
        f"💳 Դուք ընտրեցիք՝ {message.text} վճարման եղանակը։\n\n"
        "📸 Խնդրում ենք ուղարկել վճարման անդորրագիրը (նկար կամ տեքստ)՝ վճարումը հաստատելու համար։"
    )

@dp.message_handler(content_types=['photo', 'text'])
async def receive_receipt(message: types.Message):
    if message.photo:
        await message.answer("✅ Շնորհակալություն, ձեր ուղարկած անդորրագիրն ընդունված է։")
    elif message.text:
        await message.answer(f"✅ Շնորհակալություն, ձեր հաղորդագրությունը ստացվել է։\n\n📄 Բովանդակություն՝ {message.text}")
    else:
        await message.answer("⚠️ Խնդրում ենք ուղարկել վճարման նկար կամ տեքստային անդորրագիր։")

    await message.answer(
        "🎉 Ձեր պատվերը հաջողությամբ գրանցվեց։\n\n"
        "🕐 Մեր օպերատորը շուտով կկապվի ձեզ հետ պատվերը հաստատելու և առաքման մանրամասները պարզելու համար։\n\n"
        "🙏 Եթե ցանկանում եք, կարող եք թողնել կարծիք պատվերի մասին 👇",
        reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("✍️ Թողնել կարծիք"))
    )

@dp.message_handler(lambda message: message.text == "👤 Իմ էջը")
async def personal_page(message: types.Message):
    user_id = message.from_user.id
    data = user_data.get(user_id)
    if not data:
        await message.answer("📄 Դուք դեռ պատվեր չեք կատարել, էջը հասանելի կլինի առաջին պատվերից հետո։")
        return

    profile = (
        f"👤 Անձնական էջ \n\n"
        f"🌍 Երկիր: {data['country']}\n"
        f"👤 Անուն: {data['name']} {data['surname']}\n"
        f"📞 Հեռախոս: {data['phone']}\n"
        f"📦 Պատվերների քանակ: {data['orders']}\n"
        f"🎁 Կուտակած զեղչ: {data['discount']}%"
    )
    await message.answer(profile)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)
