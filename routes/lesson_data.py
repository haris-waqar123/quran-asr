from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from utils.database import insert_lesson_data
from utils.extensions import verify_token
from utils.app_logger import logger

router = APIRouter()

class LessonData(BaseModel):
    lesson_no: int
    alphabet: str
    file_name: str

@router.post("/add_lesson_data")
async def add_lesson_data(data: LessonData, authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail='Authorization header is missing')

    try:
        token = authorization.split(" ")[1]
        logger.info(f'Authorization header for Qaida: {token}')

        user_info = verify_token(token)
    except Exception as e:
        logger.error(f"Failed to Authorize: {e}")
        raise HTTPException(status_code=401, detail='Failed to Authorize')

    if user_info is None:
        logger.error(f"User {user_info}, Invalid Token")
        raise HTTPException(status_code=401, detail='Invalid token')

    lesson_no = data.lesson_no
    alphabet = data.alphabet
    file_name = data.file_name

    insert_lesson_data(lesson_no, alphabet, file_name, 0, True)

    return {"message": "Data saved successfully!"}
