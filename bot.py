import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import aiosqlite

from config import BOT_TOKEN, DB_PATH, EXPORT_FILE, FREE_TIER_LIMIT
from database import init_db
from export import export_to_excel
from scraper import scrape_directory

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# In-memory set for freemium gatekeeping (resets on restart)
premium_users: set[int] = set()

class ScraperState(StatesGroup):
    waiting_for_url = State()

def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Generate Lead Report", callback_data="ask_for_url")],
        [InlineKeyboardButton(text="🏆 Top 3 Rated Companies", callback_data="stat_top_3")],
        [InlineKeyboardButton(text="🌐 Website Statistics", callback_data="stat_websites")]
    ])

def get_premium_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔓 Upgrade to Premium", callback_data="upgrade_premium")]
    ])

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    welcome_text = (
        "👋 Hello! I am the B2B Lead Extractor (Demo Environment).\n\n"
        "I can extract, clean, and structure B2B contacts directly into an Excel pipeline. "
        "Use the options below to interact with the database."
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
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT business_name, rating FROM leads WHERE rating IS NOT NULL ORDER BY rating DESC LIMIT 3")
        rows = await cursor.fetchall()

        text = "🏆 **Top 3 Rated Companies:**\n\n"
        for idx, (name, rating) in enumerate(rows, 1):
            text += f"{idx}. {name} - ⭐ {rating}\n"

        await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "stat_websites")
async def handle_websites(callback: CallbackQuery):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM leads WHERE website IS NOT NULL")
        with_web = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM leads")
        total = (await cursor.fetchone())[0]

        percentage = round((with_web / total) * 100, 1) if total > 0 else 0.0

        text = (
            "🌐 **Digital Presence Stats:**\n\n"
            f"• Total Leads: {total}\n"
            f"• Have a Website: {with_web}\n"
            f"• Conversion potential: {percentage}%"
        )
        
        await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

# FSM: STEP 1
@dp.callback_query(F.data == "ask_for_url")
async def request_url(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "🔗 **Please send me the target directory URL you want to scrape.**\n\n"
        "*Example:* `https://www.yellowpages.com/dallas-tx/plumbers`",
        parse_mode="Markdown"
    )

    await state.set_state(ScraperState.waiting_for_url)
    await callback.answer()

# FSM: STEP 2
@dp.message(ScraperState.waiting_for_url)
async def process_target_url(message: Message, state: FSMContext):
    target_url = message.text.strip()

    # Domain limit validation
    if "yellowpages.com" not in target_url:
        await message.answer("⚠️ Invalid URL. This parser MVP is currently optimized strictly for `yellowpages.com` domains. Please try again with a supported link.")
        return

    user_id = message.from_user.id
    is_premium = True # TEMPORARY!!!

    loading_msg = await message.answer("⏳ Wiping old database and launching Playwright browser...")

    # Launching scraper
    try:
        stats = await scrape_directory(target_url)
    except Exception as e:
        await loading_msg.edit_text(f"⚠️ Scraping failed: {e}")
        await state.clear()
        return

    if stats["total_found"] == 0:
        await loading_msg.edit_text("⚠️ No results found on this page. Make sure the URL points to a valid search directory.")
        await state.clear()
        return

    await loading_msg.edit_text(f"✅ Extracted {stats['total_found']} raw cards. Executing Data Deduplication...")
    await asyncio.sleep(1.0)

    # Export Gatekeeping
    if is_premium:
        export_to_excel(limit=None)
        caption_text = (
            f"🎯 **Data Pipeline Completed!**\n\n"
            f"• Cards parsed: {stats['total_found']}\n"
            f"• Unique leads added: {stats['new_added']}\n\n"
            f"Here is your full premium dataset."
        )
    else:
        export_to_excel(limit=FREE_TIER_LIMIT)
        caption_text = (
            f"🎯 **Data Pipeline Completed!**\n\n"
            f"• Cards parsed: {stats['total_found']}\n"
            f"• Unique leads added: {stats['new_added']}\n\n"
            f"⚠️ *This is a free Demo Report (limited to {FREE_TIER_LIMIT} rows).* Upgrade to Premium to export the entire database."
        )

    file_path = EXPORT_FILE

    if os.path.exists(file_path):
        document = FSInputFile(file_path)
        markup = get_main_keyboard() if is_premium else get_premium_keyboard()

        await message.answer_document(
            document,
            caption=caption_text,
            reply_markup=markup,
            parse_mode="Markdown"
        )
        await loading_msg.delete()
    else:
        await message.answer("⚠️ An error occurred while generating the file.")

    await state.clear()

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
async def handle_any_text(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == ScraperState.waiting_for_url.state:
        return
    
    if message.text == "/premium":
        return
    
    await message.answer(
        "⚠️ This is a portfolio demo environment.\n"
        "Text input is disabled. Please use the button below to test the data engineering pipeline.",
        reply_markup=get_main_keyboard()
    )

async def main():
    init_db()
    logging.info("🤖 Bot successfully launched and ready to work!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())