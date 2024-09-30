from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from flask import request, abort
from pydantic import BaseModel
from API_utils import load_api_key
from config import API_KEY

SECRET_KEY = load_api_key()
ALGORITHM = "HS256"

class TokenData(BaseModel):
    username: str | None = None

class CredentialsException(Exception):
    pass

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise CredentialsException("Could not validate credentials")
        token_data = TokenData(username=username)
        return token_data
    except (JWTError, CredentialsException) as e:
        abort(401, description=str(e))

def get_current_user(token=None):
    if token is None:
        token = request.headers.get("Authorization")
        if not token:
            abort(401, description="Authorization header missing")
        token = token.replace("Bearer ", "")
    return verify_token(token)