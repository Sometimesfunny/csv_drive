from jose import jwt
import os

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = "HS256"

def create_access_token(data: dict):
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    data = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
    return data
