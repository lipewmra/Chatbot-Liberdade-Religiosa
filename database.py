# database.py
import sqlite3
import pandas as pd
from datetime import datetime

import hashlib

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
    
    # Create Admin Auth table
    c.execute('''
        CREATE TABLE IF NOT EXISTS admin_auth (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            password_hash TEXT
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
    
    # Initialize default admin password if not exists
    init_admin_auth()

def init_admin_auth():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM admin_auth")
    if c.fetchone()[0] == 0:
        # Default password: "admin"
        default_hash = hashlib.sha256("admin".encode()).hexdigest()
        c.execute("INSERT INTO admin_auth (password_hash) VALUES (?)", (default_hash,))
        conn.commit()
    conn.close()

def verify_password(password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT password_hash FROM admin_auth LIMIT 1")
    stored_hash = c.fetchone()
    conn.close()
    
    if stored_hash:
        input_hash = hashlib.sha256(password.encode()).hexdigest()
        return input_hash == stored_hash[0]
    return False

def update_password(new_password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    new_hash = hashlib.sha256(new_password.encode()).hexdigest()
    # Update the single row
    c.execute("UPDATE admin_auth SET password_hash = ?", (new_hash,))
    # If for some reason distinct row didn't exist (edge case), insert it
    if c.rowcount == 0:
         c.execute("INSERT INTO admin_auth (password_hash) VALUES (?)", (new_hash,))
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

def get_monthly_stats():
    conn = sqlite3.connect(DB_NAME)
    query = """
        SELECT strftime('%Y-%m', timestamp) as month, COUNT(*) as count 
        FROM logs 
        GROUP BY month 
        ORDER BY month
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def get_keyword_stats():
    conn = sqlite3.connect(DB_NAME)
    # Get all user inputs
    df = pd.read_sql("SELECT user_input FROM logs", conn)
    conn.close()
    
    if df.empty:
        return pd.DataFrame(columns=['keyword', 'count'])
        
    # Basic keyword extraction (split by space, lowercase, remove common short words)
    all_text = " ".join(df['user_input'].astype(str)).lower()
    
    # Remove punctuation
    import string
    all_text = all_text.translate(str.maketrans('', '', string.punctuation))
    
    words = all_text.split()
    
    # Filter out common stop words (Portuguese)
    stop_words = set(['de', 'a', 'o', 'que', 'e', 'do', 'da', 'em', 'um', 'para', 'com', 'não', 'uma', 'os', 'no', 'se', 'na', 'por', 'mais', 'as', 'dos', 'como', 'mas', 'foi', 'ao', 'ele', 'das', 'tem', 'à', 'seu', 'sua', 'ou', 'ser', 'quando', 'muito', 'há', 'nos', 'já', 'está', 'eu', 'também', 'só', 'pelo', 'pela', 'até', 'isso', 'ela', 'entre', 'era', 'depois', 'sem', 'mesmo', 'aos', 'ter', 'seus', 'quem', 'nas', 'me', 'esse', 'eles', 'estão', 'você', 'tinha', 'foram', 'essa', 'num', 'nem', 'suas', 'meu', 'às', 'minha', 'têm', 'numa', 'pelos', 'elas', 'qual', 'nós', 'lhe', 'deles', 'essas', 'esses', 'pelas', 'este', 'dele', 'tu', 'te', 'vocês', 'vos', 'lhes', 'meus', 'minhas', 'teu', 'tua', 'teus', 'tuas', 'nosso', 'nossa', 'nossos', 'nossas', 'dela', 'delas', 'esta', 'estes', 'estas', 'aquele', 'aquela', 'aqueles', 'aquelas', 'isto', 'aquilo', 'estou', 'está', 'estamos', 'estão', 'estive', 'esteve', 'estivemos', 'estiveram', 'estava', 'estávamos', 'estavam', 'estivera', 'estivéramos', 'esteja', 'estejamos', 'estejam', 'estivesse', 'estivéssemos', 'estivessem', 'estiver', 'estivermos', 'estiverem', 'hei', 'há', 'havemos', 'hão', 'houve', 'houvemos', 'houveram', 'houvera', 'houvéramos', 'haja', 'hajamos', 'hajam', 'houvesse', 'houvéssemos', 'houvessem', 'houver', 'houvermos', 'houverem', 'houverei', 'houverá', 'houveremos', 'houverão', 'houveria', 'houveríamos', 'houveriam', 'sou', 'somos', 'são', 'era', 'éramos', 'eram', 'fui', 'foi', 'fomos', 'foram', 'fora', 'fôramos', 'seja', 'sejamos', 'sejam', 'fosse', 'fôssemos', 'fossem', 'for', 'formos', 'forem', 'serei', 'será', 'seremos', 'serão', 'seria', 'seríamos', 'seriam', 'tenho', 'tem', 'temos', 'tém', 'tinha', 'tínhamos', 'tinham', 'tive', 'teve', 'tivemos', 'tiveram', 'tivera', 'tivéramos', 'tenha', 'tenhamos', 'tenham', 'tivesse', 'tivéssemos', 'tivessem', 'tiver', 'tivermos', 'tiverem', 'terei', 'terá', 'teremos', 'terão', 'teria', 'teríamos', 'teriam'])
    
    filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
    
    # Count frequency
    from collections import Counter
    word_counts = Counter(filtered_words)
    
    # Convert to DataFrame
    stats_df = pd.DataFrame(word_counts.most_common(20), columns=['keyword', 'count'])
    return stats_df

def reset_database():
    """
    Clears all data from logs, faqs, and reference_links.
    Does NOT clear admin_auth (handled separately).
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM logs")
    c.execute("DELETE FROM faqs")
    c.execute("DELETE FROM reference_links")
    # Reset auto-increment counters if desired, but not strictly necessary for simple reset
    c.execute("DELETE FROM sqlite_sequence WHERE name IN ('logs', 'faqs', 'reference_links')")
    conn.commit()
    conn.close()

def reset_admin_password():
    """
    Resets the admin password to 'admin'.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    default_hash = hashlib.sha256("admin".encode()).hexdigest()
    c.execute("UPDATE admin_auth SET password_hash = ?", (default_hash,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
