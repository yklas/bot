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
import json 
from aiogram import types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton


# Configuration
TELEGRAM_TOKEN = "7819420348:AAG8yOE4qVLy9wOUegX__XV-xTnD7U9BzoQ"
TIMEZONE = pytz.timezone('Asia/Almaty')

# Logging setup with more detailed configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher with error handling
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Store active users and group chats with proper type hints
active_users: set[int] = set()
group_ids: set[int] = set()

# Update error handling decorator
def handle_exceptions(func):
    async def wrapper(*args, **kwargs):
        try:
            # Remove dispatcher from kwargs if it exists
            if 'dispatcher' in kwargs:
                del kwargs['dispatcher']
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            # Get chat_id from different possible argument types
            chat_id = None
            for arg in args:
                if isinstance(arg, Message):
                    chat_id = arg.chat.id
                elif isinstance(arg, CallbackQuery):
                    chat_id = arg.message.chat.id
                elif isinstance(arg, int):
                    chat_id = arg
            
            if chat_id:
                try:
                    await bot.send_message(
                        chat_id=chat_id,
                        text="Қателік орын алды. Қайтадан әрекеттеніп көріңіз. /start"
                    )
                except Exception as send_error:
                    logger.error(f"Error sending error message: {send_error}")
    return wrapper



# English learning content
ENGLISH_QUESTIONS: List[Dict] = [
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

# Improve user progress tracking with TypedDict
from typing import TypedDict

class UserProgress(TypedDict):
    asked_questions: List[str]
    current_question: Dict | None
    correct_answers: int
    questions_answered: int
    last_question_message: Dict | None

user_progress: Dict[int, UserProgress] = {}
# Add rate limiting
from collections import defaultdict
from datetime import datetime, timedelta

rate_limit: Dict[int, List[datetime]] = defaultdict(list)
RATE_LIMIT_MESSAGES = 5
RATE_LIMIT_PERIOD = 60  # seconds

def is_rate_limited(user_id: int) -> bool:
    now = datetime.now()
    # Clean old timestamps
    rate_limit[user_id] = [ts for ts in rate_limit[user_id] 
                          if now - ts < timedelta(seconds=RATE_LIMIT_PERIOD)]
    
    if len(rate_limit[user_id]) >= RATE_LIMIT_MESSAGES:
        return True
    
    rate_limit[user_id].append(now)
    return False


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
    {'hour': 10, 'minute': 0},
    {'hour': 13, 'minute': 0},
    {'hour': 18, 'minute': 0},
    {'hour': 21, 'minute': 0}
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
            hour=18, 
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
            hour=21,
            minute=50,
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

# start_command функциясын жаңарту
async def send_scheduled_message(chat_id: int, message: str):
    """Send scheduled message to user or group with appropriate keyboard"""
    try:
        # Determine chat type and set appropriate keyboard
        is_group = chat_id in group_ids
        keyboard = None
        
        if is_group:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📚 Ағылшын тілін үйрену", callback_data="learn_english")]
            ])
        else:
            keyboard = get_english_menu()
            
        await bot.send_message(chat_id, message, reply_markup=keyboard)
        logger.info(f"Scheduled message sent to {'group' if is_group else 'private'} chat {chat_id}")
    except Exception as e:
        logger.error(f"Error sending scheduled message to {chat_id}: {e}")
        # Remove from tracking if message fails
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
        is_group = chat_id in group_ids
        
        # Common scheduling for both private and group chats
        scheduler_jobs = [
            # Morning reminder - 7:00
            {
                'func': send_scheduled_message,
                'hour': 7,
                'minute': 0,
                'args': [chat_id, random.choice(MORNING_MESSAGES if not is_group else GROUP_MESSAGES['morning'])],
                'id': f'morning_{chat_id}'
            },
            # Noon message - 10:00
            {
                'func': send_scheduled_message,
                'hour': 10,
                'minute': 0,
                'args': [chat_id, NOON_MESSAGE if not is_group else random.choice(GROUP_MESSAGES['book'])],
                'id': f'noon_{chat_id}'
            },
            # Afternoon message - 16:00
            {
                'func': send_scheduled_message,
                'hour': 16,
                'minute': 0,
                'args': [chat_id, AFTERNOON_MESSAGE if not is_group else random.choice(GROUP_MESSAGES['english'])],
                'id': f'afternoon_{chat_id}'
            },
            # Evening message - 20:00
            {
                'func': send_scheduled_message,
                'hour': 20,
                'minute': 0,
                'args': [chat_id, EVENING_MESSAGE if not is_group else random.choice(GROUP_MESSAGES['activity'])],
                'id': f'evening_{chat_id}'
            },
            # Salauat message - 22:00
            {
                'func': send_scheduled_message,
                'hour': 21,
                'minute': 50,
                'args': [chat_id, SALAUAT_MESSAGE],
                'id': f'salauat_{chat_id}'
            }
        ]

        # Schedule all jobs
        for job in scheduler_jobs:
            scheduler.add_job(
                job['func'],
                'cron',
                hour=job['hour'],
                minute=job['minute'],
                args=job['args'],
                id=job['id'],
                replace_existing=True
            )

        # Schedule English lessons at specific times
        for schedule in english_schedule:
            job_id = f'english_{schedule["hour"]}_{schedule["minute"]}_{chat_id}'
            if is_group:
                scheduler.add_job(
                    send_group_english_activity,
                    'cron',
                    hour=schedule['hour'],
                    minute=schedule['minute'],
                    args=[chat_id],
                    id=job_id,
                    replace_existing=True
                )
            else:
                scheduler.add_job(
                    send_english_question,
                    'cron',
                    hour=schedule['hour'],
                    minute=schedule['minute'],
                    args=[chat_id],
                    id=job_id,
                    replace_existing=True
                )

        if not scheduler.running:
            scheduler.start()
        
        logger.info(f"Reminders scheduled for {'group' if is_group else 'private'} chat {chat_id}")
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

# Add these functions
def save_group_ids():
    with open('group_ids.json', 'w') as f:
        json.dump(list(group_ids), f)

def load_group_ids():
    try:
        with open('group_ids.json', 'r') as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()

# Update start command to use the same scheduling system
@dp.message(CommandStart())
async def start_command(message: Message):
    """Handle /start command"""
    try:
        chat_id = message.chat.id
        
        if message.chat.type in ['group', 'supergroup']:
            group_ids.add(chat_id)
            save_group_ids()
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
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
                reply_markup=keyboard
            )
        else:
            active_users.add(chat_id)
            await message.reply(
                "Ассалаумағалейкум! 👋\n"
                "Мен сіздің көмекшіңізбін. Сұрақтарыңызға жауап беріп, "
                "күнделікті ескертулер жасаймын!\n\n"
                "Төмендегі батырмаларды басып, ағылшын тілін үйрене аласыз!",
                reply_markup=get_english_menu()
            )
        
        # Schedule reminders for both private and group chats
        await schedule_reminders(chat_id)
        logger.info(f"Bot started in {'group' if chat_id in group_ids else 'private'} chat: {chat_id}")
    except Exception as e:
        logger.error(f"Error in start_command: {e}")
        await message.reply("Қателік орын алды. Қайтадан әрекеттеніп көріңіз.")
        
# Update message handler
@dp.message()
async def handle_messages(message: Message):
    """Handle all incoming messages with rate limiting"""
    try:
        # Check rate limiting
        if is_rate_limited(message.from_user.id):
            await message.answer("Тым жиі хабарлама жібердіңіз. Біраз күте тұрыңыз.")
            return

        # Check if message has text
        if not message.text:
            return

        # Convert message to lowercase and strip whitespace
        text = message.text.lower().strip()
        
        # Log incoming message for debugging
        logger.info(f"Received message: '{text}' in chat {message.chat.id}")

        # Check if the message is in BASIC_RESPONSES
        if text in BASIC_RESPONSES:
            try:
                # Create appropriate keyboard based on chat type
                keyboard = (
                    get_english_menu() 
                    if message.chat.type == 'private'
                    else InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(
                            text="📚 Ағылшын тілін үйрену",
                            callback_data="learn_english"
                        )]
                    ])
                )
                
                # Send response with keyboard
                await message.answer(
                    BASIC_RESPONSES[text],
                    reply_markup=keyboard
                )
                
                # Log successful response
                logger.info(f"Successfully sent response for '{text}' in chat {message.chat.id}")
                
                # Update tracking
                if message.chat.type == 'private':
                    active_users.add(message.chat.id)
                elif message.chat.type in ['group', 'supergroup']:
                    group_ids.add(message.chat.id)
                    save_group_ids()
                
            except Exception as e:
                logger.error(f"Error sending response for '{text}': {e}", exc_info=True)
                await message.answer("Қателік орын алды. Қайтадан әрекеттеніп көріңіз.")

    except Exception as e:
        logger.error(f"Error in handle_messages: {e}", exc_info=True)
        await message.answer("Қателік орын алды. Қайтадан әрекеттеніп көріңіз.")


# Add proper cleanup on shutdown
async def shutdown(dispatcher: Dispatcher):
    """Cleanup resources on shutdown"""
    try:
        if scheduler.running:
            scheduler.shutdown(wait=True)
        await bot.session.close()
        logger.info("Bot shut down successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Stop командасын қосу
@dp.message(Command("stop"))
@handle_exceptions
async def stop_command(message: Message):
    """Handle /stop command to unsubscribe user from bot"""
    try:
        chat_id = message.chat.id
        
        # Тек жеке чатта жұмыс істеу керек
        if message.chat.type != 'private':
            await message.answer("❌ Бұл команда тек жеке чатта жұмыс істейді.")
            return

        # Пайдаланушыдан растау сұрау
        confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Иә, тоқтату", callback_data="confirm_stop"),
                InlineKeyboardButton(text="❌ Жоқ, бас тарту", callback_data="cancel_stop")
            ]
        ])
        
        await message.answer(
            "❗️ Сіз ботты тоқтатқыңыз келе ме?\n\n"
            "Бұл әрекет:\n"
            "- Күнделікті хабарламаларды тоқтатады\n"
            "- Сіздің оқу прогресіңіз сақталады\n"
            "- Кез-келген уақытта /start командасымен қайта бастай аласыз",
            reply_markup=confirm_keyboard
        )
        
    except Exception as e:
        logger.error(f"Error in stop_command: {e}", exc_info=True)
        await message.answer("Қателік орын алды. Қайтадан әрекеттеніп көріңіз.")

# Тоқтатуды растау/бас тарту үшін callback handler-лер
@dp.callback_query(lambda c: c.data == "confirm_stop")
async def confirm_stop(callback_query: CallbackQuery):
    """Handle stop confirmation"""
    try:
        chat_id = callback_query.message.chat.id
        
        # Remove from active users
        if chat_id in active_users:
            active_users.discard(chat_id)
        
        # Remove all scheduled jobs for this user
        jobs = scheduler.get_jobs()
        for job in jobs:
            if str(chat_id) in job.id:
                scheduler.remove_job(job.id)
        
        # Remove keyboard and update message
        await callback_query.message.edit_text(
            "✅ Бот сәтті тоқтатылды!\n\n"
            "Қайта бастау үшін /start командасын жіберіңіз.\n"
            "Сау болыңыз! 👋"
        )
        
        logger.info(f"User {chat_id} stopped the bot")
        
    except Exception as e:
        logger.error(f"Error in confirm_stop: {e}", exc_info=True)
        await callback_query.message.edit_text(
            "Қателік орын алды. Қайтадан әрекеттеніп көріңіз."
        )

@dp.callback_query(lambda c: c.data == "cancel_stop")
async def cancel_stop(callback_query: CallbackQuery):
    """Handle stop cancellation"""
    try:
        # Remove confirmation keyboard and update message
        await callback_query.message.edit_text(
            "✅ Бас тартылды. Бот жұмысын жалғастыра береді!"
        )
        
    except Exception as e:
        logger.error(f"Error in cancel_stop: {e}", exc_info=True)
        await callback_query.message.edit_text(
            "Қателік орын алды. Қайтадан әрекеттеніп көріңіз."
        )


# register_commands функциясын жаңарту
async def register_commands(bot: Bot):
    """Register bot commands"""
    commands = [
        types.BotCommand(command="start", description="Ботты бастау"),
        types.BotCommand(command="help", description="Көмек алу"),
        types.BotCommand(command="schedule", description="Кесте көру"),
        types.BotCommand(command="stop", description="Ботты тоқтату")  # Жаңа команда
    ]
    await bot.set_my_commands(commands)
    logger.info("Bot commands registered successfully")

# Update main function to include command registration
async def main() -> None:
    """Main function to start the bot"""
    try:
        # Load saved group IDs
        global group_ids
        group_ids = load_group_ids()
        
        # Register commands
        await register_commands(bot)
        
        # Start scheduler if not running
        if not scheduler.running:
            scheduler.start()
            
        # Schedule reminders for existing groups
        for group_id in group_ids:
            await schedule_reminders(group_id)
            
        # Start polling
        logger.info("Bot started successfully")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Critical error in main function: {e}", exc_info=True)
    finally:
        await shutdown(dp)# Update main function with proper shutdown handling


@dp.message(Command("check_schedules"))
async def check_schedules(message: Message):
    try:
        chat_id = message.chat.id
        jobs = scheduler.get_jobs()
        schedules = [f"Job: {job.id}, Next run: {job.next_run_time}" for job in jobs if str(chat_id) in job.id]
        
        if schedules:
            await message.reply("\n".join(schedules))
        else:
            await message.reply("No scheduled messages found for this chat")
    except Exception as e:
        logger.error(f"Error checking schedules: {e}")


# Remove duplicate help_command handlers and add schedule command
# schedule командасын түзету
@dp.message(Command("schedule"))
@handle_exceptions
async def schedule_command(message: Message):
    """Handle /schedule command"""
    try:
        schedule_text = (
            "📅 *Күнделікті хабарламалар кестесі*\n\n"
            "🌅 07:00 - Таңғы сәлемдесу\n"
            "📚 10:00 - Кітап оқу уақыты\n"
            "🇬🇧 13:00 - Ағылшын тілі сабағы\n"
            "📝 16:00 - Күндізгі белсенділік\n"
            "🌟 18:00 - Ағылшын тілі сабағы\n"
            "📊 20:00 - Күн қорытындысы\n"
            "🌙 21:00 - Ағылшын тілі сабағы\n"
            "🤲 21:50 - Салауат\n\n"
            "⚡️ Хабарламаларды өз уақытында аласыз!"
        )
        
        keyboard = None
        if message.chat.type == 'private':
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📚 Ағылшын тілін үйрену", callback_data="learn_english")],
                [InlineKeyboardButton(text="📊 Менің жетістіктерім", callback_data="my_progress")]
            ])
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📚 Ағылшын тілін үйрену", callback_data="learn_english")]
            ])
        
        await message.answer(
            text=schedule_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        logger.info(f"Schedule command sent successfully in chat {message.chat.id}")
        
    except Exception as e:
        logger.error(f"Error in schedule_command: {e}", exc_info=True)
        await message.answer("Қателік орын алды. Қайтадан /schedule командасын жіберіңіз.")



# help командасын түзету
@dp.message(Command("help"))
@handle_exceptions
async def help_command(message: Message):
    """Handle /help command"""
    try:
        help_text = (
            "🤖 *Бот көмекшісі*\n\n"
            "Негізгі командалар:\n"
            "🔹 /start - Ботты қайта іске қосу\n"
            "🔹 /help - Көмек алу\n"
            "🔹 /schedule - Хабарламалар кестесі\n\n"
            "📱 Қосымша мүмкіндіктер:\n"
            "📚 Ағылшын тілін үйрену\n"
            "🕐 Күнделікті ескертулер\n"
            "📝 Жетістіктерді бақылау\n\n"
            "❓ Сұрақтарыңыз болса, еркін жазыңыз!"
        )
        
        # Create keyboard based on chat type
        keyboard = None
        if message.chat.type == 'private':
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📚 Ағылшын тілін үйрену", callback_data="learn_english")],
                [InlineKeyboardButton(text="📊 Менің жетістіктерім", callback_data="my_progress")]
            ])
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📚 Ағылшын тілін үйрену", callback_data="learn_english")]
            ])
        
        await message.answer(
            text=help_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        logger.info(f"Help command sent successfully in chat {message.chat.id}")
        
    except Exception as e:
        logger.error(f"Error in help_command: {e}", exc_info=True)
        await message.answer("Қателік орын алды. Қайтадан /help командасын жіберіңіз.")

# Ensure the bot is run only if this script is executed directly
if __name__ == "__main__":
    asyncio.run(main())
