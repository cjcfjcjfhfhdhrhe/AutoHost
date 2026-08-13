from telethon import TelegramClient, events
from telethon.tl.types import ReplyKeyboardMarkup, KeyboardButtonRow, KeyboardButton
from telethon.tl.custom import Button
import asyncio
import os
import glob
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
BOT_TOKEN = "8985271005:AAH82tnFSk65QgOF6k6tZaokqmN6-H1Usjg"

client = TelegramClient('bot_session', API_ID, API_HASH)

user_states = {}

def get_main_menu():
    return ReplyKeyboardMarkup(
        rows=[
            KeyboardButtonRow([KeyboardButton(text="👤 Профили"), KeyboardButton(text="⚡ Рассылка")]),
            KeyboardButtonRow([KeyboardButton(text="💬 Сообщения"), KeyboardButton(text="👥 Группы")]),
            KeyboardButtonRow([KeyboardButton(text="📊 Статистика"), KeyboardButton(text="⚙️ Настройки")]),
            KeyboardButtonRow([KeyboardButton(text="💎 Подписка"), KeyboardButton(text="❓ Поддержка")]),
        ],
        resize=True
    )

@client.on(events.NewMessage(pattern=lambda e: e.raw_text == '/start'))
async def start(event):
    await event.respond(
        "👋 Добро пожаловать в Автохост | Управление проектами!\nВыберите нужный пункт меню:",
        buttons=get_main_menu()
    )

@client.on(events.NewMessage(pattern=lambda e: e.raw_text == '👤 Профили'))
async def profiles_menu(event):
    user_id = event.sender_id
    
    session_files = glob.glob(f"session_{user_id}_*.session")
    
    text = "👤 **Управление профилями (аккаунтами):**\n\n"
    inline_buttons = []
    
    if session_files:
        text += "Подключенные аккаунты:\n"
        for sf in session_files:
            phone_num = sf.replace(f"session_{user_id}_", "").replace(".session", "")
            inline_buttons.append([Button.inline(f"📱 {phone_num} (Активен)", data=f"sel_{phone_num}".encode())])
    else:
        text += "У вас пока не добавлено ни одного аккаунта.\n"

    inline_buttons.append([Button.inline("➕ Добавить еще аккаунт", b"add_phone")])
    inline_buttons.append([Button.inline("⬅️ Назад в меню", b"back_to_menu")])

    await event.respond(text, buttons=inline_buttons)

@client.on(events.CallbackQuery(data=b'add_phone'))
async def add_phone_cb(event):
    user_id = event.sender_id
    user_states[user_id] = {'step': 'waiting_phone'}
    await event.edit("📱 Введите номер нового аккаунта в международном формате (например, `+79991234567`):")

@client.on(events.CallbackQuery(data=b'back_to_menu'))
async def back_menu_cb(event):
    await event.edit("Главное меню:")
    await event.respond("Выберите нужный пункт:", buttons=get_main_menu())

@client.on(events.CallbackQuery(pattern=b'sel_'))
async def select_profile_cb(event):
    phone = event.data.decode().replace("sel_", "")
    await event.edit(f"✅ Аккаунт **{phone}** выбран для работы!")

@client.on(events.NewMessage(pattern=lambda e: e.raw_text == '👥 Группы'))
async def groups_menu(event):
    user_id = event.sender_id
    session_files = glob.glob(f"session_{user_id}_*.session")
    
    if not session_files:
        await event.respond("⚠️ Сначала добавьте хотя бы один аккаунт через раздел **«👤 Профили»**!", buttons=get_main_menu())
        return

    await event.respond("🔍 Анализирую чаты с подключенных аккаунтов... Пожалуйста, подождите.")

    try:
        all_groups = set()
        for sf in session_files:
            session_name = sf.replace(".session", "")
            user_client = TelegramClient(session_name, API_ID, API_HASH)
            await user_client.connect()
            
            if await user_client.is_user_authorized():
                async for dialog in user_client.iter_dialogs():
                    if dialog.is_group or dialog.is_channel:
                        entity = dialog.entity
                        if hasattr(entity, 'megagroup') and entity.megagroup or dialog.is_group:
                            all_groups.add(dialog.title)
            await user_client.disconnect()

        if all_groups:
            text = "📋 **Найденные группы:**\n\n" + "\n".join([f"• {g}" for g in list(all_groups)[:30]])
        else:
            text = "📋 На подключенных аккаунтах не найдено групп."

        await event.respond(text, buttons=get_main_menu())

    except Exception as e:
        await event.respond(f"❌ Ошибка при сканировании: {e}", buttons=get_main_menu())

@client.on(events.NewMessage(pattern=lambda e: e.raw_text == '⚙️ Настройки'))
async def settings_menu(event):
    await event.respond("⚙️ Системные настройки.", buttons=get_main_menu())

@client.on(events.NewMessage(pattern=lambda e: e.raw_text == '⚡ Рассылка'))
async def mailing_menu(event):
    await event.respond("⚡ Меню управления рассылкой.", buttons=get_main_menu())

@client.on(events.NewMessage)
async def handle_auth_steps(event):
    if event.is_private and event.raw_text:
        user_id = event.sender_id
        state = user_states.get(user_id, {}).get('step')

        if state == 'waiting_phone':
            phone = event.raw_text.strip()
            user_states[user_id]['phone'] = phone
            
            session_name = f"session_{user_id}_{phone}"
            user_client = TelegramClient(session_name, API_ID, API_HASH)
            await user_client.connect()
            
            try:
                sent = await user_client.send_code_request(phone)
                user_states[user_id]['client'] = user_client
                user_states[user_id]['phone_code_hash'] = sent.phone_code_hash
                user_states[user_id]['step'] = 'waiting_code'
                await event.respond("✅ Код отправлен в Telegram этого аккаунта!\nВведите полученный код подтверждения:")
            except Exception as e:
                await event.respond(f"❌ Ошибка отправки кода: {e}\nПопробуйте снова через раздел «Профили».")
                user_states.pop(user_id, None)

        elif state == 'waiting_code':
            code = event.raw_text.strip()
            phone = user_states[user_id]['phone']
            code_hash = user_states[user_id]['phone_code_hash']
            user_client = user_states[user_id]['client']
            
            try:
                await user_client.sign_in(phone=phone, code=code, phone_code_hash=code_hash)
                await user_client.disconnect()
                user_states.pop(user_id, None)
                await event.respond(f"🎉 **Аккаунт {phone} успешно добавлен!**", buttons=get_main_menu())
            except Exception as e:
                if "A password is required" in str(e):
                    user_states[user_id]['step'] = 'waiting_password'
                    await event.respond("🔒 Требуется двухэтапная аутентификация (облачный пароль). Введите пароль:")
                else:
                    await event.respond(f"❌ Ошибка авторизации: {e}\nПопробуйте начать заново.")
                    await user_client.disconnect()
                    user_states.pop(user_id, None)

        elif state == 'waiting_password':
            password = event.raw_text.strip()
            phone = user_states[user_id]['phone']
            user_client = user_states[user_id]['client']
            
            try:
                await user_client.sign_in(password=password)
                await user_client.disconnect()
                user_states.pop(user_id, None)
                await event.respond(f"🎉 **Аккаунт {phone} успешно добавлен (2FA пройден)!**", buttons=get_main_menu())
            except Exception as e:
                await event.respond(f"❌ Неверный пароль: {e}\nПопробуйте заново через меню «Профили».")
                await user_client.disconnect()
                user_states.pop(user_id, None)

async def main():
    await client.start(bot_token=BOT_TOKEN)
    logging.info("--- АВТОХОСТ УСПЕШНО ЗАПУЩЕН ---")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
    
