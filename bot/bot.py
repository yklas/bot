import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from datetime import datetime
import pytz
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Configuration
TELEGRAM_TOKEN = "7819420348:AAHElDNd7JI4c5gDbYD7TTe2kAWVn2TVZBo"
TIMEZONE = pytz.timezone('Asia/Almaty')

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Scheduled messages
MORNING_MESSAGES = [
    "🌅 Ерте тұрған еркектің ырысы артық! Күніңіз сәтті өтсін! 💪",
    "🌅 Ерте тұрған әйелдің бір ісі артық! Күніңіз берекелі болсын! ✨"
]

NOON_MESSAGE = "📚 Кітап оқу уақыты келді! Білім - таусылмас қазына! 📖"
AFTERNOON_MESSAGE = "🇬🇧 Қалай, бауырым, ағылшын тіліндегі жаңа сөздерді жаттадың ба? Remember - practice makes perfect! 😊"
EVENING_MESSAGE = "📝 Күн қорытындысы! Бүгінгі тапсырмаларды орындап бітірдің бе? Share your progress! 🎯"
SALAUAT_MESSAGE = "Бүгінгі салауатты ұмытпайық! Аллахумма солли 'аля саййидина Мухаммадин уа 'аля али саййидина Мухаммад"

# Basic responses dictionary
BASIC_RESPONSES = {
    "сәлем": "сәлем қалайсыз?",
    "салем": "салем қалайсыз?",
    "сәлем қалайсың": "Алхамдулиллах, жақсы! Өзіңіз қалайсыз?",
    "қалайсың": "Алхамдулиллах, жақсы! Өзіңіз қалайсыз?",
    "рахмет": "Қош келдіңіз! 🙏",
    "ассалаумағалейкум": "Уағалейкум ассалам! 😊 Қалыңыз қалай?",
    "не жаңалық": "жаңалықты ютубтан қарасаңыз болады 🙃",
    "қайырлы таң": "Қайырлы таң, баршамызға қайырлы күн болсын! 💫",
    "неге": "балға мен шеге 😆",
    "жақсымын": "жақсы болсаң менде жақсымын айналайын!😅",
    "тыныш отыр": "казір бос отыратын заман емес 😉",
    "бауырым": "бауырым ішімдегі тауірім диснго",
    "Ааа": "Ааа деме Түсінікті де",
    "Аа": "Аа деме Ааа деп айт",
    "жақсы": "еее солай де",
    "Күшті": "Күшті деме жақсы де",
    "Good morning": "Әні, ағылшынша жібереді дим",
    "😂": "күлме досқа келер басқа дейді 😌",
    "МашаАллаһ": "туф не деген имандысың ааа?",
    "мықты": "туф не деген красавчикпін 😎",
    "мыхты": "туф не деген красавчикпін 😎",
    "мықты мықты": "туф не деген красавчикпін 😎",
}

# Store active users
active_users = set()

# Initialize scheduler
scheduler = AsyncIOScheduler(timezone=TIMEZONE)

@dp.message(CommandStart())
async def start_command(message: Message):
    """Handle /start command"""
    try:
        user_id = message.from_user.id
        active_users.add(user_id)
        
        await message.answer(
            "Ассалаумағалейкум! 👋\n"
            "Мен сіздің көмекшіңізбін. Сұрақтарыңызға жауап беріп, "
            "күнделікті ескертулер жасаймын!\n\n"
            "Сұрақтарыңызды қоя беріңіз 😊"
        )
        
        await schedule_reminders(user_id)
        logger.info(f"New user started the bot: {user_id}")
    except Exception as e:
        logger.error(f"Error in start_command: {e}")
        await message.answer("Қателік орын алды. Қайтадан әрекеттеніп көріңіз.")

@dp.message()
async def handle_messages(message: Message):
    """Handle all incoming messages"""
    try:
        text = message.text.lower()
        if text in BASIC_RESPONSES:
            await message.answer(BASIC_RESPONSES[text])
        else:
            await message.answer("Кешіріңіз, мен сізді түсінбедім. Басқаша түсіндіріп көріңізші 😊")
    except Exception as e:
        logger.error(f"Error in handle_messages: {e}")
        await message.answer("Қателік орын алды. Қайтадан әрекеттеніп көріңіз.")

async def send_scheduled_message(chat_id: int, message: str):
    """Send scheduled message to user"""
    try:
        await bot.send_message(chat_id, message)
        logger.info(f"Scheduled message sent to {chat_id}")
    except Exception as e:
        logger.error(f"Error sending scheduled message to {chat_id}: {e}")
        active_users.discard(chat_id)

async def morning_reminder(chat_id: int):
    """Send morning reminder"""
    message = MORNING_MESSAGES[0]  # You can add logic to determine gender
    await send_scheduled_message(chat_id, message)

async def schedule_reminders(chat_id: int):
    """Schedule all reminders for a user"""
    try:
        # Schedule daily reminders
        scheduler.add_job(
            morning_reminder,
            'cron',
            hour=7,
            minute=0,
            args=[chat_id],
            id=f'morning_{chat_id}',
            replace_existing=True
        )
        
        # Schedule noon message
        scheduler.add_job(
            send_scheduled_message,
            'cron',
            hour=12,
            minute=0,
            args=[chat_id, NOON_MESSAGE],
            id=f'noon_{chat_id}',
            replace_existing=True
        )
        
        # Schedule afternoon message
        scheduler.add_job(
            send_scheduled_message,
            'cron',
            hour=16,
            minute=0,
            args=[chat_id, AFTERNOON_MESSAGE],
            id=f'afternoon_{chat_id}',
            replace_existing=True
        )
        
        # Schedule evening message
        scheduler.add_job(
            send_scheduled_message,
            'cron',
            hour=20,
            minute=0,
            args=[chat_id, EVENING_MESSAGE],
            id=f'evening_{chat_id}',
            replace_existing=True
        )
        
        # Schedule salauat message
        scheduler.add_job(
            send_scheduled_message,
            'cron',
            hour=14,
            minute=0,
            args=[chat_id, SALAUAT_MESSAGE],
            id=f'salauat_{chat_id}',
            replace_existing=True
        )
        
        if not scheduler.running:
            scheduler.start()
        
        logger.info(f"Reminders scheduled for user {chat_id}")
    except Exception as e:
        logger.error(f"Error scheduling reminders for {chat_id}: {e}")

async def main():
    """Main function to run the bot"""
    try:
        logger.info("Starting bot...")
        # Delete webhook before polling
        await bot.delete_webhook(drop_pending_updates=True)
        # Start polling
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
    finally:
        # Proper cleanup
        await bot.session.close()
        scheduler.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
