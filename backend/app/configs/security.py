#the responsability is to manage
# - password hashing
# - JWT
# - token checking
import jwt
from datetime import datetime, timedelta, timezone

from app.configs.config import settings

from pwdlib import PasswordHash

#-------Hashing section

hashing_object = PasswordHash.recommended()#object used for hashing the pwd

#function used for hash the pwd 
def hash_pwd_tool (pwd : str) -> str:
    return hashing_object.hash(pwd)

#function used to verify the hash with the pwd
def vefify_hash_pwd (plain_pwd: str, hashed_pwd: str) -> bool:
    return hashing_object.verify(plain_pwd, hashed_pwd)


#-------Token Section

#this function create a token that it is assigned to a user by including its own ID
#the token will be signed using JWT_SECRET_KEY
def create_access_token(data: dict ) -> str:
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp":expire})

    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, settings.JWT_ALGORITHM)