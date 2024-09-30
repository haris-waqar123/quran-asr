from flask import Blueprint, request, jsonify
from pydantic import BaseModel
from utils.database import connect_db
from utils.jwt_utils import get_current_user

router = Blueprint('lesson_data', __name__)

class LessonData(BaseModel):
    lesson_no: int
    alphabet: str
    file_name: str

@router.route("/add_lesson_data", methods=["POST"])
def add_lesson_data():

    current_user = get_current_user()
    
    if not current_user:
        return jsonify({"detail": "Invalid API key"}), 401

    # Parse and validate the request data
    data = LessonData(**request.get_json())
    lesson_no = data.lesson_no
    alphabet = data.alphabet
    file_name = data.file_name

    # Connect to the database and insert the data
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO lessons_data (lesson_no, alphabet, file_name)
        VALUES (?, ?, ?)
    ''', (lesson_no, alphabet, file_name))

    conn.commit()
    conn.close()

    return jsonify({"message": "Data saved successfully!"})
