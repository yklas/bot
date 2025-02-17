import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from datetime import datetime
import pytz
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import random
from typing import List, Dict

# Configuration
TELEGRAM_TOKEN = "7819420348:AAHElDNd7JI4c5gDbYD7TTe2kAWVn2TVZBo"
TIMEZONE = pytz.timezone('Asia/Almaty')

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# English learning content
ENGLISH_QUESTIONS = [
    {
        "image_url": "/api/placeholder/400/300",
        "question": "What season is shown in this picture?",
        "options": ["Spring", "Summer", "Autumn", "Winter"],
        "correct": "Spring",
        "translation": "Суретте қай мезгіл көрсетілген?"
    },
    {
        "image_url": "/api/placeholder/400/300",
        "question": "What weather is it in the image?",
        "options": ["Sunny", "Rainy", "Cloudy", "Snowy"],
        "correct": "Sunny",
        "translation": "Суретте қандай ауа райы?"
    },
    {
        "image_url": "/api/placeholder/400/300",
        "question": "What type of landscape is this?",
        "options": ["Mountain", "Beach", "Forest", "Desert"],
        "correct": "Mountain",
        "translation": "Бұл қандай ландшафт түрі?"
    },
    {
        "image_url": "/api/placeholder/400/300",
        "question": "What time of day is shown?",
        "options": ["Morning", "Noon", "Evening", "Night"],
        "correct": "Morning",
        "translation": "Тәуліктің қай мезгілі көрсетілген?"
    }
]

# User progress tracking
user_progress = {}

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

def get_english_menu() -> InlineKeyboardMarkup:
    """Create English learning menu"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇬🇧 Ағылшын тілін үйрену", callback_data="learn_english")],
        [InlineKeyboardButton(text="📊 Менің прогрессім", callback_data="my_progress")]
    ])
    return keyboard

async def send_english_question(chat_id: int) -> None:
    """Send a random English question to user"""
    question = random.choice(ENGLISH_QUESTIONS)
    
    # Create options keyboard
    options_keyboard = []
    for option in question["options"]:
        options_keyboard.append([InlineKeyboardButton(
            text=option,
            callback_data=f"answer_{option}"
        )])
    
    markup = InlineKeyboardMarkup(inline_keyboard=options_keyboard)
    
    # Send question with image
    await bot.send_photo(
        chat_id=chat_id,
        photo=question["image_url"],
        caption=f"{question['question']}\n\n{question['translation']}",
        reply_markup=markup
    )
    
    # Store current question for user
    user_progress[chat_id] = {"current_question": question}

@dp.callback_query(lambda c: c.data == "learn_english")
async def process_learn_english(callback_query: CallbackQuery):
    """Handle English learning button click"""
    await callback_query.answer()
    await send_english_question(callback_query.from_user.id)

@dp.callback_query(lambda c: c.data.startswith("answer_"))
async def process_answer(callback_query: CallbackQuery):
    """Handle answer selection"""
    user_id = callback_query.from_user.id
    selected_answer = callback_query.data.replace("answer_", "")
    
    if user_id in user_progress and "current_question" in user_progress[user_id]:
        current_question = user_progress[user_id]["current_question"]
        
        if selected_answer == current_question["correct"]:
            await callback_query.answer("🎉 Дұрыс! / Correct!")
            # Update user progress
            if "correct_answers" not in user_progress[user_id]:
                user_progress[user_id]["correct_answers"] = 0
            user_progress[user_id]["correct_answers"] += 1
        else:
            await callback_query.answer(
                f"❌ Қате! Дұрыс жауап: {current_question['correct']}\n"
                f"Wrong! The correct answer is: {current_question['correct']}"
            )
        
        # Send new question after delay
        await asyncio.sleep(2)
        await send_english_question(user_id)

@dp.callback_query(lambda c: c.data == "my_progress")
async def show_progress(callback_query: CallbackQuery):
    """Show user's learning progress"""
    user_id = callback_query.from_user.id
    
    if user_id in user_progress and "correct_answers" in user_progress[user_id]:
        correct = user_progress[user_id]["correct_answers"]
        await callback_query.answer(
            f"Сіздің жетістіктеріңіз: {correct} дұрыс жауап!\n"
            f"Your progress: {correct} correct answers!"
        )
    else:
        await callback_query.answer(
            "Сіз әлі тест тапсырған жоқсыз.\n"
            "You haven't taken any tests yet."
        )

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
            "Төмендегі батырмаларды басып, ағылшын тілін үйрене аласыз!",
            reply_markup=get_english_menu()
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
            await message.answer(BASIC_RESPONSES[text], reply_markup=get_english_menu())
        else:
            await message.answer(
                "Кешіріңіз, мен сізді түсінбедім. Басқаша түсіндіріп көріңізші 😊",
                reply_markup=get_english_menu()
            )
    except Exception as e:
        logger.error(f"Error in handle_messages: {e}")
        await message.answer("Қателік орын алды. Қайтадан әрекеттеніп көріңіз.")

async def send_scheduled_message(chat_id: int, message: str):
    """Send scheduled message to user"""
    try:
        await bot.send_message(chat_id, message, reply_markup=get_english_menu())
        logger.info(f"Scheduled message sent to {chat_id}")
    except Exception as e:
        logger.error(f"Error sending scheduled message to {chat_id}: {e}")
        active_users.discard(chat_id)

async def morning_reminder(chat_id: int):
    """Send morning reminder"""
    message = MORNING_MESSAGES[0]
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
        
        # Schedule daily English questions
        for hour in [9, 13, 17, 21]:  # 4 times per day
            scheduler.add_job(
                send_english_question,
                'cron',
                hour=hour,
                minute=0,
                args=[chat_id],
                id=f'english_{hour}_{chat_id}',
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
