import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from crud_func import initiate_db, get_all_products, add_user, is_included
import sqlite3


logger = logging.getLogger(__name__)

bot = Bot(token='KEY')
dp = Dispatcher(bot, storage=MemoryStorage())

initiate_db()


class RegistrationState(StatesGroup):
    username = State()
    email = State()
    age = State()


def create_product_rows():
    conn = sqlite3.connect('users_products.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO Products VALUES (null, ?, ?, ?)', ('ВитаминA', 'Качество №1.', 100))
    cursor.execute('INSERT INTO Products VALUES (null, ?, ?, ?)', ('ВитаминC', 'Импортная.', 200))
    cursor.execute('INSERT INTO Products VALUES (null, ?, ?, ?)', ('ВитаминD', 'БАД', 300))
    cursor.execute('INSERT INTO Products VALUES (null, ?, ?, ?)', ('ВитаминE', '*НОВИНКА*.', 400))
    conn.commit()
    conn.close()


create_product_rows()


@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    main_menu_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    main_menu_kb.add(types.KeyboardButton('Рассчитать'))
    main_menu_kb.add(types.KeyboardButton('Информация'))
    main_menu_kb.add(types.KeyboardButton('Купить'))
    main_menu_kb.add(types.KeyboardButton('Регистрация'))
    await message.reply("Добро пожаловать! Выберите опцию:", reply_markup=main_menu_kb)


@dp.message_handler(text='Регистрация')
async def sign_up(message: types.Message):
    await message.reply("Введите имя пользователя (только латинский алфавит):")
    await RegistrationState.username.set()


@dp.message_handler(state=RegistrationState.username)
async def set_username(message: types.Message, state: FSMContext):
    username = message.text
    if is_included(username):
        await message.reply("Пользователь существует, введите другое имя:")
        return
    await state.update_data(username=username)
    await message.reply("Введите свой email:")
    await RegistrationState.email.set()


@dp.message_handler(state=RegistrationState.email)
async def set_email(message: types.Message, state: FSMContext):
    email = message.text
    await state.update_data(email=email)
    await message.reply("Введите свой возраст:")
    await RegistrationState.age.set()


@dp.message_handler(state=RegistrationState.age)
async def set_age(message: types.Message, state: FSMContext):
    age = int(message.text)
    await state.update_data(age=age)
    data = await state.get_data()
    add_user(data['username'], data['email'], data['age'])
    await message.reply("Регистрация завершена!")
    await state.finish()


@dp.callback_query_handler()
async def handle_product_selection(call: types.CallbackQuery, state: FSMContext):
    all_products = get_all_products()
    current_state = await state.get_state()
    if current_state is None:
        await call.message.reply("Пожалуйста, выберите товар.")
        return

    for product in all_products:
        await call.message.reply(
            f"Название: {product[1]} | Описание: {product[2]} | Цена: {product[3]}")

    await call.message.reply("Продолжить выбор?", reply_markup=product_inline_kb)


@dp.callback_query_handler(text='product_buying')
async def handle_product_buying(call: types.CallbackQuery):
    await call.message.reply("Вы успешно приобрели продукт!")


@dp.message_handler(text='Отменить')
async def cancel_product_selection(message: types.Message, state: FSMContext):
    await state.finish()
    await message.reply("Выбор отменен.")


product_inline_kb = InlineKeyboardMarkup(row_width=1)
product_inline_kb.add(InlineKeyboardButton("ВитаминA", callback_data='product_buying'))
product_inline_kb.add(InlineKeyboardButton("ВитаминC", callback_data='product_buying'))
product_inline_kb.add(InlineKeyboardButton("ВитаминD", callback_data='product_buying'))
product_inline_kb.add(InlineKeyboardButton("ВитаминE", callback_data='product_buying'))

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
