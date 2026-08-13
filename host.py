from telethon import TelegramClient, events
from telethon.tl.types import ReplyKeyboardMarkup, KeyboardButtonRow, KeyboardButton
from telethon.tl.custom import Button
import asyncio
import os
import glob
import logging
import subprocess

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
BOT_TOKEN = "8985271005:AAH82tnFSk65QgOF6k6tZaokqmN6-H1Usjg"

client = TelegramClient('bot_session', API_ID, API_HASH)

user_states = {}
# Словарь для хранения активных процессов запущенных ботов: {user_id: subprocess.Popen}
active_bot_processes = {}

def get_main_menu(is_admin=False):
    rows = [
        KeyboardButtonRow([KeyboardButton(text="👤 Профили"), KeyboardButton(text="⚡ Рассылка")]),
        KeyboardButtonRow([KeyboardButton(text="💬 Сообщения"), KeyboardButton(text="👥 Группы")]),
        KeyboardButtonRow([KeyboardButton(text="🤖 Создать своего бота"), KeyboardButton(text="⚙️ Настройки")]),
        KeyboardButtonRow([KeyboardButton(text="💎 Подписка"), KeyboardButton(text="❓ Поддержка")]),
    ]
    if is_admin:
        rows.append(KeyboardButtonRow([KeyboardButton(text="🛠 Админ-панель")]))
    return ReplyKeyboardMarkup(rows=rows, resize=True)

@client.on(events.NewMessage(pattern=lambda e: e.raw_text == '/start'))
async def start(event):
    user_id = event.sender_id
    is_admin = user_id == 2040  # Ваш ID
    
    await event.respond(
        "🤖 **Добро пожаловать в CisAuto (Автохост)!**\nУправляйте своими ботами и загружайте обновления.",
        buttons=get_main_menu(is_admin=is_admin)
    )

@client.on(events.NewMessage(pattern=lambda e: e.raw_text == '🤖 Создать своего бота'))
async def host_bot_menu(event):
    user_id = event.sender_id
    user_states[user_id] = {'step': 'waiting_bot_file'}
    
    text = (
        "🤖 **Автохост ботов:**\n\n"
        "Отправьте мне файл вашего бота (`.py`), чтобы разместить его на хосте или обновить уже существующий.\n"
        "⚠️ *Если файл с таким именем уже существовал, старая версия будет полностью остановлена, а код заменен на новый.*"
    )
    await event.respond(text, buttons=get_main_menu())

# Перехват файла для хостинга
@client.on(events.NewMessage)
async def handle_file_upload(event):
    if not event.is_private:
        return

    user_id = event.sender_id
    state_data = user_states.get(user_id)
    
    if not state_data or state_data.get('step') != 'waiting_bot_file':
        return

    # Проверяем, прислал ли пользователь файл
    if event.document:
        file_name = event.document.attributes[0].file_name if hasattr(event.document.attributes[0], 'file_name') else f"bot_{user_id}.py"
        
        if not file_name.endswith('.py'):
            await event.respond("❌ Пожалуйста, отправьте файл с расширением `.py`!")
            return

        # Создаем папку для пользовательских ботов, если её нет
        os.makedirs("hosted_bots", exist_ok=True)
        file_path = os.path.join("hosted_bots", f"user_{user_id}_{file_name}")

        # Скачиваем файл (он принудительно перезапишет старый файл, если он там был)
        await event.client.download_media(event.message, file=file_path)

        # 1. Останавливаем старый процесс этого бота, если он работал
        if user_id in active_bot_processes:
            try:
                active_bot_processes[user_id].terminate()
                active_bot_processes[user_id].wait()
            except Exception:
                pass

        # 2. Запускаем новый файл свежей версии
        try:
            process = subprocess.Popen(["python", file_path])
            active_bot_processes[user_id] = process
            
            user_states.pop(user_id, None)
            await event.respond(
                f"✅ **Успешно!** Файл `{file_name}` принят, перезаписан и запущен на автохосте.\nСтарые процессы обновлены.",
                buttons=get_main_menu()
            )
        except Exception as e:
            await event.respond(f"❌ Ошибка при запуске скрипта: {e}", buttons=get_main_menu())
    else:
        await event.respond("⚠️ Пожалуйста, отправьте именно файл скрипта (`.py`), а не текст.")

@client.on(events.NewMessage(pattern=lambda e: e.raw_text in ['👤 Профили', '⚡ Рассылка', '💬 Сообщения', '👥 Группы', '⚙️ Настройки', '💎 Подписка', '❓ Поддержка', '🛠 Админ-панель']))
async def other_menus(event):
    user_id = event.sender_id
    user_states.pop(user_id, None)
    text = event.raw_text
    await event.respond(f"🛠 Раздел **{text}** в разработке.", buttons=get_main_menu())

async def main():
    await client.start(bot_token=BOT_TOKEN)
    logging.info("--- АВТОХОСТ CISAUTO УСПЕШНО ЗАПУЩЕН ---")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
    
