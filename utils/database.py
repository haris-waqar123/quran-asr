import sqlite3
import time

def connect_db():
    conn = sqlite3.connect('lessons.db')
    return conn

def create_table():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lessons_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_no INTEGER NOT NULL,
            alphabet TEXT NOT NULL,
            file_name TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

def current_milli_time():
    return round(time.time() * 1000)