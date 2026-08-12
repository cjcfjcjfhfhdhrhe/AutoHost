import asyncio
import os
import logging
import subprocess
from telethon import TelegramClient, events
from telethon.tl.types import ReplyKeyboardMarkup, KeyboardButtonRow, KeyboardButton

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

API_ID = 2040
API_HASH = "b18441aff607e10a989891a5462e627"
MAIN_BOT_TOKEN = "8729742332:AAHxR7NqPhVaV_ij1HOCdQeo7MqqrM-S1PA"

USERS_BOTS_DIR = "users_bots"
os.makedirs(USERS_BOTS_DIR, exist_ok=True)

# Словарь для хранения запущенных процессов пользователей
running_bots = {}

def get_main_menu():
    return ReplyKeyboardMarkup(
        rows=[
            KeyboardButtonRow([KeyboardButton(text="🚀 Мед бот"), KeyboardButton(text="🔴 Помощь")]),
            KeyboardButtonRow([KeyboardButton(text="⚙️ Статус"), KeyboardButton(text="🛑 Остановить бот")])
        ],
        resize=True
    )

async def main():
    client = TelegramClient('main_bot_session', API_ID, API_HASH)
    
    @client.on(events.NewMessage(pattern='/start'))
    async def start(event):
        await event.respond("Привет! Я бот-менеджер для запуска ваших скриптов.", buttons=get_main_menu())

    @client.on(events.NewMessage(pattern='🚀 Мед бот'))
    async def run_med_bot(event):
        user_id = event.sender_id
        await event.respond("Запускаю процесс...", buttons=get_main_menu())
        
        # Пример запуска простого цикла или скрипта
        script_path = os.path.join(USERS_BOTS_DIR, f"user_{user_id}.py")
        
        # Создадим простой тестовый скрипт для демонстрации, если его нет
        if not os.path.exists(script_path):
            with open(script_path, "w", encoding="utf-8") as f:
                f.write("import time\nwhile True:\n    print('Running...')\n    time.sleep(5)")

        if user_id in running_bots:
            running_bots[user_id].terminate()

        process = subprocess.Popen(["python", script_path])
        running_bots[user_id] = process
        await event.respond("✅ Бот успешно запущен в фоновом режиме!", buttons=get_main_menu())

    @client.on(events.NewMessage(pattern='🛑 Остановить бот'))
    async def stop_bot(event):
        user_id = event.sender_id
        if user_id in running_bots:
            running_bots[user_id].terminate()
            del running_bots[user_id]
            await event.respond("🛑 Ваш бот остановлен.", buttons=get_main_menu())
        else:
            await event.respond("У вас нет запущенных активных ботов.", buttons=get_main_menu())

    @client.on(events.NewMessage(pattern='⚙️ Статус'))
    async def status_bot(event):
        user_id = event.sender_id
        if user_id in running_bots and running_bots[user_id].poll() is None:
            await event.respond("🟢 Статус: Бот работает.", buttons=get_main_menu())
        else:
            await event.respond("🔴 Статус: Бот не запущен.", buttons=get_main_menu())

    await client.start(bot_token=MAIN_BOT_TOKEN)
    logging.info("Главный бот-менеджер запущен и ожидает сообщения...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
    
