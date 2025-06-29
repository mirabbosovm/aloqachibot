from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
import json
from keep_alive import keep_alive
import requests
import os

API_TOKEN = '7552192503:AAG56SZBLsKkn-56xNFCJ6ZuzvlgEAcc7WI'
ADMIN_ID = 959222282

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# Ro'yxatdan o'tish state'lari
class RegisterState(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()

users_file = 'users.json'
def load_users():
    return json.load(open(users_file, 'r')) if os.path.exists(users_file) else {}

def save_users(data):
    with open(users_file, 'w') as f:
        json.dump(data, f, indent=4)

# /start komandasi
@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    users = load_users()
    if str(message.from_user.id) in users:
        await message.answer("Siz allaqachon ro'yxatdan o'tgansiz.")
    else:
        await message.answer("Ismingizni kiriting:")
        await RegisterState.waiting_for_name.set()

@dp.message_handler(state=RegisterState.waiting_for_name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    button = KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True)
    markup = ReplyKeyboardMarkup(resize_keyboard=True).add(button)
    await message.answer("Iltimos, telefon raqamingizni yuboring", reply_markup=markup)
    await RegisterState.waiting_for_phone.set()

@dp.message_handler(content_types=types.ContentType.CONTACT, state=RegisterState.waiting_for_phone)
async def get_phone(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name = data['name']
    phone = message.contact.phone_number
    users = load_users()
    users[str(message.from_user.id)] = {"name": name, "phone": phone}
    save_users(users)
    await message.answer("Ro'yxatdan o'tdingiz!", reply_markup=types.ReplyKeyboardRemove())
    await state.finish()

# /ism buyrug'i orqali ismni o'zgartirish
@dp.message_handler(commands=['ism'])
async def change_name(message: types.Message):
    users = load_users()
    if str(message.from_user.id) in users:
        await message.answer("Yangi ismingizni kiriting:")
        await RegisterState.waiting_for_name.set()
    else:
        await message.answer("Iltimos, avval ro'yxatdan o'ting /start orqali.")

# /valyuta buyrug'i orqali MB kurslari
@dp.message_handler(commands=['valyuta'])
async def get_valyuta(message: types.Message):
    url = 'https://cbu.uz/uz/arkhiv-kursov-valyut/json/'
    try:
        r = requests.get(url, timeout=5).json()
        result = []
        for item in r:
            if item['Ccy'] in ['USD', 'EUR', 'RUB']:
                result.append(f"{item['CcyNm_UZ']} ({item['Ccy']}):\n  Sotib olish: {item['Rate']} so'm\n  Sana: {item['Date']}")
        await message.answer("\n\n".join(result))
    except:
        await message.answer("Valyuta kurslarini olishda xatolik yuz berdi.")

# Har qanday media va matn adminga yuboriladi
@dp.message_handler(content_types=types.ContentType.ANY)
async def forward_media(message: types.Message):
    users = load_users()
    if str(message.from_user.id) not in users:
        await message.answer("Iltimos, avval ro'yxatdan o'ting /start orqali.")
        return
    user = users[str(message.from_user.id)]
    caption = f"📩 Yangi xabar\n👤 {user.get('name')}\n📞 {user.get('phone')}\n🆔 {message.from_user.id}"
    await bot.send_message(chat_id=ADMIN_ID, text=caption)
    await bot.copy_message(chat_id=ADMIN_ID, from_chat_id=message.chat.id, message_id=message.message_id)
    await message.answer("Xabaringiz yuborildi!")

# Flask serverni ishga tushirish
if __name__ == '__main__':
    keep_alive()
    executor.start_polling(dp, skip_updates=True)
