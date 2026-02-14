# database.py
import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "chatbot.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Create logs table
    c.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_input TEXT,
            bot_response TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create FAQs table (optional for now, but good for admin)
    c.execute('''
        CREATE TABLE IF NOT EXISTS faqs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            answer TEXT
        )
    ''')

    # Create Reference Links table
    c.execute('''
        CREATE TABLE IF NOT EXISTS reference_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT,
            title TEXT,
            content TEXT,
            added_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def log_message(user_input, bot_response):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO logs (user_input, bot_response) VALUES (?, ?)", (user_input, bot_response))
    conn.commit()
    conn.close()

def get_logs():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM logs ORDER BY timestamp DESC LIMIT 50", conn)
    conn.close()
    return df

def get_stats():
    conn = sqlite3.connect(DB_NAME)
    # Simple stats: count messages
    count = pd.read_sql("SELECT COUNT(*) as count FROM logs", conn).iloc[0]['count']
    conn.close()
    return {"total_messages": count}

if __name__ == "__main__":
    init_db()
