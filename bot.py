import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import logging

from config import TG_TOKEN, SECRET, my_params
from service import  Loader
from utils import is_authorized, add_user_to_database, get_users

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Создание экземпляра бота
bot = Bot(token=TG_TOKEN)
dp = Dispatcher()

scheduler = AsyncIOScheduler(timezone='Europe/Moscow')


# Обработчик команды /start
@dp.message(Command("start"))
async def start(message: types.Message):
    """
        This handler receives messages with `/start` command
    """
    # Проверяем, авторизован ли пользователь
    if is_authorized(message.from_user.id):
        await message.reply('Вы успешно авторизовались. '
                            'Для справки вызовите команду /help.')
    else:
        # Запрашиваем секретное слово у пользователя
        await message.reply('Введите секретное слово:')


# Обработчик команды "/help"
@dp.message(Command("help"))
async def process_help_command(message: types.Message):
    """
        This handler receives messages with `/help` command
    """
    help_message = "Бот ежедневно в 10:00 и 18:00 отправляет список заказов, которые были отгружены, " \
                    "но не были отсканированы в течение 12 часов.\n\n" \
                    "Список доступных команд:\n\n" \
                    "/start - Начать взаимодействие с ботом.\n\n" \
                    "/info - Получить номера заказов с расхождениями за последние 12 часов.\n\n"
    await message.reply(help_message)


# Обработчик команды /info
@dp.message(Command("info"))
async def start(message: types.Message):
    """
        This handler receives messages with `/info` command
    """
    # Проверяем, авторизован ли пользователь
    if is_authorized(message.from_user.id):
        loader_order = Loader(params=my_params)
        report_text = loader_order.formation_text_message()
        await message.reply(report_text)
    else:
        # Запрашиваем секретное слово у пользователя
        await message.reply('Введите секретное слово:')


# Обработчик текстовых сообщений
@dp.message()
async def process_secret_word(message: types.Message):
    # Проверяем, соответствует ли введенное слово секретному слову
    if message.text == SECRET:
        # Добавляем идентификатор пользователя в базу данных
        add_user_to_database(message.from_user.id)
        await message.reply('Вы успешно авторизовались. '
                            'Для справки вызовите команду /help.')
    elif is_authorized(message.from_user.id):
        await message.reply('Вы успешно авторизовались. '
                            'Для справки вызовите команду /help.')
    else:
        await message.reply('Введите секретное слово:')


async def send_result():
    # Получение списка активных чатов
    active_users = get_users()
    # Отправка сообщения с результатом во все активные чаты
    loader_order = Loader(params=my_params)
    report_text = loader_order.formation_text_message()

    for user_id in active_users:
        await bot.send_message(chat_id=user_id[0], text=report_text)


# Запуск бота
async def main():
    scheduler.add_job(send_result, 'cron', hour=13)
    scheduler.add_job(send_result, 'cron', hour=18)
    scheduler.start()
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())