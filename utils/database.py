from utils.app_logger import logger
import time
import psycopg2

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
        logger.info("Data inserted successfully.")
    except psycopg2.OperationalError as e:
        logger.error(f"OperationalError: {e}")
    except psycopg2.Error as e:
        logger.error(f"Error: {e}")
    finally:
        if conn:
            conn.close()

def current_milli_time():
    return round(time.time() * 1000)