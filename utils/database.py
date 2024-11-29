import logging
import time
import psycopg2

# def connect_db():
#     conn = sqlite3.connect('lessons.db')
#     return conn

# def create_table():
#     conn = connect_db()
#     cursor = conn.cursor()

#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS lessons_data (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             lesson_no INTEGER NOT NULL,
#             alphabet TEXT NOT NULL,
#             file_name TEXT NOT NULL
#         )
#     ''')

#     conn.commit()
#     conn.close()


async def insert_lesson_data(lesson_no, alphabet, file_name, probability, force_fully):
    conn = None
    try:
        conn = psycopg2.connect(
            dbname='lessons_database',
            user='ai_quran',
            password='aiquran123',
            host='localhost'
        )
        cursor = conn.cursor()
        insert_query = """
        INSERT INTO lessons_data (lesson_no, alphabet, file_name, probability, force_fully)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (lesson_no, alphabet, file_name, probability, force_fully))
        conn.commit()
        logging.info("Data inserted successfully.")
    except psycopg2.OperationalError as e:
        logging.error(f"OperationalError: {e}")
    except psycopg2.Error as e:
        logging.error(f"Error: {e}")
    finally:
        if conn:
            conn.close()

def current_milli_time():
    return round(time.time() * 1000)