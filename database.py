# database.py
import sqlite3
import pickle

DB_NAME = 'database.db'

def setup_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Tabela de usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            encoding BLOB NOT NULL
        )
    ''')

    # Tabela de conversas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            user_message TEXT NOT NULL,
            assistant_response TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

def register_user(name, encoding):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    serialized_encoding = pickle.dumps(encoding)
    cursor.execute('INSERT INTO users (name, encoding) VALUES (?, ?)', (name, serialized_encoding))
    conn.commit()
    conn.close()

def save_conversation(user_name, user_message, assistant_response):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Obter o ID do usuário
    cursor.execute('SELECT id FROM users WHERE name = ?', (user_name,))
    result = cursor.fetchone()
    if result:
        user_id = result[0]
    else:
        user_id = None
    cursor.execute('''
        INSERT INTO conversations (user_id, user_message, assistant_response)
        VALUES (?, ?, ?)
    ''', (user_id, user_message, assistant_response))
    conn.commit()
    conn.close()

def get_known_encodings():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT encoding FROM users')
    results = cursor.fetchall()
    encodings = [pickle.loads(row[0]) for row in results]
    conn.close()
    return encodings

def get_user_names():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM users')
    results = cursor.fetchall()
    names = [row[0] for row in results]
    conn.close()
    return names