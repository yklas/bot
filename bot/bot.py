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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize bot
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

# Simple responses for basic greetings
BASIC_RESPONSES = {
    "сәлем": "салем қалайсыз?",
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

# User chat IDs storage
active_users = set()

@dp.message(CommandStart())
   # Вебхукті өшіру: күтуге қалдырылған хабарламаларды да өшіріп тастайды
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
async def main():

async def start_command(message: Message):
    user_id = message.from_user.id
    active_users.add(user_id)
    
    await message.answer(
        "Ассалаумағалейкум! 👋\n"
        "Мен сіздің көмекшіңізбін. Сұрақтарыңызға жауап беріп, "
        "күнделікті ескертулер жасаймын!\n\n"
        "Сұрақтарыңызды қоя беріңіз 😊"
    )
    
    # Start reminders for new user
    await schedule_reminders(user_id)

@dp.message()
async def handle_messages(message: Message):
    text = message.text.lower()
    
    if text in BASIC_RESPONSES:
        await message.answer(BASIC_RESPONSES[text])
    else:
        await message.answer("Кешіріңіз, мен сізді түсінбедім. Басқаша түсіндіріп көріңізші 😊")

async def send_scheduled_message(chat_id: int, message: str):
    try:
        await bot.send_message(chat_id, message)
    except Exception as e:
        logger.error(f"Error sending scheduled message to {chat_id}: {e}")
        active_users.discard(chat_id)  # Remove user if message fails

async def morning_reminder(chat_id: int):
    message = MORNING_MESSAGES[0]  # You can add logic to determine gender
    await send_scheduled_message(chat_id, message)

async def schedule_reminders(chat_id: int):
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    
    # Schedule daily reminders
    scheduler.add_job(morning_reminder, 'cron', hour=7, minute=0, args=[chat_id])
    scheduler.add_job(send_scheduled_message, 'cron', hour=12, minute=0, args=[chat_id, NOON_MESSAGE])
    scheduler.add_job(send_scheduled_message, 'cron', hour=16, minute=0, args=[chat_id, AFTERNOON_MESSAGE])
    scheduler.add_job(send_scheduled_message, 'cron', hour=20, minute=0, args=[chat_id, EVENING_MESSAGE])
    scheduler.add_job(send_scheduled_message, 'cron', hour=14, minute=0, args=[chat_id, SALAUAT_MESSAGE])
    
    if not scheduler.running:
        scheduler.start()

async def main():
    try:
        logger.info("Starting bot...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
