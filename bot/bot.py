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
    {
        "id": "3",
        "image_url": "https://www.oates.com.au/medias/VC-Prod-Sell-Slot-null?context=bWFzdGVyfHJvb3R8MTg3MjI4fGltYWdlL3BuZ3xhREpoTDJneU1TODVOVE0xTkRJM05ERXhPVGs0TDFaRFgxQnliMlJmVTJWc2JGOVRiRzkwWDI1MWJHd3w3ZmVkZTc0Y2QzMWU4ZjAxMmFiM2NlM2M4NDYxYjY0NzQyNTAyYTM0YjdkNDNiZmFlMjU3N2RiYmU3NWVkYjIw",
        "question": "Үйдегі еденді тазалау үшін қолданатын бұл зат қалай аталады?",
        "options": ["Mop", "Broom", "Rug", "Bucket"],
        "correct": "Broom",
    },
    {
        "id": "4",
        "image_url": "https://www.thefurnituremarket.co.uk/media/catalog/product/cache/e87de9c08ea8cd93ad1e6aad80c8118c/r/c/rc15-cotswold-rustic-oak-double-wardrobe-1.jpg",
        "question": "Киімдерді жинап, сақтау үшін қолданатын бұл зат қалай аталады?",
        "options": ["Sofa", "Mirror", "Wardrobe", "Table"],
        "correct": "Wardrobe",
    },
       {
        "id": "5",
        "image_url": "https://hips.hearstapps.com/hmg-prod/images/best-washing-machines-6580810397efc.png?crop=0.405xw:0.811xh;0.300xw,0.0962xh&resize=1200:*",
        "question": "Киімді жуу үшін қолданатын бұл зат қалай аталады?",
        "options": ["Vacuum cleaner", "Washing machine", "Iron", "Blender"],
        "correct": "Washing machine",
    },
       {
        "id": "6",
        "image_url": "https://images-cdn.ubuy.co.in/65979c2cb910f53d2e6e34ae-3-5cu-ft-compact-refrigerator-mini.jpg",
        "question": "Тамақты тоңазытқышта сақтау үшін қолданатын бұл зат қалай аталады?",
        "options": ["Fridge", "Stove", "Dishwasher", "Sink"],
        "correct": "Fridge",
    },
       {
        "id": "7",
        "image_url": "https://wallniture.com/cdn/shop/files/wallniture_forte_lgo420_shelf_bur_woo_lvr_rn_ls_v2_2000x2000_59323fb2-d661-4b66-8d4c-362c39b73901.jpg?v=1718376884&width=2500",
        "question": "Кітаптар мен басқа да заттарды қою үшін қолданатын затты қалай атайды?",
        "options": ["Chair", "Pillow", "Curtain", "Shelf"],
        "correct": "Shelf",
    },
       {
        "id": "8",
        "image_url": "https://www.nilkamalfurniture.com/cdn/shop/files/Mozart_66bfc296-2982-4ee1-883a-50e80a422835_600x.jpg?v=1728031239",
        "question": "Түнде ұйықтау үшін қолданатын затты қалай атайды?",
        "options": ["Bed", "Carpet", "Drawer", "Door"],
        "correct": "Bed",
    },
       {
        "id": "9",
        "image_url": "https://m.media-amazon.com/images/I/31CPVoKIJmL.jpg",
        "question": "Су ішетін ыдыс қалай аталады?",
        "options": ["Kettle", "Spoon", "Plate", "Glass"],
        "correct": "Glass",
    },
       {
        "id": "10",
        "image_url": "https://wondershop.sg/media/catalog/product/d/s/dst8020_20_pis_16x9.png?optimize=high&bg-color=255,255,255&fit=bounds&height=700&width=700&canvas=700:700",
        "question": "Киім үтіктеу үшін қолданатын зат не деп аталады?",
        "options": ["Fan", "Toaster", "Iron", "Vaccum cleaner"],
        "correct": "Iron",
    },
]

# User progress tracking
user_progress: Dict[int, Dict] = {}

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

# Scheduled messages
MORNING_MESSAGES = [
    "🌅 Ерте тұрған еркектің ырысы артық! Күніңіз сәтті өтсін! 💪",
    "🌅 Ерте тұрған әйелдің бір ісі артық! Күніңіз берекелі болсын! ✨"
]

NOON_MESSAGE = "📚 Кітап оқу уақыты келді! Білім - таусылмас қазына! 📖"
AFTERNOON_MESSAGE = "🇬🇧 Қалай, бауырым, ағылшын тіліндегі жаңа сөздерді жаттадың ба? Remember - practice makes perfect! 😊"
EVENING_MESSAGE = "📝 Күн қорытындысы! Бүгінгі күнің біліммен өттіма, әлде пайдасыз іспен өттіма? Share your progress! 🎯"
SALAUAT_MESSAGE = "Бүгінгі салауатты ұмытпайық! Аллахумма солли 'аля саййидина Мухаммадин уа 'аля али саййидина Мухаммад"

# Initialize scheduler
scheduler = AsyncIOScheduler(timezone=TIMEZONE)
GROUP_CHAT_ID = "-2385835678" 

# Scheduled messages жаңарту
GROUP_MESSAGES = {
    'morning': [
        "🌅 Қайырлы таң, достар!\nБүгін де жаңа білім күтіп тұр! Қане, белсенді болайық! 💪",
        "🌅 Таң нұрлы, көңіл-күй көтеріңкі!\nБүгін тағы да қызықты тапсырмалар күтіп тұр! 🌟",
        "🌅 Жаңа күн - жаңа мүмкіндіктер!\nБілімге құштар болайық! 📚"
    ],
    'english': [
        "🇬🇧 Ағылшын тілі уақыты!\nҚәне, достар, жаңа сөздер үйренейік! 🎯",
        "🇬🇧 English Time!\nБүгінгі жаңа сөздерді үйренуге дайынсыздар ма? 📝",
        "🇬🇧 Let's learn English!\nЖаңа сөздер мен сөз тіркестерін үйренетін уақыт келді! 🎓"
    ],
    'activity': [
        "🎯 Белсенділік уақыты!\nТопта кім бар? Қандай жаңалықтар бар? 😊",
        "💫 Достар, қалайсыздар?\nБүгін қандай жетістіктерге жеттіңіздер? 🌟",
        "🎉 Топ белсенділігін арттыратын уақыт!\nБір-бірімізге қолдау көрсетейік! 💪"
    ],
    'book': [
        "📚 Кітап оқып жатсыңдар ма? Бүгін қандай кітап оқып жатырсыздар? 📖",
        "📚 Кітап - білім бұлағы! Күнде 20 минут оқу арқылы көп білім алуға болады! 📚",
        "📚 Достар, бүгін қандай пайдалы кітап оқып жатырсыздар? Бөлісіңіздер! 📖"
    ]
}

async def send_group_english_activity(chat_id: int):
    """Send interactive English activity to group"""
    try:
        # Жаңа сұрақ жіберу
        intro_message = random.choice(GROUP_MESSAGES['english'])
        await bot.send_message(chat_id, intro_message)
        await asyncio.sleep(2)  # Кішкене үзіліс
        await send_english_question(chat_id)
    except Exception as e:
        logger.error(f"Error sending group English activity: {e}")

async def send_group_activity_prompt(chat_id: int):
    """Send activity prompt to group"""
    try:
        message = random.choice(GROUP_MESSAGES['activity'])
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📚 Ағылшын тілін үйрену", callback_data="learn_english")],
            [InlineKeyboardButton(text="💭 Пікір қалдыру", callback_data="leave_feedback")]
        ])
        await bot.send_message(chat_id, message, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error sending group activity prompt: {e}")

async def send_book_reminder(chat_id: int):
    """Send book reading reminder"""
    try:
        message = random.choice(GROUP_MESSAGES['book'])
        await bot.send_message(chat_id, message)
    except Exception as e:
        logger.error(f"Error sending book reminder: {e}")

# Сағат пен минутты жаңартылған уақыттарға сәйкес реттеу
english_schedule = [
    {'hour': 9, 'minute': 00},
    {'hour': 13, 'minute': 30},
    {'hour': 17, 'minute': 00},
    {'hour': 21, 'minute': 00}
]

async def schedule_group_activities(chat_id: int):
    """Schedule group-specific activities"""
    try:
        # Таңғы сәлемдесу - 7:00
        scheduler.add_job(
            send_scheduled_message,
            'cron',
            hour=7,
            minute=0,
            args=[chat_id, random.choice(GROUP_MESSAGES['morning'])],
            id=f'group_morning_{chat_id}',
            replace_existing=True
        )

        # Кітап оқу ескертуі - 10:00
        scheduler.add_job(
            send_book_reminder,
            'cron',
            hour=10,
            minute=0,
            args=[chat_id],
            id=f'group_book_{chat_id}',
            replace_existing=True
        )

        # Ағылшын тілі белсенділіктері - 16:00
        scheduler.add_job(
            send_scheduled_message,
            'cron',
            hour=16, 
            minute=0,
            args=[chat_id, AFTERNOON_MESSAGE],
            id=f'group_afternoon_{chat_id}',
            replace_existing=True
        )

        # Күн қорытындысы - 20:00
        scheduler.add_job(
            send_scheduled_message,
            'cron',
            hour=20,
            minute=0,
            args=[chat_id, EVENING_MESSAGE],
            id=f'group_evening_{chat_id}',
            replace_existing=True
        )

        # Салауат ескертуі - 22:00
        scheduler.add_job(
            send_scheduled_message,
            'cron',
            hour=22,
            minute=0,
            args=[chat_id, SALAUAT_MESSAGE],
            id=f'group_salauat_{chat_id}',
            replace_existing=True
        )

        # Ағылшын тілі белсенділіктері
        for schedule in english_schedule:
            scheduler.add_job(
                send_group_english_activity,
                'cron',
                hour=schedule['hour'],
                minute=schedule['minute'],
                args=[chat_id],
                id=f'group_english_{schedule["hour"]}_{schedule["minute"]}_{chat_id}',
                replace_existing=True
            )

        logger.info(f"Group activities scheduled for chat {chat_id}")
    except Exception as e:
        logger.error(f"Error scheduling group activities: {e}")

def get_english_menu() -> InlineKeyboardMarkup:
    """Create main menu keyboard"""
    keyboard = [
        [InlineKeyboardButton(text="📚 Ағылшын тілін үйрену", callback_data="learn_english")],
        [InlineKeyboardButton(text="📊 Менің жетістіктерім", callback_data="my_progress")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def send_english_question(chat_id: int) -> None:
    """Send English learning question to chat"""
    try:
        # Get previously asked questions for this chat
        asked_questions = user_progress.get(chat_id, {}).get("asked_questions", [])
        
        # Filter out questions that haven't been asked yet
        available_questions = [q for q in ENGLISH_QUESTIONS if q["id"] not in asked_questions]
        
        # If all questions have been asked, reset the list
        if not available_questions:
            asked_questions = []
            available_questions = ENGLISH_QUESTIONS
        
        # Select a random question
        question = random.choice(available_questions)
        
        # Initialize or update user progress
        if chat_id not in user_progress:
            user_progress[chat_id] = {
                "asked_questions": [],
                "current_question": None,
                "correct_answers": 0,
                "questions_answered": 0
            }
        
        # Update current question and asked questions
        user_progress[chat_id]["current_question"] = question
        user_progress[chat_id]["asked_questions"] = asked_questions + [question["id"]]
        
        # Create keyboard with options
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
            logger.info(f"Question {question['id']} sent successfully to chat {chat_id}")
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

@dp.callback_query(lambda c: c.data == "learn_english")
async def start_learning(callback_query: CallbackQuery):
    """Handle learn English button"""
    try:
        chat_id = callback_query.message.chat.id
        await callback_query.answer()
        await send_english_question(chat_id)
    except Exception as e:
        logger.error(f"Error in start_learning: {e}")
        await callback_query.message.answer("Қателік орын алды. Қайтадан көріңіз.")

@dp.callback_query(lambda c: c.data.startswith("answer_"))
async def process_answer(callback_query: CallbackQuery):
    """Handle answer selection"""
    try:
        chat_id = callback_query.message.chat.id
        _, question_id, selected_answer = callback_query.data.split("_")
        
        # Initialize progress if not exists
        if chat_id not in user_progress:
            user_progress[chat_id] = {
                "asked_questions": [],
                "current_question": None,
                "correct_answers": 0,
                "questions_answered": 0,
                "last_question_message": None  # Add this to track the last question message
            }
        
        current_question = user_progress[chat_id].get("current_question")
        
        if current_question and current_question["id"] == question_id:
            # Remove the old keyboard
            await callback_query.message.edit_reply_markup(reply_markup=None)
            
            # Store result message for later deletion
            if selected_answer == current_question["correct"]:
                user_progress[chat_id]["correct_answers"] += 1
                result_message = await callback_query.message.reply("🎉 Дұрыс! / Correct!")
            else:
                result_message = await callback_query.message.reply(
                    f"❌ Қате! Дұрыс жауап: {current_question['correct']}"
                )
            
            user_progress[chat_id]["questions_answered"] += 1
            
            # Send result message with next question button
            result_text = (
                f"✅ Дұрыс жауаптар: {user_progress[chat_id]['correct_answers']}\n"
                f"📝 Барлық жауаптар: {user_progress[chat_id]['questions_answered']}"
            )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📚 Келесі сұрақ", callback_data="next_question")],
                [InlineKeyboardButton(text="🔙 Басты мәзір", callback_data="main_menu")]
            ])
            
            status_message = await callback_query.message.reply(result_text, reply_markup=keyboard)
            
            # Store messages to be deleted when moving to next question
            user_progress[chat_id]["last_question_message"] = {
                "question": callback_query.message,
                "result": result_message,
                "status": status_message
            }
        
    except Exception as e:
        logger.error(f"Error in process_answer: {e}")
        await callback_query.message.reply("Қателік орын алды. Қайтадан көріңіз.")

@dp.callback_query(lambda c: c.data == "next_question")
async def next_question(callback_query: CallbackQuery):
    """Handle next question button"""
    try:
        await callback_query.answer()
        chat_id = callback_query.message.chat.id
        
        # Delete previous messages if they exist
        if chat_id in user_progress and user_progress[chat_id].get("last_question_message"):
            last_messages = user_progress[chat_id]["last_question_message"]
            try:
                # Delete previous question, result, and status messages
                await last_messages["question"].delete()
                await last_messages["result"].delete()
                await last_messages["status"].delete()
            except Exception as delete_error:
                logger.error(f"Error deleting messages: {delete_error}")
            
            # Clear the stored messages
            user_progress[chat_id]["last_question_message"] = None
        
        # Send new question
        await send_english_question(chat_id)
        
    except Exception as e:
        logger.error(f"Error in next_question: {e}")
        await callback_query.message.answer("Қателік орын алды. Қайтадан көріңіз.")

@dp.callback_query(lambda c: c.data == "my_progress")
async def show_progress(callback_query: CallbackQuery):
    """Show user's learning progress"""
    try:
        chat_id = callback_query.message.chat.id
        
        if chat_id in user_progress:
            correct = user_progress[chat_id].get("correct_answers", 0)
            total = user_progress[chat_id].get("questions_answered", 0)
            percentage = (correct / total * 100) if total > 0 else 0
            
            progress_text = (
                f"📊 Сіздің жетістіктеріңіз:\n\n"
                f"✅ Дұрыс жауаптар: {correct}\n"
                f"📝 Барлық жауаптар: {total}\n"
                f"📈 Пайыздық көрсеткіш: {percentage:.1f}%"
            )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Басты мәзір", callback_data="main_menu")]
            ])
            
            await callback_query.message.answer(progress_text, reply_markup=keyboard)
        else:
            await callback_query.answer(
                "Сіз әлі тест тапсырған жоқсыз.\n"
                "You haven't taken any tests yet."
            )
    except Exception as e:
        logger.error(f"Error in show_progress: {e}")
        await callback_query.message.answer("Қателік орын алды. Қайтадан көріңіз.")

async def send_scheduled_message(chat_id: int, message: str):
    """Send scheduled message to user or group"""
    try:
        # Get appropriate keyboard based on chat type
        keyboard = get_english_menu() if chat_id not in group_ids else None
        await bot.send_message(chat_id, message, reply_markup=keyboard)
        logger.info(f"Scheduled message sent to {chat_id}")
    except Exception as e:
        logger.error(f"Error sending scheduled message to {chat_id}: {e}")
        if chat_id in active_users:
            active_users.discard(chat_id)
        if chat_id in group_ids:
            group_ids.discard(chat_id)

async def morning_reminder(chat_id: int):
    """Send morning reminder"""
    message = random.choice(MORNING_MESSAGES)
    await send_scheduled_message(chat_id, message)

async def schedule_reminders(chat_id: int):
    """Schedule all reminders for a user or group"""
    try:
        logger.info(f"Scheduling reminders for chat {chat_id}")
        
        # Алдымен осы чат үшін бар тапсырмаларды өшіреміз
        for job in scheduler.get_jobs():
            if str(chat_id) in job.id:
                scheduler.remove_job(job.id)
        
        # Таңғы хабарлама
        scheduler.add_job(
            send_scheduled_message,
            'cron',
            hour=7,
            minute=0,
            args=[chat_id, random.choice(MORNING_MESSAGES)],
            id=f'morning_{chat_id}',
            replace_existing=True
        )
        
        # Түскі хабарлама
        scheduler.add_job(
            send_scheduled_message,
            'cron',
            hour=10,
            minute=0,
            args=[chat_id, NOON_MESSAGE],
            id=f'noon_{chat_id}',
            replace_existing=True
        )
        
        # Түстен кейінгі хабарлама
        scheduler.add_job(
            send_scheduled_message,
            'cron',
            hour=16,
            minute=0,
            args=[chat_id, AFTERNOON_MESSAGE],
            id=f'afternoon_{chat_id}',
            replace_existing=True
        )
        
        # Кешкі хабарлама
        scheduler.add_job(
            send_scheduled_message,
            'cron',
            hour=20,
            minute=0,
            args=[chat_id, EVENING_MESSAGE],
            id=f'evening_{chat_id}',
            replace_existing=True
        )
        
        # Салауат хабарламасы
        scheduler.add_job(
            send_scheduled_message,
            'cron',
            hour=22,
            minute=0,
            args=[chat_id, SALAUAT_MESSAGE],
            id=f'salauat_{chat_id}',
            replace_existing=True
        )
        
        logger.info(f"Successfully scheduled all reminders for chat {chat_id}")
        logger.info(f"Current jobs for chat {chat_id}: {[job.id for job in scheduler.get_jobs() if str(chat_id) in job.id]}")
        
    except Exception as e:
        logger.error(f"Error scheduling reminders for {chat_id}: {e}")

# Жаңа callback handler қосу
@dp.callback_query(lambda c: c.data == "leave_feedback")
async def handle_feedback(callback_query: CallbackQuery):
    """Handle feedback button press"""
    try:
        await callback_query.answer()
        await callback_query.message.reply(
            "💭 Топты жақсарту үшін пікіріңізді қалдырыңыз!\n"
            "Қандай тақырыптар қызықтырады? Қандай жаттығулар қосқымыз келеді?"
        )
    except Exception as e:
        logger.error(f"Error handling feedback: {e}")

# start_command функциясын жаңарту
@dp.message(CommandStart())
async def start_command(message: Message):
    """Handle /start command"""
    try:
        chat_id = message.chat.id
        
        if message.chat.type in ['group', 'supergroup']:
            group_ids.add(chat_id)
            # Создаем упрощенную клавиатуру для группы
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
                reply_markup=group_keyboard  # Добавляем клавиатуру для группы
            )
            # Топ үшін арнайы жоспарлау
            await schedule_group_activities(chat_id)
        else:
            # Жеке чат үшін бұрынғы код
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
@dp.message()
async def handle_messages(message: Message):
    """Handle all incoming messages"""
    try:
        text = message.text.lower() if message.text else ""
        if text in BASIC_RESPONSES:
            # Добавляем клавиатуру в зависимости от типа чата
            if message.chat.type == 'private':
                keyboard = get_english_menu()
            else:
                # Упрощенная клавиатура для групп
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📚 Ағылшын тілін үйрену", callback_data="learn_english")]
                ])
            await message.answer(BASIC_RESPONSES[text], reply_markup=keyboard)
            
        # Add user to active users if it's a private chat
        if message.chat.type == 'private':
            active_users.add(message.chat.id)
        # Add group to groups list if it's a group chat
        elif message.chat.type in ['group', 'supergroup']:
            group_ids.add(message.chat.id)
            
    except Exception as e:
        logger.error(f"Error in handle_messages: {e}")

async def main() -> None:
    try:
        # Scheduler-ді алдымен іске қосамыз
        scheduler.start()
        logger.info("Scheduler started successfully")
        
        # Командаларды орнату
        commands_list = [
            types.BotCommand(command="start", description="Бастау / Start the bot"),
            types.BotCommand(command="help", description="Көмек / Help information"),
            types.BotCommand(command="schedule", description="Кесте / Show schedule"),
        ]
        await bot.set_my_commands(commands_list)
        
        # Polling-ті бастау
        logger.info("Starting bot polling...")
        await dp.start_polling(bot, skip_updates=True)
        
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        raise
    finally:
        scheduler.shutdown()
        await bot.session.close()
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
        # Create appropriate keyboard based on chat type
        if message.chat.type == 'private':
            keyboard = get_english_menu()
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📚 Ағылшын тілін үйрену", callback_data="learn_english")]
            ])
            
        await message.answer(help_text, reply_markup=keyboard, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error in help_command: {e}")
        await message.answer("Қателік орын алды. Қайтадан көріңіз.")

@dp.message(Command('schedule'))
async def schedule_command(message: Message):
    """Handle /schedule command"""
    schedule_text = (
        "📅 *Күнделікті хабарламалар кестесі:*\n\n"
        "🌅 07:00 - Таңғы ескерту\n"
        "📚 10:00 - Кітап оқу уақыты\n"
        "🇬🇧 13:00 - Ағылшын тілі сабағы\n"
        "🇬🇧 16:00 - Ағылшын тілі сабағы\n"
        "🇬🇧 17:00 - Ағылшын тілі сабағы\n"
        "📝 20:00 - Күн қорытындысы\n"
        "🤲 22:00 - Салауат\n\n"
        "🔄 Барлық ескертулер *автоматты түрде* жіберіледі."
    )
    try:
        # Create appropriate keyboard based on chat type
        if message.chat.type == 'private':
            keyboard = get_english_menu()
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📚 Ағылшын тілін үйрену", callback_data="learn_english")]
            ])
            
        await message.answer(schedule_text, reply_markup=keyboard, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error in schedule_command: {e}")
        await message.answer("Қателік орын алды. Қайтадан көріңіз.")

# Ensure the bot is run only if this script is executed directly
if __name__ == "__main__":
    asyncio.run(main())
