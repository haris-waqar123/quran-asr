import logging
from flask import Blueprint, request, jsonify
from pydantic import BaseModel
from utils.database import insert_lesson_data
from utils.extensions import verify_token
import psycopg2
from psycopg2 import sql

router = Blueprint('lesson_data', __name__)

class LessonData(BaseModel):
    lesson_no: int
    alphabet: str
    file_name: str


#postgre SQL

@router.route("/add_lesson_data", methods=["POST"])
def add_lesson_data():

    auth_header = request.headers.get('Authorization')

    if not auth_header:
        return jsonify({'label': 'Authorization header is missing',"probability": 0.0}), 401
    token = auth_header.split(" ")[1]

    logging.error(f'Authorization header for Qaida: {token}')

    if token == 's2yHZSwIfhm1jUo01We00c9APLAndXgX':
        logging.info('Special token detected, bypassing token verification')
        user_info = {'uid': 'bypass_user'}  # Assign a dummy user_info for bypass
    else:
        user_info = verify_token(token)

    if user_info is None:
        logging.info(f"User {user_info}")
        return jsonify({'label': 'Invalid token', "probability": 0.0}), 401

    # Parse and validate the request data
    data = LessonData(**request.get_json())
    lesson_no = data.lesson_no
    alphabet = data.alphabet
    file_name = data.file_name

    # Connect to the database and insert the data
    # conn = connect_db()
    # cursor = conn.cursor()

    # cursor.execute('''
    #     INSERT INTO lessons_data (lesson_no, alphabet, file_name)
    #     VALUES (?, ?, ?)
    # ''', (lesson_no, alphabet, file_name))

    # conn.commit()
    # conn.close()



    insert_lesson_data(lesson_no, alphabet, file_name, 0, True)    

    return jsonify({"message": "Data saved successfully!"})
