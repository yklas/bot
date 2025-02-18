import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from datetime import datetime
import pytz
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import random
from typing import List, Dict

# Configuration
TELEGRAM_TOKEN = "7819420348:AAHElDNd7JI4c5gDbYD7TTe2kAWVn2TVZBo"
TIMEZONE = pytz.timezone('Asia/Almaty')

# Logging setup with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Initialize scheduler with explicit timezone and job defaults
scheduler = AsyncIOScheduler(
    timezone=TIMEZONE,
    job_defaults={
        'misfire_grace_time': 300,  # 5 minutes grace time
        'coalesce': True,
        'max_instances': 1
    }
)

# Store active users and group chats
active_users = set()
group_ids = set()

# English learning content
ENGLISH_QUESTIONS = [
    {
        "id": "1",
        "image_url": "https://m.media-amazon.com/images/I/514nTHwlFnL.jpg",
        "question": "Тамақ ішкен кезде қолданатын бұл зат қалай аталады?",
        "options": ["Spoon", "Fork", "Knife", "Plate"],
        "correct": "Spoon",
    },
    {
        "id": "2",
        "image_url": "https://www.kitchenstuffplus.com/media/catalog/product/7/3/7398_hauz-stovetop-kettle_230914133830626_ldk9f98hlpmd9nxf.jpg",
        "question": "Ас үйде су қайнату үшін қолданатын құрылғы қалай аталады?",
        "options": ["Kettle", "Toaster", "Blender", "Bucket"],
        "correct": "Kettle",
    },
    # ... rest of your questions ...
]

# Basic responses dictionary
BASIC_RESPONSES = {
    "сәлем": "сәлем қалайсыз?",
    "салем": "салем қалайсыз?",
    "сәлем қалайсың": "Алхамдулиллах, жақсы! Өзіңіз қалайсыз?",
    # ... rest of your responses ...
}

# Scheduled messages
MORNING_MESSAGES = [
    "🌅 Ерте тұрған еркектің ырысы артық! Күніңіз сәтті өтсін! 💪",
    "🌅 Ерте тұрған әйелдің бір ісі артық! Күніңіз берекелі болсын! ✨"
]

NOON_MESSAGE = "📚 Кітап оқу уақыты келді! Білім - таусылмас қазына! 📖"
AFTERNOON_MESSAGE = "🇬🇧 Қалай, бауырым, ағылшын тіліндегі жаңа сөздерді жаттадың ба? Remember - practice makes perfect! 😊"
EVENING_MESSAGE = "📝 Күн қорытындысы! Бүгінгі күнің біліммен өттіма, әлде пайдасыз іспен өттіма? Share your progress! 🎯"
SALAUAT_MESSAGE = "Бүгінгі салауатты ұмытпайық! Аллахумма солли 'аля саййидина Мухаммадин уа 'аля али саййидина Мухаммад"

# Group messages
GROUP_MESSAGES = {
    'morning': [
        "🌅 Қайырлы таң, достар!\nБүгін де жаңа білім күтіп тұр! Қане, белсенді болайық! 💪",
        # ... rest of morning messages ...
    ],
    'english': [
        "🇬🇧 Ағылшын тілі уақыты!\nҚәне, достар, жаңа сөздер үйренейік! 🎯",
        # ... rest of english messages ...
    ],
    # ... rest of group messages ...
}

# English schedule
english_schedule = [
    {'hour': 9, 'minute': 0},
    {'hour': 14, 'minute': 46},
    {'hour': 17, 'minute': 0},
    {'hour': 21, 'minute': 0}
]

# User progress tracking
user_progress: Dict[int, Dict] = {}

async def send_scheduled_message(chat_id: int, message: str):
    """Send scheduled message to user or group"""
    try:
        keyboard = get_english_menu() if chat_id not in group_ids else None
        await bot.send_message(chat_id, message, reply_markup=keyboard)
        logger.info(f"Scheduled message sent to {chat_id}")
    except Exception as e:
        logger.error(f"Error sending scheduled message to {chat_id}: {e}")
        if chat_id in active_users:
            active_users.discard(chat_id)
        if chat_id in group_ids:
            group_ids.discard(chat_id)

async def send_english_question(chat_id: int) -> None:
    """Send English learning question to chat"""
    try:
        asked_questions = user_progress.get(chat_id, {}).get("asked_questions", [])
        available_questions = [q for q in ENGLISH_QUESTIONS if q["id"] not in asked_questions]
        
        if not available_questions:
            asked_questions = []
            available_questions = ENGLISH_QUESTIONS
        
        question = random.choice(available_questions)
        
        if chat_id not in user_progress:
            user_progress[chat_id] = {
                "asked_questions": [],
                "current_question": None,
                "correct_answers": 0,
                "questions_answered": 0
            }
        
        user_progress[chat_id]["current_question"] = question
        user_progress[chat_id]["asked_questions"] = asked_questions + [question["id"]]
        
        options_keyboard = []
        for option in question["options"]:
            callback_data = f"answer_{question['id']}_{option}"
            options_keyboard.append([InlineKeyboardButton(text=option, callback_data=callback_data)])
        
        markup = InlineKeyboardMarkup(inline_keyboard=options_keyboard)
        
        try:
            await bot.send_photo(
                chat_id=chat_id,
                photo=question["image_url"],
                caption=f"❓ {question['question']}",
                reply_markup=markup
            )
        except Exception as photo_error:
            logger.error(f"Error sending photo: {photo_error}")
            await bot.send_message(
                chat_id=chat_id,
                text=f"❓ {question['question']}",
                reply_markup=markup
            )
    except Exception as e:
        logger.error(f"Error in send_english_question: {e}")
        await bot.send_message(
            chat_id=chat_id,
            text="Қателік орын алды. Қайтадан көріңіз. /start"
        )

async def schedule_reminders(chat_id: int):
    """Schedule all reminders for a user or group"""
    try:
        logger.info(f"Starting to schedule reminders for chat {chat_id}")
        
        # Remove existing jobs for this chat
        for job in scheduler.get_jobs():
            if str(chat_id) in job.id:
                scheduler.remove_job(job.id)
                logger.info(f"Removed existing job {job.id}")
        
        # Define schedules with explicit triggers
        schedules = [
            {
                'id': f'morning_{chat_id}',
                'trigger': CronTrigger(hour=7, minute=0, timezone=TIMEZONE),
                'message': random.choice(MORNING_MESSAGES)
            },
            {
                'id': f'noon_{chat_id}',
                'trigger': CronTrigger(hour=10, minute=0, timezone=TIMEZONE),
                'message': NOON_MESSAGE
            },
            {
                'id': f'afternoon_{chat_id}',
                'trigger': CronTrigger(hour=16, minute=0, timezone=TIMEZONE),
                'message': AFTERNOON_MESSAGE
            },
            {
                'id': f'evening_{chat_id}',
                'trigger': CronTrigger(hour=20, minute=0, timezone=TIMEZONE),
                'message': EVENING_MESSAGE
            },
            {
                'id': f'salauat_{chat_id}',
                'trigger': CronTrigger(hour=22, minute=0, timezone=TIMEZONE),
                'message': SALAUAT_MESSAGE
            }
        ]
        
        # Add English learning schedules
        for time in english_schedule:
            schedules.append({
                'id': f'english_{chat_id}_{time["hour"]}_{time["minute"]}',
                'trigger': CronTrigger(hour=time['hour'], minute=time['minute'], timezone=TIMEZONE),
                'func': send_group_english_activity,
                'args': [chat_id]
            })
        
        # Schedule all jobs
        for schedule in schedules:
            if 'func' in schedule:
                scheduler.add_job(
                    schedule['func'],
                    trigger=schedule['trigger'],
                    args=schedule['args'],
                    id=schedule['id'],
                    replace_existing=True
                )
            else:
                scheduler.add_job(
                    send_scheduled_message,
                    trigger=schedule['trigger'],
                    args=[chat_id, schedule['message']],
                    id=schedule['id'],
                    replace_existing=True
                )
            logger.info(f"Scheduled job {schedule['id']}")
        
        # Verify scheduled jobs
        current_jobs = scheduler.get_jobs()
        logger.info(f"Currently scheduled jobs for chat {chat_id}: {[job.id for job in current_jobs]}")
        
        # Log next run times
        for job in current_jobs:
            if str(chat_id) in job.id:
                logger.info(f"Next run time for {job.id}: {job.next_run_time}")
        
    except Exception as e:
        logger.error(f"Error scheduling reminders for {chat_id}: {e}")
        raise

# Command handlers
@dp.message(CommandStart())
async def start_command(message: Message):
    """Handle /start command"""
    try:
        chat_id = message.chat.id
        
        if message.chat.type in ['group', 'supergroup']:
            group_ids.add(chat_id)
            group_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📚 Ағылшын тілін үйрену", callback_data="learn_english")]
            ])
            await message.reply(
                "Ассалаумағалейкум, топ мүшелері! 👋\n\n"
                "Мен сіздердің көмекшілеріңізбін!\n"
                "🎯 Менің мүмкіндіктерім:\n"
                "- Күнделікті ағылшын тілі сабақтары\n"
                "- Топ белсенділігін арттыру\n"
                "- Қызықты тапсырмалар\n"
                "- Пайдалы ескертулер\n\n"
                "Топта белсенді болыңыздар! 🌟",
                reply_markup=group_keyboard
            )
            await schedule_group_activities(chat_id)
        else:
            active_users.add(chat_id)
            await message.reply(
                "Ассалаумағалейкум! 👋\n"
                "Мен сіздің көмекшіңізбін. Сұрақтарыңызға жауап беріп, "
                "күнделікті ескертулер жасаймын!\n\n"
                "Төмендегі батырмаларды басып, ағылшын тілін үйрене аласыз!",
                reply_markup=get_english_menu()
            )
            await schedule_reminders(chat_id)
        
        logger.info(f"Bot started in chat: {chat_id}")
    except Exception as e:
        logger.error(f"Error in start_command: {e}")
        await message.reply("Қателік орын алды. Қайтадан әрекеттеніп көріңіз.")

@dp.message(Command('help'))
async def help_command(message: Message):
    """Handle /help command"""
    help_text = (
        "🤖 *Менің мүмкіндіктерім:*\n\n"
        "🔹 /start - Ботты іске қосу\n"
        "🔹 /help - Көмек алу\n"
        "🔹 /schedule - Хабарламалар кестесін қарау\n\n"
        "📚 Ағылшын тілін үйрену мүмкіндігін пайдалану үшін тиісті батырманы басыңыз.\n"
        "🕘 Ескертулер күн бойы белгіленген уақытта жіберіледі.\n"
        "❓ Мәтіндік сұрақтарға автоматты түрде жауап беремін.\n\n"
        "📱 Тапсырмаларды орындап, біліміңізді жетілдіріңіз!"
    )
    try:
        keyboard = get_english_menu() if message.chat.type == 'private' else InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="📚 Ағылшын тілін үйрену", callback_data="learn_english")]]
        )
        await message.answer(help_text, reply_markup=keyboard, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error in help_command: {e}")
        await message.answer("Қателік орын алды. ")

@dp.message(Command('schedule'))
async def schedule_command(message: Message):
    """Handle /schedule command to show daily schedule"""
    schedule_text = (
        "📅 *Күнделікті кесте:*\n\n"
        "🌅 07:00 - Таңғы уәж\n"
        "📚 10:00 - Кітап оқу уақыты\n"
        "🇬🇧 Ағылшын тілі сабақтары:\n"
        "   • 09:00\n"
        "   • 14:35\n"
        "   • 17:00\n"
        "   • 21:00\n"
        "📝 20:00 - Күн қорытындысы\n"
        "🤲 22:00 - Салауат айту\n\n"
        "⏰ Барлық хабарламалар Алматы уақыты бойынша жіберіледі."
    )
    try:
        await message.answer(schedule_text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error in schedule_command: {e}")
        await message.answer("Кесте көрсету кезінде қателік орын алды.")

async def send_group_english_activity(chat_id: int):
    """Send English learning activity to group"""
    try:
        message = random.choice(GROUP_MESSAGES['english'])
        question = random.choice(ENGLISH_QUESTIONS)
        
        options_keyboard = []
        for option in question["options"]:
            callback_data = f"group_answer_{question['id']}_{option}"
            options_keyboard.append([InlineKeyboardButton(text=option, callback_data=callback_data)])
        
        markup = InlineKeyboardMarkup(inline_keyboard=options_keyboard)
        
        await bot.send_message(chat_id, message)
        await bot.send_photo(
            chat_id=chat_id,
            photo=question["image_url"],
            caption=f"❓ {question['question']}",
            reply_markup=markup
        )
    except Exception as e:
        logger.error(f"Error in send_group_english_activity: {e}")
        if chat_id in group_ids:
            group_ids.discard(chat_id)

async def schedule_group_activities(chat_id: int):
    """Schedule activities for group chats"""
    try:
        # Morning message
        scheduler.add_job(
            send_scheduled_message,
            trigger=CronTrigger(hour=7, minute=0, timezone=TIMEZONE),
            args=[chat_id, random.choice(GROUP_MESSAGES['morning'])],
            id=f'group_morning_{chat_id}',
            replace_existing=True
        )
        
        # English learning sessions
        for time in english_schedule:
            scheduler.add_job(
                send_group_english_activity,
                trigger=CronTrigger(hour=time['hour'], minute=time['minute'], timezone=TIMEZONE),
                args=[chat_id],
                id=f'group_english_{chat_id}_{time["hour"]}_{time["minute"]}',
                replace_existing=True
            )
        
        logger.info(f"Group activities scheduled for chat {chat_id}")
    except Exception as e:
        logger.error(f"Error scheduling group activities for {chat_id}: {e}")

@dp.callback_query(lambda c: c.data.startswith(('answer_', 'group_answer_')))
async def process_answer(callback_query: CallbackQuery):
    """Process answers for English learning questions"""
    try:
        chat_id = callback_query.message.chat.id
        user_id = callback_query.from_user.id
        is_group = callback_query.data.startswith('group_answer_')
        
        # Extract question ID and selected answer
        parts = callback_query.data.split('_')
        question_id = parts[2] if is_group else parts[1]
        selected_answer = parts[3] if is_group else parts[2]
        
        # Find the correct question
        question = next((q for q in ENGLISH_QUESTIONS if q["id"] == question_id), None)
        if not question:
            await callback_query.answer("Қателік орын алды. Қайтадан көріңіз.")
            return
        
        # Check if the answer is correct
        is_correct = selected_answer == question["correct"]
        
        # Update user progress
        if chat_id not in user_progress:
            user_progress[chat_id] = {
                "asked_questions": [],
                "correct_answers": 0,
                "questions_answered": 0
            }
        
        user_progress[chat_id]["questions_answered"] += 1
        if is_correct:
            user_progress[chat_id]["correct_answers"] += 1
        
        # Calculate success rate
        success_rate = (user_progress[chat_id]["correct_answers"] / 
                       user_progress[chat_id]["questions_answered"] * 100)
        
        # Prepare response message
        if is_correct:
            response = f"✅ Дұрыс! '{selected_answer}' - дұрыс жауап!\n\n"
        else:
            response = f"❌ Қате! Дұрыс жауап: '{question['correct']}'\n\n"
        
        response += f"📊 Жетістік: {success_rate:.1f}%"
        
        # Send response
        await callback_query.message.reply(response)
        
        # Send new question after delay
        if not is_group:
            await asyncio.sleep(2)
            await send_english_question(chat_id)
        
    except Exception as e:
        logger.error(f"Error in process_answer: {e}")
        await callback_query.answer("Қателік орын алды. Қайтадан көріңіз.")

def get_english_menu() -> InlineKeyboardMarkup:
    """Create English learning menu keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 Ағылшын тілін үйрену", callback_data="learn_english")],
        [InlineKeyboardButton(text="📊 Жетістіктерім", callback_data="my_progress")]
    ])

@dp.callback_query(lambda c: c.data == "learn_english")
async def start_english_learning(callback_query: CallbackQuery):
    """Start English learning session"""
    try:
        chat_id = callback_query.message.chat.id
        await send_english_question(chat_id)
    except Exception as e:
        logger.error(f"Error in start_english_learning: {e}")
        await callback_query.answer("Қателік орын алды. Қайтадан көріңіз.")

@dp.callback_query(lambda c: c.data == "my_progress")
async def show_progress(callback_query: CallbackQuery):
    """Show user's learning progress"""
    try:
        chat_id = callback_query.message.chat.id
        progress = user_progress.get(chat_id, {
            "correct_answers": 0,
            "questions_answered": 0
        })
        
        if progress["questions_answered"] == 0:
            await callback_query.message.reply(
                "📊 Сіз әлі тапсырма орындаған жоқсыз.\n"
                "Ағылшын тілін үйренуді бастау үшін тиісті батырманы басыңыз!",
                reply_markup=get_english_menu()
            )
        else:
            success_rate = (progress["correct_answers"] / 
                          progress["questions_answered"] * 100)
            
            await callback_query.message.reply(
                f"📊 *Сіздің жетістіктеріңіз:*\n\n"
                f"✅ Дұрыс жауаптар: {progress['correct_answers']}\n"
                f"📝 Барлық жауаптар: {progress['questions_answered']}\n"
                f"🎯 Жетістік: {success_rate:.1f}%",
                parse_mode="Markdown",
                reply_markup=get_english_menu()
            )
    except Exception as e:
        logger.error(f"Error in show_progress: {e}")
        await callback_query.answer("Қателік орын алды. Қайтадан көріңіз.")

async def main():
    """Main function to start the bot"""
    try:
        logger.info("Starting bot...")
        scheduler.start()
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error in main function: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
