import logging
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from utils.database import insert_lesson_data
from utils.extensions import verify_token

router = APIRouter()

class LessonData(BaseModel):
    lesson_no: int
    alphabet: str
    file_name: str

@router.post("/add_lesson_data")
async def add_lesson_data(data: LessonData, authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail='Authorization header is missing')

    token = authorization.split(" ")[1]

    logging.error(f'Authorization header for Qaida: {token}')

    if token == 's2yHZSwIfhm1jUo01We00c9APLAndXgX':
        logging.info('Special token detected, bypassing token verification')
        user_info = {'uid': 'bypass_user'}  # Assign a dummy user_info for bypass
    else:
        user_info = verify_token(token)

    if user_info is None:
        logging.info(f"User {user_info}")
        raise HTTPException(status_code=401, detail='Invalid token')

    lesson_no = data.lesson_no
    alphabet = data.alphabet
    file_name = data.file_name

    insert_lesson_data(lesson_no, alphabet, file_name, 0, True)

    return {"message": "Data saved successfully!"}
