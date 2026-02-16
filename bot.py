import os
import time
import threading
import sqlite3
import telebot

OWNER_ID = 5486316497
DB_FILE = "timers.db"

# --- Initialize bot ---
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    print("BOT_TOKEN not set")
    exit()

bot = telebot.TeleBot(TOKEN)

# --- Database ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS timers (
                    chat_id INTEGER PRIMARY KEY,
                    end_time INTEGER
                )""")
    conn.commit()
    conn.close()

def set_timer(chat_id, end_time):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("REPLACE INTO timers (chat_id, end_time) VALUES (?, ?)", (chat_id, end_time))
    conn.commit()
    conn.close()

def delete_timer(chat_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM timers WHERE chat_id=?", (chat_id,))
    conn.commit()
    conn.close()

def get_timer(chat_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT end_time FROM timers WHERE chat_id=?", (chat_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

# --- Timer checker thread ---
def timer_checker():
    while True:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT chat_id, end_time FROM timers")
        rows = c.fetchall()
        now = int(time.time())
        for chat_id, end_time in rows:
            if now >= end_time:
                try:
                    bot.send_message(chat_id, "⚠️ ALERT")
                except Exception as e:
                    print("Failed to send alert:", e)
                delete_timer(chat_id)
        conn.close()
        time.sleep(5)

# --- Command handlers ---
@bot.message_handler(commands=['timer'])
def start_timer(message):
    if message.from_user.id != OWNER_ID:
        return

    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "Usage: /timer 0.5 (hours, fractions allowed)")
        return

    try:
        hours = float(args[1])
        if hours <= 0:
            bot.reply_to(message, "Enter a number > 0")
            return
    except:
        bot.reply_to(message, "Enter a valid number")
        return

    chat_id = message.chat.id
    if get_timer(chat_id):
        bot.reply_to(message, "Timer already running")
        return

    end_time = int(time.time() + hours * 3600)
    set_timer(chat_id, end_time)
    bot.reply_to(message, f"⏳ Timer started for {hours} hours")

@bot.message_handler(func=lambda m: m.text == "Panama")
def stop_timer(message):
    if message.from_user.id != OWNER_ID:
        return

    chat_id = message.chat.id
    if get_timer(chat_id):
        delete_timer(chat_id)
        bot.reply_to(message, "🛑 Timer stopped")

# --- Main ---
if __name__ == "__main__":
    init_db()
    threading.Thread(target=timer_checker, daemon=True).start()
    print("Bot running...")
    bot.infinity_polling()
