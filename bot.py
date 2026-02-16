import os
import sqlite3
import time
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

OWNER_ID = 5486316497
DB = "timers.db"

# Database functions
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS timers (
            chat_id INTEGER PRIMARY KEY,
            end_time INTEGER
        )
    """)
    conn.commit()
    conn.close()

def set_timer(chat_id, end_time):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("REPLACE INTO timers (chat_id, end_time) VALUES (?, ?)", (chat_id, end_time))
    conn.commit()
    conn.close()

def delete_timer(chat_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM timers WHERE chat_id=?", (chat_id,))
    conn.commit()
    conn.close()

def get_timer(chat_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT end_time FROM timers WHERE chat_id=?", (chat_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

# Background checker
async def timer_checker(app: Application):
    while True:
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT chat_id, end_time FROM timers")
        rows = c.fetchall()
        now = int(time.time())
        for chat_id, end_time in rows:
            if now >= end_time:
                try:
                    await app.bot.send_message(chat_id=chat_id, text="⚠️ ALERT")
                except Exception as e:
                    print("Failed to send alert:", e)
                delete_timer(chat_id)
        conn.close()
        await asyncio.sleep(5)

# Start timer
async def start_timer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage: /timer 0.5 (fractional hours allowed)")
        return

    try:
        hours = float(context.args[0])
        if hours <= 0:
            await update.message.reply_text("Please enter a number greater than 0.")
            return
    except:
        await update.message.reply_text("Please enter a valid number.")
        return

    chat_id = update.effective_chat.id
    if get_timer(chat_id):
        await update.message.reply_text("A timer is already running.")
        return

    end_time = int(time.time() + hours * 3600)
    set_timer(chat_id, end_time)
    await update.message.reply_text(f"⏳ Timer started for {hours} hours.")

# Stop timer
async def panama_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    chat_id = update.effective_chat.id
    if get_timer(chat_id):
        delete_timer(chat_id)
        await update.message.reply_text("🛑 Timer stopped.")

# Main
def main():
    TOKEN = os.environ.get("BOT_TOKEN")
    if not TOKEN:
        print("Error: BOT_TOKEN not set")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("timer", start_timer))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Panama$"), panama_stop))

    # Start background task
    asyncio.create_task(timer_checker(app))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
