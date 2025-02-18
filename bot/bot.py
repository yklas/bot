import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from datetime import datetime, timedelta
import pytz
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import random
from typing import List, Dict, Optional
import aiohttp
import json
import os
from dotenv import load_dotenv
import sqlite3
import re
from dataclasses import dataclass
from openai import AsyncOpenAI

# Load environment variables
load_dotenv()

# Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
UNSPLASH_API_KEY = os.getenv("UNSPLASH_API_KEY")
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

# Initialize OpenAI client
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Database setup
def setup_database():
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    
    # Create tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            joined_date TEXT,
            is_active BOOLEAN
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS groups (
            group_id INTEGER PRIMARY KEY,
            group_name TEXT,
            joined_date TEXT,
            is_active BOOLEAN
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            question_id TEXT PRIMARY KEY,
            date TEXT,
            content TEXT,
            image_url TEXT,
            options TEXT,
            correct_answer TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_progress (
            user_id INTEGER,
            question_id TEXT,
            answer TEXT,
            is_correct BOOLEAN,
            answer_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (question_id) REFERENCES questions(question_id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Data models
@dataclass
class Question:
    id: str
    date: str
    content: str
    image_url: str
    options: List[str]
    correct_answer: str

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('bot_database.db')
        self.c = self.conn.cursor()
    
    def close(self):
        self.conn.close()
    
    def add_user(self, user_id: int, username: str, first_name: str, last_name: str):
        self.c.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, username, first_name, last_name, joined_date, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name, 
              datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S'), True))
        self.conn.commit()
    
    def add_group(self, group_id: int, group_name: str):
        self.c.execute('''
            INSERT OR REPLACE INTO groups 
            (group_id, group_name, joined_date, is_active)
            VALUES (?, ?, ?, ?)
        ''', (group_id, group_name, 
              datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S'), True))
        self.conn.commit()
    
    def add_question(self, question: Question):
        self.c.execute('''
            INSERT OR REPLACE INTO questions 
            (question_id, date, content, image_url, options, correct_answer)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (question.id, question.date, question.content, question.image_url,
              json.dumps(question.options), question.correct_answer))
        self.conn.commit()
    
    def get_daily_questions(self, date: str) -> List[Question]:
        self.c.execute('''
            SELECT * FROM questions WHERE date = ?
        ''', (date,))
        rows = self.c.fetchall()
        return [Question(
            id=row[0],
            date=row[1],
            content=row[2],
            image_url=row[3],
            options=json.loads(row[4]),
            correct_answer=row[5]
        ) for row in rows]

async def generate_questions() -> List[Question]:
    """Generate new questions using GPT-4"""
    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": """
                Generate 4 English learning questions. For each question, provide:
                1. A clear image description for visual reference
                2. A question in Kazakh about everyday objects or situations
                3. Four multiple choice options in English
                4. The correct answer
                
                Format each question as a JSON object with fields:
                {
                    "image_description": "...",
                    "question": "...",
                    "options": ["...", "...", "...", "..."],
                    "correct_answer": "..."
                }
                
                Return an array of 4 such objects.
                """},
                {"role": "user", "content": "Generate 4 unique English learning questions."}
            ]
        )
        
        # Parse the response
        content = response.choices[0].message.content
        questions_data = json.loads(content)
        
        questions = []
        current_date = datetime.now(TIMEZONE).strftime('%Y-%m-%d')
        
        for idx, q_data in enumerate(questions_data, 1):
            # Get image URL for the question
            image_url = await search_image(q_data['image_description'])
            
            question = Question(
                id=f"{current_date}_{idx}",
                date=current_date,
                content=q_data['question'],
                image_url=image_url,
                options=q_data['options'],
                correct_answer=q_data['correct_answer']
            )
            questions.append(question)
        
        return questions
        
    except Exception as e:
        logger.error(f"Error generating questions: {e}")
        return []

async def search_image(query: str) -> str:
    """Search for an image using Unsplash API"""
    try:
        async with aiohttp.ClientSession() as session:
            params = {
                'query': query,
                'client_id': UNSPLASH_API_KEY,
                'per_page': 1
            }
            async with session.get('https://api.unsplash.com/search/photos', params=params) as response:
                data = await response.json()
                if data['results']:
                    return data['results'][0]['urls']['regular']
        
        return "/api/placeholder/400/320"
    except Exception as e:
        logger.error(f"Error searching image: {e}")
        return "/api/placeholder/400/320"

async def update_daily_questions():
    """Generate and store new daily questions"""
    try:
        questions = await generate_questions()
        db = Database()
        
        for question in questions:
            db.add_question(question)
        
        # Send questions to all active groups
        db.c.execute('SELECT group_id FROM groups WHERE is_active = TRUE')
        groups = db.c.fetchall()
        
        for group_id in groups:
            await send_daily_questions(group_id[0])
        
        db.close()
    except Exception as e:
        logger.error(f"Error updating daily questions: {e}")

async def send_daily_questions(chat_id: int):
    """Send daily questions to a chat"""
    try:
        db = Database()
        current_date = datetime.now(TIMEZONE).strftime('%Y-%m-%d')
        questions = db.get_daily_questions(current_date)
        
        intro_message = (
            "🇬🇧 Қайырлы күн! Бүгінгі ағылшын тілі сұрақтары:\n\n"
            "💡 Әр сұраққа жауап беріп, біліміңізді тексеріңіз!"
        )
        await bot.send_message(chat_id, intro_message)
        await asyncio.sleep(1)
        
        for question in questions:
            keyboard = []
            for option in question.options:
                callback_data = f"answer_{question.id}_{option}"
                keyboard.append([InlineKeyboardButton(text=option, callback_data=callback_data)])
            
            markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
            
            await bot.send_photo(
                chat_id=chat_id,
                photo=question.image_url,
                caption=f"❓ {question.content}",
                reply_markup=markup
            )
            await asyncio.sleep(1)
        
        db.close()
    except Exception as e:
        logger.error(f"Error sending daily questions: {e}")

@dp.message(CommandStart())
async def start_command(message: Message):
    """Handle /start command"""
    try:
        db = Database()
        chat_id = message.chat.id
        
        if message.chat.type in ['group', 'supergroup']:
            db.add_group(chat_id, message.chat.title)
            await message.reply(
                "👋 Сәлеметсіздер!\n\n"
                "Мен сіздердің ағылшын тілін үйренуге көмектесетін боттарыңызбын.\n\n"
                "🎯 Мүмкіндіктерім:\n"
                "- Күн сайын жаңа сұрақтар\n"
                "- Суреттермен түсіндіру\n"
                "- Прогресті бақылау\n"
                "- Автоматты ескертулер\n\n"
                "Сұрақтарға жауап беріп, білім деңгейіңізді көтеріңіз! 📚"
            )
        else:
            db.add_user(
                chat_id,
                message.from_user.username,
                message.from_user.first_name,
                message.from_user.last_name
            )
            await message.reply(
                "👋 Сәлеметсіз!\n\n"
                "Мен сізге ағылшын тілін үйренуге көмектесемін.\n\n"
                "🎯 Мүмкіндіктерім:\n"
                "- Күн сайын жаңа сұрақтар\n"
                "- Жеке прогресті бақылау\n"
                "- Деңгейге сай тапсырмалар\n\n"
                "Бастау үшін /learn командасын жіберіңіз! 📚"
            )
        
        db.close()
        logger.info(f"New chat started: {chat_id}")
    except Exception as e:
        logger.error(f"Error in start_command: {e}")
        await message.reply("Қателік орын алды. Қайтадан көріңіз.")

@dp.message(Command("learn"))
async def learn_command(message: Message):
    """Handle /learn command"""
    try:
        await send_daily_questions(message.chat.id)
    except Exception as e:
        logger.error(f"Error in learn_command: {e}")
        await message.reply("Қателік орын алды. Қайтадан көріңіз.")

@dp.callback_query(lambda c: c.data.startswith("answer_"))
async def process_answer(callback_query: CallbackQuery):
    """Handle answer selection"""
    try:
        db = Database()
        _, question_id, answer = callback_query.data.split("_")
        
        # Get question
        db.c.execute('SELECT * FROM questions WHERE question_id = ?', (question_id,))
        question_data = db.c.fetchone()
        
        if question_data:
            question = Question(
                id=question_data[0],
                date=question_data[1],
                content=question_data[2],
                image_url=question_data[3],
                options=json.loads(question_data[4]),
                correct_answer=question_data[5]
            )
            
            is_correct = answer == question.correct_answer
            
            # Save user's answer
            db.c.execute('''
                INSERT INTO user_progress 
                (user_id, question_id, answer, is_correct, answer_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                callback_query.from_user.id,
                question_id,
                answer,
                is_correct,
                datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')
            ))
            db.conn.commit()
            
            # Send response
            if is_correct:
                await callback_query.answer("🎉 Дұрыс! / Correct!")
                await callback_query.message.reply("✅ Жарайсыз! Дұрыс жауап!")
            else:
                await callback_query.answer("❌ Қате / Incorrect")
                await callback_query.message.reply(
                    f"❌ Өкінішке орай, қате жауап.\n"
                    f"Дұрыс жауап: {question.correct_answer}"
                )
        
        db.close()
    except Exception as e:
        logger.error(f"Error processing answer: {e}")
        await callback_query.answer("Қателік орын алды. Қайтадан көріңіз.")

# Schedule tasks
scheduler = AsyncIOScheduler(timezone=TIMEZONE)
scheduler.add_job(
    update_daily_questions,
    'cron',
    hour=9,  # Send questions at 9 AM
    minute=0,
    timezone=TIMEZONE
)

async def main():
    """Main function to start the bot"""
    try:
        # Setup database
        setup_database()
        
        # Set bot commands
        await bot.set_my_commands([
            types.BotCommand(command="start", description="Ботты бастау"),
            types.BotCommand(command="learn", description="Жаңа сұрақтар алу"),
            types.BotCommand(command="stats", description="Статистика көру")
        ])
        
        # Start scheduler
        scheduler.start()
        
        # Start polling
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error in main function: {e}")
    finally:
        scheduler.shutdown()
        await bot.session

@dp.message(Command("stats"))
async def stats_command(message: Message):
    """Handle /stats command - show user statistics"""
    try:
        db = Database()
        user_id = message.from_user.id
        
        # Get user's progress
        db.c.execute('''
            SELECT 
                COUNT(*) as total_answers,
                SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct_answers,
                COUNT(DISTINCT date(answer_date)) as active_days
            FROM user_progress
            WHERE user_id = ?
        ''', (user_id,))
        
        stats = db.c.fetchone()
        
        if stats and stats[0] > 0:
            total_answers, correct_answers, active_days = stats
            accuracy = (correct_answers / total_answers) * 100
            
            # Get streak information
            db.c.execute('''
                SELECT date(answer_date) as answer_date
                FROM user_progress
                WHERE user_id = ?
                GROUP BY date(answer_date)
                ORDER BY answer_date DESC
            ''', (user_id,))
            
            dates = [row[0] for row in db.c.fetchall()]
            current_streak = 0
            
            if dates:
                current_date = datetime.now(TIMEZONE).date()
                last_date = datetime.strptime(dates[0], '%Y-%m-%d').date()
                
                if (current_date - last_date).days <= 1:
                    current_streak = 1
                    for i in range(len(dates) - 1):
                        date1 = datetime.strptime(dates[i], '%Y-%m-%d').date()
                        date2 = datetime.strptime(dates[i + 1], '%Y-%m-%d').date()
                        if (date1 - date2).days == 1:
                            current_streak += 1
                        else:
                            break
            
            stats_message = (
                "📊 Сіздің статистикаңыз:\n\n"
                f"✅ Жалпы жауаптар: {total_answers}\n"
                f"🎯 Дұрыс жауаптар: {correct_answers}\n"
                f"📈 Дәлдік: {accuracy:.1f}%\n"
                f"📅 Белсенді күндер: {active_days}\n"
                f"🔥 Ағымдағы streak: {current_streak} күн\n\n"
                "Жақсы жұмыс! Солай жалғастырыңыз! 💪"
            )
        else:
            stats_message = (
                "📊 Статистика әлі жоқ.\n\n"
                "Сұрақтарға жауап беру үшін /learn командасын қолданыңыз!"
            )
        
        await message.reply(stats_message)
        db.close()
        
    except Exception as e:
        logger.error(f"Error in stats_command: {e}")
        await message.reply("Қателік орын алды. Қайтадан көріңіз.")

@dp.message(Command("help"))
async def help_command(message: Message):
    """Handle /help command"""
    help_text = (
        "🤖 Бот командалары:\n\n"
        "/start - Ботты бастау\n"
        "/learn - Жаңа сұрақтар алу\n"
        "/stats - Жеке статистиканы көру\n"
        "/help - Көмек алу\n\n"
        "💡 Қосымша ақпарат:\n"
        "- Күн сайын жаңа сұрақтар таңғы 9:00-де жіберіледі\n"
        "- Әр сұраққа бір рет қана жауап бере аласыз\n"
        "- Статистика автоматты түрде жаңартылып отырады\n\n"
        "❓ Сұрақтар болса, админге хабарласыңыз"
    )
    await message.reply(help_text)

@dp.message(Command("admin"))
async def admin_command(message: Message):
    """Handle /admin command - admin only features"""
    try:
        # Check if user is admin
        chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        if chat_member.status not in ['creator', 'administrator']:
            await message.reply("⛔️ Бұл команда тек әкімшілерге қол жетімді.")
            return
        
        db = Database()
        
        # Get usage statistics
        db.c.execute('''
            SELECT 
                COUNT(DISTINCT user_id) as total_users,
                COUNT(DISTINCT group_id) as total_groups,
                COUNT(*) as total_answers,
                SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct_answers
            FROM user_progress
        ''')
        
        stats = db.c.fetchone()
        total_users, total_groups, total_answers, correct_answers = stats
        
        if total_answers > 0:
            accuracy = (correct_answers / total_answers) * 100
        else:
            accuracy = 0
        
        # Get active users for last 7 days
        week_ago = (datetime.now(TIMEZONE) - timedelta(days=7)).strftime('%Y-%m-%d')
        db.c.execute('''
            SELECT COUNT(DISTINCT user_id) 
            FROM user_progress 
            WHERE date(answer_date) >= ?
        ''', (week_ago,))
        
        active_users = db.c.fetchone()[0]
        
        admin_message = (
            "👨‍💼 Әкімші панелі\n\n"
            "📊 Жалпы статистика:\n"
            f"👥 Барлық қолданушылар: {total_users}\n"
            f"👥 Белсенді қолданушылар (7 күн): {active_users}\n"
            f"💭 Топтар саны: {total_groups}\n"
            f"✅ Жауаптар саны: {total_answers}\n"
            f"📈 Орташа дәлдік: {accuracy:.1f}%\n\n"
            "💡 Әкімші командалары:\n"
            "/force_update - Жаңа сұрақтарды қазір жіберу\n"
            "/broadcast - Барлық қолданушыларға хабарлама жіберу"
        )
        
        await message.reply(admin_message)
        db.close()
        
    except Exception as e:
        logger.error(f"Error in admin_command: {e}")
        await message.reply("Қателік орын алды. Қайтадан көріңіз.")

@dp.message(Command("force_update"))
async def force_update_command(message: Message):
    """Handle /force_update command - admin only"""
    try:
        # Check if user is admin
        chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        if chat_member.status not in ['creator', 'administrator']:
            await message.reply("⛔️ Бұл команда тек әкімшілерге қол жетімді.")
            return
        
        await message.reply("🔄 Жаңа сұрақтар жасалуда...")
        await update_daily_questions()
        await message.reply("✅ Жаңа сұрақтар жіберілді!")
        
    except Exception as e:
        logger.error(f"Error in force_update_command: {e}")
        await message.reply("Қателік орын алды. Қайтадан көріңіз.")

@dp.message(Command("broadcast"))
async def broadcast_command(message: Message):
    """Handle /broadcast command - admin only"""
    try:
        # Check if user is admin
        chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        if chat_member.status not in ['creator', 'administrator']:
            await message.reply("⛔️ Бұл команда тек әкімшілерге қол жетімді.")
            return
        
        # Get broadcast message
        broadcast_text = message.text.replace("/broadcast", "").strip()
        if not broadcast_text:
            await message.reply(
                "Хабарлама мәтінін көрсетіңіз.\n"
                "Мысалы: /broadcast Сәлеметсіздер! Жаңа функция қосылды."
            )
            return
        
        db = Database()
        
        # Get all active users and groups
        db.c.execute('SELECT user_id FROM users WHERE is_active = TRUE')
        users = db.c.fetchall()
        
        db.c.execute('SELECT group_id FROM groups WHERE is_active = TRUE')
        groups = db.c.fetchall()
        
        # Send broadcast
        success_count = 0
        fail_count = 0
        
        for chat_id in [*users, *groups]:
            try:
                await bot.send_message(chat_id[0], broadcast_text)
                success_count += 1
                await asyncio.sleep(0.1)  # Avoid hitting rate limits
            except Exception:
                fail_count += 1
        
        await message.reply(
            f"📨 Broadcast нәтижесі:\n"
            f"✅ Сәтті жіберілді: {success_count}\n"
            f"❌ Қате: {fail_count}"
        )
        
        db.close()
        
    except Exception as e:
        logger.error(f"Error in broadcast_command: {e}")
        await message.reply("Қателік орын алды. Қайтадан көріңіз.")

@dp.message()
async def handle_other_messages(message: Message):
    """Handle all other messages"""
    if message.chat.type in ['group', 'supergroup']:
        # Only respond to messages specifically mentioning the bot in groups
        if message.mentioned:
            await message.reply(
                "Көмек керек пе? /help командасын қолданыңыз!\n"
                "Need help? Use the /help command!"
            )
    else:
        # For private chats, provide a helpful response
        await message.reply(
            "Қолжетімді командалар:\n"
            "/start - Ботты бастау\n"
            "/learn - Жаңа сұрақтар алу\n"
            "/stats - Статистика көру\n"
            "/help - Көмек алу"
        )

async def send_reminder():
    """Send daily reminder to inactive users"""
    try:
        db = Database()
        current_date = datetime.now(TIMEZONE).strftime('%Y-%m-%d')
        
        # Find users who haven't answered today's questions
        db.c.execute('''
            SELECT DISTINCT u.user_id
            FROM users u
            LEFT JOIN user_progress up ON 
                u.user_id = up.user_id AND 
                date(up.answer_date) = ?
            WHERE u.is_active = TRUE AND up.user_id IS NULL
        ''', (current_date,))
        
        inactive_users = db.c.fetchall()
        
        reminder_message = (
            "🔔 Сәлеметсіз!\n\n"
            "Бүгін сіз әлі сұрақтарға жауап берген жоқсыз.\n"
            "Білім жолында тоқтамаңыз! 💪\n\n"
            "Жаңа сұрақтар алу үшін /learn командасын жіберіңіз."
        )
        
        for user_id in inactive_users:
            try:
                await bot.send_message(user_id[0], reminder_message)
                await asyncio.sleep(0.1)  # Avoid hitting rate limits
            except Exception as e:
                logger.error(f"Error sending reminder to user {user_id[0]}: {e}")
        
        db.close()
        
    except Exception as e:
        logger.error(f"Error in send_reminder: {e}")

# Add reminder schedule
scheduler.add_job(
    send_reminder,
    'cron',
    hour=20,  # Send reminder at 8 PM
    minute=0,
    timezone=TIMEZONE
)

async def cleanup_inactive():
    """Clean up inactive users and groups"""
    try:
        db = Database()
        month_ago = (datetime.now(TIMEZONE) - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Mark users as inactive if no activity for 30 days
        db.c.execute('''
            UPDATE users
            SET is_active = FALSE
            WHERE user_id IN (
                SELECT DISTINCT u.user_id
                FROM users u
                LEFT JOIN user_progress up ON 
                    u.user_id = up.user_id AND 
                    date(up.answer_date) >= ?
                WHERE u.is_active = TRUE AND up.user_id IS NULL
            )
        ''', (month_ago,))
        
        # Mark groups as inactive if bot was removed
        for group in db.c.execute('SELECT group_id FROM groups WHERE is_active = TRUE'):
            try:
                await bot.get_chat(group[0])
            except Exception:
                db.c.execute('UPDATE groups SET is_active = FALSE WHERE group_id = ?', (group[0],))
        
        db.conn.commit()
        db.close()
        
    except Exception as e:
        logger.error(f"Error in cleanup_inactive: {e}")

# Add cleanup schedule
scheduler.add_job(
    cleanup_inactive,
    'cron',
    hour=3,  # Run cleanup at 3 AM
    minute=0,
    timezone=TIMEZONE
)

if __name__ == '__main__':
    # Run the bot
    asyncio.run(main())
