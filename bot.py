import os
import sqlite3
import time
import threading
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

OWNER_ID = 5486316497
DB = "timers.db"

# Initialize DB
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

# Timer checker thread
def timer_checker(bot):
    while True:
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT chat_id, end_time FROM timers")
        rows = c.fetchall()
        now = int(time.time())
        for chat_id, end_time in rows:
            if now >= end_time:
                try:
                    bot.send_message(chat_id=chat_id, text="⚠️ ALERT")
                except:
                    pass
                delete_timer(chat_id)
        conn.close()
        time.sleep(5)

# /timer command
def start_timer(update, context):
    if update.effective_user.id != OWNER_ID:
        return
    if not context.args:
        update.message.reply_text("Usage: /timer 0.5 (hours, fractions allowed)")
        return
    try:
        hours = float(context.args[0])
        if hours <= 0:
            update.message.reply_text("Enter a number greater than 0")
            return
    except:
        update.message.reply_text("Enter a valid number")
        return
    chat_id = update.effective_chat.id
    if get_timer(chat_id):
        update.message.reply_text("Timer already running")
        return
    end_time = int(time.time() + hours * 3600)
    set_timer(chat_id, end_time)
    update.message.reply_text(f"⏳ Timer started for {hours} hours")

# Stop timer with "Panama"
def panama_stop(update, context):
    if update.effective_user.id != OWNER_ID:
        return
    chat_id = update.effective_chat.id
    if get_timer(chat_id):
        delete_timer(chat_id)
        update.message.reply_text("🛑 Timer stopped")

def main():
    TOKEN = os.environ.get("BOT_TOKEN")
    if not TOKEN:
        print("BOT_TOKEN not set in environment")
        return

    init_db()

    bot = Bot(TOKEN)
    updater = Updater(bot=bot, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("timer", start_timer))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex("^Panama$"), panama_stop))

    # Start timer checker thread
    threading.Thread(target=timer_checker, args=(bot,), daemon=True).start()

    print("Bot running...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
