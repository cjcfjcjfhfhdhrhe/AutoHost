Import asyncio
import os
import logging
import subprocess
from telethon import TelegramClient, events
from telethon.tl.types import ReplyKeyboardMarkup, KeyboardButtonRow, KeyboardButton

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
MAIN_BOT_TOKEN = "8729742332:AAHxR7NqPHVaV_ijlHOCDqEo7MqqrM-SlPA"

USERS_BOTS_DIR = "users_bots"
os.makedirs(USERS_BOTS_DIR, exist_ok=True)

# Словарь для хранения запущенных процессов пользователей
running_bots = {}

def get_main_menu():
    return ReplyKeyboardMarkup(
        rows=[
            KeyboardButtonRow([KeyboardButton(text="🚀 Мой бот"), KeyboardButton(text="🛑 Статус хоста")]),
            KeyboardButtonRow([KeyboardButton(text="❓ Помощь")]),
        ],
        resize=True
    )

def setup_bot_handlers(bot_client):

    @bot_client.on(events.NewMessage(incoming=True, pattern='/start'))
    async def start(event):
        await event.respond(
            "🤖 **Автохост-менеджер CisAuto**\n\n"
            "Отправьте мне ваш `.py` файл, и я автоматически сохраню и **запущу** его на хостинге 24/7!",
            buttons=get_main_menu()
        )

    @bot_client.on(events.NewMessage(incoming=True, pattern='❓ Помощь'))
    async def help_cmd(event):
        await event.respond(
            "📖 **Инструкция:**\n"
            "1. Отправьте файл вашего бота с расширением `.py`.\n"
            "2. Бот примет его и сразу активирует процесс в фоновом режиме.",
            buttons=get_main_menu()
        )

    @bot_client.on(events.NewMessage(incoming=True, pattern='🛑 Статус хоста'))
    async def status_host(event):
        active_count = len(running_bots)
        await event.respond(f"🟢 Хостинг-менеджер активен. Запущено пользовательских ботов: {active_count}", buttons=get_main_menu())

    @bot_client.on(events.NewMessage(incoming=True, pattern='🚀 Мой бот'))
    async def my_bot_status(event):
        user_id = event.sender_id
        if user_id in running_bots and running_bots[user_id].poll() is None:
            await event.respond("✅ Ваш бот в данный момент **работает** в активном процессе.", buttons=get_main_menu())
        else:
            await event.respond("⚠️ Ваш бот не запущен. Отправьте файл `.py` заново.", buttons=get_main_menu())

    @bot_client.on(events.NewMessage(incoming=True))
    async def handle_file(event):
        system_texts = ["🚀 Мой бот", "🛑 Статус хоста", "❓ Помощь", "/start"]
        if event.text in system_texts:
            return

        if event.document:
            file_name = "bot.py"
            for attr in event.document.attributes:
                if hasattr(attr, 'file_name'):
                    file_name = attr.file_name

            if not file_name.endswith('.py'):
                await event.respond("❌ Ошибка: отправьте файл с расширением **.py**")
                return

            user_id = event.sender_id
            status_msg = await event.respond("🔄 Принимаю файл и запускаю процесс...")

            try:
                safe_file_name = f"user_{user_id}_{file_name}"
                file_path = os.path.join(USERS_BOTS_DIR, safe_file_name)
                
                # Скачиваем файл
                await event.download_media(file=file_path)

                # Если у пользователя уже был запущен бот, останавливаем старый процесс
                if user_id in running_bots:
                    try:
                        running_bots[user_id].terminate()
                    except:
                        pass

                # Запускаем новый скрипт в фоновом режиме через Python
                process = subprocess.Popen(["python", file_path])
                running_bots[user_id] = process

                await status_msg.edit(
                    f"🎉 **Успешно!**\n"
                    f"Файл `{file_name}` принят и **запущен** в фоновом режиме.",
                    buttons=get_main_menu()
                )

            except Exception as e:
                await status_msg.edit(f"❌ Ошибка при запуске: {e}", buttons=get_main_menu())

async def main():
    main_bot = TelegramClient("autohost_fixed_session", API_ID, API_HASH)
    await main_bot.start(bot_token=MAIN_BOT_TOKEN)
    setup_bot_handlers(main_bot)
    logging.info("Бот-автохост запущен с поддержкой автозапуска файлов!")
    await main_bot.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())