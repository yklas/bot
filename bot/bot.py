import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from datetime import datetime, time
import pytz
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import random
import json
import os
from typing import List, Dict, TypedDict, Optional

# Configuration
TELEGRAM_TOKEN = "7819420348:AAHElDNd7JI4c5gDbYD7TTe2kAWVn2TVZBo"
TIMEZONE = pytz.timezone('Asia/Almaty')
NOTIFICATIONS_FILE = "user_notifications.json"

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Data structures
class CustomNotification(TypedDict):
    hour: int
    minute: int
    message: str
    enabled: bool

# Storage
active_users: set[int] = set()
group_ids: set[int] = set()
user_notifications: Dict[int, List[CustomNotification]] = {}

# Updated basic responses
BASIC_RESPONSES = {
    "сәлем": "Уағалейкум ассалам! Қалыңыз қалай? 😊",
    "салем": "Уағалейкум ассалам! Қалыңыз қалай? 😊",
    "қалайсың": "Алхамдулиллаһ, жақсымын! Өзіңіз қалай? 🌟",
    "рахмет": "Бәрекелді! 🙏",
    "ассалаумағалейкум": "Уағалейкум ассалам! Қалыңыз қалай? 😊",
    "не жаңалық": "Алхамдулиллаһ, бәрі жақсы! Сізде қандай жаңалықтар бар? 🌟",
    "қайырлы таң": "Қайырлы таң! Күніңіз берекелі болсын! ✨",
    "жақсымын": "Алхамдулиллаһ! Әрдайым жақсы болыңыз! 😊",
    "бауырым": "Иә, тыңдап тұрмын 😊",
    "жақсы": "Алхамдулиллаһ! 🌟",
}

# Notification management functions
def load_notifications():
    """Load custom notifications from file"""
    if os.path.exists(NOTIFICATIONS_FILE):
        try:
            with open(NOTIFICATIONS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {int(k): v for k, v in data.items()}
        except Exception as e:
            logger.error(f"Error loading notifications: {e}")
    return {}

def save_notifications():
    """Save custom notifications to file"""
    try:
        with open(NOTIFICATIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(user_notifications, f, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving notifications: {e}")

# Initialize scheduler
scheduler = AsyncIOScheduler(timezone=TIMEZONE)

# Command handlers
@dp.message(CommandStart())
async def start_command(message: Message):
    """Handle /start command"""
    try:
        chat_id = message.chat.id
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🕒 Ескертулерді баптау", callback_data="manage_notifications")],
            [InlineKeyboardButton(text="📚 Ағылшын тілін үйрену", callback_data="learn_english")]
        ])
        
        await message.reply(
            "Ассалаумағалейкум! 👋\n\n"
            "Мен сіздің көмекшіңізбін. Мен арқылы:\n"
            "• Ескертулер қоя аласыз 🕒\n"
            "• Ағылшын тілін үйрене аласыз 📚\n"
            "• Күнделікті жаттығулар жасай аласыз 💪\n\n"
            "Төмендегі батырмаларды басып, қажетті әрекетті таңдаңыз!",
            reply_markup=keyboard
        )
        
        # Load existing notifications for this user
        if chat_id not in user_notifications:
            user_notifications[chat_id] = []
            save_notifications()
            
    except Exception as e:
        logger.error(f"Error in start_command: {e}")
        await message.reply("Қателік орын алды. Қайтадан әрекеттеніп көріңіз.")

@dp.callback_query(lambda c: c.data == "manage_notifications")
async def manage_notifications_handler(callback_query: CallbackQuery):
    """Handle notifications management"""
    try:
        chat_id = callback_query.message.chat.id
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Жаңа ескерту қосу", callback_data="add_notification")],
            [InlineKeyboardButton(text="📋 Ескертулер тізімі", callback_data="list_notifications")],
            [InlineKeyboardButton(text="🔙 Артқа", callback_data="back_to_main")]
        ])
        
        await callback_query.message.edit_text(
            "🕒 Ескертулерді баптау мәзірі:\n\n"
            "• Жаңа ескерту қосу үшін '➕ Жаңа ескерту қосу' батырмасын басыңыз\n"
            "• Ескертулер тізімін көру үшін '📋 Ескертулер тізімі' батырмасын басыңыз",
            reply_markup=keyboard
        )
    
    except Exception as e:
        logger.error(f"Error in manage_notifications_handler: {e}")
        await callback_query.answer("Қателік орын алды. Қайтадан көріңіз.")

@dp.callback_query(lambda c: c.data == "add_notification")
async def add_notification_handler(callback_query: CallbackQuery):
    """Handle adding new notification"""
    try:
        await callback_query.message.edit_text(
            "⏰ Жаңа ескерту қосу:\n\n"
            "Ескертуді келесі форматта жіберіңіз:\n"
            "12:30 Дәрі ішу\n\n"
            "Мысалы:\n"
            "9:00 Таңғы жаттығу\n"
            "13:45 Түскі ас\n"
            "22:00 Ұйықтау",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Артқа", callback_data="manage_notifications")]
            ])
        )
        
    except Exception as e:
        logger.error(f"Error in add_notification_handler: {e}")
        await callback_query.answer("Қателік орын алды. Қайтадан көріңіз.")

@dp.message()
async def handle_notification_input(message: Message):
    """Handle text input for new notifications"""
    try:
        # Check if message format matches time + text
        text = message.text.strip()
        if ' ' in text:
            time_str, *message_parts = text.split(' ')
            if ':' in time_str:
                hour, minute = map(int, time_str.split(':'))
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    notification_text = ' '.join(message_parts)
                    
                    # Add notification
                    chat_id = message.chat.id
                    if chat_id not in user_notifications:
                        user_notifications[chat_id] = []
                    
                    new_notification = {
                        'hour': hour,
                        'minute': minute,
                        'message': notification_text,
                        'enabled': True
                    }
                    
                    user_notifications[chat_id].append(new_notification)
                    save_notifications()
                    
                    # Schedule the notification
                    job_id = f'custom_{chat_id}_{hour}_{minute}'
                    scheduler.add_job(
                        send_notification,
                        'cron',
                        hour=hour,
                        minute=minute,
                        args=[chat_id, notification_text],
                        id=job_id,
                        replace_existing=True
                    )
                    
                    # Confirm addition
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="➕ Тағы қосу", callback_data="add_notification")],
                        [InlineKeyboardButton(text="📋 Ескертулер тізімі", callback_data="list_notifications")],
                        [InlineKeyboardButton(text="🔙 Басты мәзір", callback_data="back_to_main")]
                    ])
                    
                    await message.reply(
                        f"✅ Жаңа ескерту сәтті қосылды!\n\n"
                        f"⏰ Уақыты: {hour:02d}:{minute:02d}\n"
                        f"📝 Хабарлама: {notification_text}",
                        reply_markup=keyboard
                    )
                    return
                    
        # Handle basic responses if not a notification
        if text.lower() in BASIC_RESPONSES:
            await message.reply(BASIC_RESPONSES[text.lower()])
            
    except Exception as e:
        logger.error(f"Error in handle_notification_input: {e}")
        await message.reply("Қателік орын алды. Қайтадан көріңіз.")

async def send_notification(chat_id: int, message: str):
    """Send scheduled notification"""
    try:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Ескертулер тізімі", callback_data="list_notifications")]
        ])
        
        await bot.send_message(
            chat_id=chat_id,
            text=f"⏰ Ескерту!\n\n{message}",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error sending notification to {chat_id}: {e}")

@dp.callback_query(lambda c: c.data == "list_notifications")
async def list_notifications_handler(callback_query: CallbackQuery):
    """Handle listing all notifications"""
    try:
        chat_id = callback_query.message.chat.id
        
        if chat_id not in user_notifications or not user_notifications[chat_id]:
            await callback_query.message.edit_text(
                "📋 Сізде әлі ескертулер жоқ.\n\n"
                "Жаңа ескерту қосу үшін '➕ Жаңа ескерту қосу' батырмасын басыңыз.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="➕ Жаңа ескерту қосу", callback_data="add_notification")],
                    [InlineKeyboardButton(text="🔙 Артқа", callback_data="manage_notifications")]
                ])
            )
            return
            
        # Sort notifications by time
        notifications = sorted(
            user_notifications[chat_id],
            key=lambda x: (x['hour'], x['minute'])
        )
        
        # Create notification list text
        notifications_text = "📋 Сіздің ескертулеріңіз:\n\n"
        for i, notif in enumerate(notifications, 1):
            status = "✅" if notif['enabled'] else "❌"
            notifications_text += (
                f"{i}. ⏰ {notif['hour']:02d}:{notif['minute']:02d} "
                f"{status}\n📝 {notif['message']}\n\n"
            )
        
        # Add buttons for each notification
        keyboard = []
        for i in range(len(notifications)):
            keyboard.append([
                InlineKeyboardButton(
                    text=f"❌ #{i+1} жою",
                    callback_data=f"delete_notification_{i}"
                )
            ])
        
        keyboard.extend([
            [InlineKeyboardButton(text="➕ Жаңа ескерту қосу", callback_data="add_notification")],
            [InlineKeyboardButton(text="🔙 Артқа", callback_data="manage_notifications")]
        ])
        
        await callback_query.message.edit_text(
            notifications_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        
    except Exception as e:
        logger.error(f"Error in list_notifications_handler: {e}")
        await callback_query.answer("Қателік орын алды. Қайтадан көріңіз.")

@dp.callback_query(lambda c: c.data.startswith("delete_notification_"))
async def delete_notification_handler(callback_query: CallbackQuery):
    """Handle notification deletion"""
    try:
        chat_id = callback_query.message.chat.id
        index = int(callback_query.data.split('_')[-1])
        
        if chat_id in user_notifications and 0 <= index < len(user_notifications[chat_id]):
            notification = user_notifications[chat_id][index]
            
            # Remove the scheduled job
            job_id = f'custom_{chat_id}_{notification["hour"]}_{notification["minute"]}'
            scheduler.remove_job(job_id)
            
            # Remove from storage
            user_notifications[chat_id].pop(index)
            save_notifications()
            
            await callback_query.answer("✅ Ескерту жойылды")
            await list_notifications_handler(callback_query)
            
    except Exception as e:
        logger.error(f"Error in delete_notification_handler: {e}")
        await callback_query.answer("Қателік орын алды. Қайтадан көріңіз.")

@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main_handler(callback_query: CallbackQuery):
    """Handle back to main menu"""
    try:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🕒 Ескертулерді баптау", callback_data="manage_notifications")],
            [InlineKeyboardButton(text="📚 Ағылшын тілін үйрену", callback_data="learn_english")]
        ])
        
        await callback_query.message.edit_text(
            "Басты мәзір:\n\n"
            "• Ескертулер қою үшін '🕒 Ескертулерді баптау' батырмасын басыңыз\n"
            "• Ағылшын тілін үйрену үшін '📚 Ағылшын тілін үйрену' батырмасын басыңыз",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error in back_to_main_handler: {e}")
        await callback_query.answer("Қателік орын алды. Қайтадан көріңіз.")

@dp.message(Command('help'))
async def help_command(message: Message):
    """Handle /help command"""
    help_text = (
        "🤖 Көмек мәзірі:\n\n"
        "1️⃣ Ескертулер қою:\n"
        "   • /start батырмасын басыңыз\n"
        "   • '🕒 Ескертулерді баптау' таңдаңыз\n"
        "   • '➕ Жаңа ескерту қосу' батырмасын басыңыз\n"
        "   • Уақыт пен хабарламаны жазыңыз\n"
        "   Мысалы: 9:00 Таңғы жаттығу\n\n"
        "2️⃣ Ескертулерді көру:\n"
        "   • '📋 Ескертулер тізімі' батырмасын басыңыз\n\n"
        "3️⃣ Ескертуді жою:\n"
        "   • Ескертулер тізімінен '❌ Жою' батырмасын басыңыз\n\n"
        "4️⃣ Ағылшын тілін үйрену:\n"
        "   • '📚 Ағылшын тілін үйрену' батырмасын басыңыз\n\n"
        "❓ Қосымша сұрақтар болса, админге хабарласыңыз"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Басты мәзір", callback_data="back_to_main")]
    ])
    
    await message.reply(help_text, reply_markup=keyboard)

# Initialize notifications on startup
async def init_notifications():
    """Initialize all saved notifications on startup"""
    try:
        global user_notifications
        user_notifications = load_notifications()
        
        # Schedule all saved notifications
        for chat_id, notifications in user_notifications.items():
            for notif in notifications:
                if notif['enabled']:
                    job_id = f'custom_{chat_id}_{notif["hour"]}_{notif["minute"]}'
                    scheduler.add_job(
                        send_notification,
                        'cron',
                        hour=notif['hour'],
                        minute=notif['minute'],
                        args=[chat_id, notif['message']],
                        id=job_id,
                        replace_existing=True
                    )
        
        logger.info("Notifications initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing notifications: {e}")

async def shutdown(dispatcher: Dispatcher):
    """Cleanup resources on shutdown"""
    try:
        save_notifications()  # Save notifications before shutdown
        if scheduler.running:
            scheduler.shutdown(wait=True)
        await bot.session.close()
        logger.info("Bot shut down successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

async def main() -> None:
    """Main function to start the bot"""
    try:
        # Initialize notifications
        await init_notifications()
        
        # Start the scheduler
        if not scheduler.running:
            scheduler.start()
        
        # Set up commands
        commands_list = [
            types.BotCommand(command="start", description="Ботты қосу"),
            types.BotCommand(command="help", description="Көмек алу")
        ]
        await bot.set_my_commands(commands_list)
        
        # Start polling
        logger.info("Bot started successfully")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Critical error in main function: {e}", exc_info=True)
    finally:
        await shutdown(dp)

if __name__ == "__main__":
    asyncio.run(main())
