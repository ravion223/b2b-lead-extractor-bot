import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.filters import Command, CommandStart
import logging
import aiosqlite
from dotenv import load_dotenv
from pathlib import Path

from export import export_to_excel

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Fake database (Freemium Gatekeeping)
premium_users = set()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Download Lead Report", callback_data="generate_report")],
        [InlineKeyboardButton(text="🏆 Top 3 Rated Roofers", callback_data="stat_top_3")],
        [InlineKeyboardButton(text="🌐 Website Statistics", callback_data="stat_websites")]
    ])

def get_premium_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔓 Upgrade to Premium", callback_data="upgrade_premium")]
    ])

@dp.message(CommandStart())
async def cmd_start(message: Message):
    welcome_text = (
        "👋 Hi! I'm automated B2B-parser.\n\n"
        "I can gather up-to-date Roofing Contractors contacts in Austin, TX,"
        "filter out duplicates and send you a clean Excel file for the CRM."
    )
    await message.answer(welcome_text, reply_markup=get_main_keyboard())

# --- SECRET BACKDOOR COMMAND ---
@dp.message(Command("premium"))
async def cmd_secret_premium(message: Message):
    user_id = message.from_user.id
    premium_users.add(user_id)
    await message.answer(
        "✨ [ADMIN] Premium unlocked! You now have full access to all leads.",
        reply_markup=get_main_keyboard()
    )

# --- INLINE ANALYTICS HANDLERS ---
@dp.callback_query(F.data == "stat_top_3")
async def handle_top_3(callback: CallbackQuery):
    async with aiosqlite.connect("scraper.db") as db:
        cursor = await db.execute("SELECT business_name, rating FROM leads WHERE rating IS NOT NULL ORDER BY rating DESC LIMIT 3")
        rows = await cursor.fetchall()

        text = "🏆 **Top 3 Rated Roofing Contractors:**\n\n"
        for idx, (name, rating) in enumerate(rows, 1):
            text += f"{idx}. {name} - ⭐ {rating}\n"

        await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "stat_websites")
async def handle_websites(callback: CallbackQuery):
    async with aiosqlite.connect("scraper.db") as db:
        cursor = await db.execute("SELECT COUNT(*) FROM leads WHERE website IS NOT NULL")
        with_web = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM leads")
        total = (await cursor.fetchone())[0]

        text = (
            "🌐 **Digital Presence Stats:**\n\n"
            f"• Total Leads: {total}\n"
            f"• Have a Website: {with_web}\n"
            f"• Conversion potential: {round((with_web/total)*100, 1)}%"
        )
        
        await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "generate_report")
async def handle_generate_report(callback: CallbackQuery):
    user_id = callback.from_user.id
    is_premium = user_id in premium_users

    loading_msg = await callback.message.answer("⏳ Initializing connection to SQLite database...")
    await callback.message.delete()

    statuses = [
        "🔍 Reading data (Roofing Contractors, Austin, TX)...",
        "⚙️ Executing Data Deduplication...",
        "📊 Pandas DataFrame generation and formatting...",
        "✅ Export in .xlsx (openpyxl engine) finished!"
    ]

    for status in statuses[1:]:
        await asyncio.sleep(1.2)
        await loading_msg.edit_text(status)

    await asyncio.sleep(0.8)

    if is_premium:
        export_to_excel(limit=None)
        caption_text = "🎯 Done! Here is your report with contacts."
    else:
        export_to_excel(limit=5)
        caption_text = "⚠️ This is a free Demo Report (limited to 5 rows).\n\nUpgrade to Premium to export the entire database."

    file_path = "leads_report.xlsx"

    if os.path.exists(file_path):
        document = FSInputFile(file_path)
        markup = get_main_keyboard() if is_premium else get_premium_keyboard()
        await callback.message.answer_document(
            document, 
            caption=caption_text,
            reply_markup=markup
        )
        
        await loading_msg.delete()
    else:
        await callback.message.answer("⚠️ An error occured when generating file.")

    await callback.answer()

@dp.callback_query(F.data == "upgrade_premium")
async def handle_upgrade_prompt(callback: CallbackQuery):
    await callback.message.answer(
        "🔒 **Premium Access Required**\n\n"
        "To unlock unlimited exports, please purchase a premium.\n"
        "*(Hint for testers: type /premium to bypass this paywall)*",
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.message(F.text)
async def handle_any_text(message: Message):
    if message.text == "/premium":
        return
    
    await message.answer(
        "⚠️ This is a portfolio demo environment.\n"
        "Text input is disabled. Please use the button below to test the data engineering pipeline.",
        reply_markup=get_main_keyboard()
    )

async def main():
    logging.info("🤖 Bot successfully launched and ready to work!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())