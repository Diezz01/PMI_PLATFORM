# the resposabilitties are:
# - signup
# - login

from sqlalchemy.orm import Session

from app.services.user_service import get_user_by_email
from app.configs.security import create_access_token, vefify_hash_pwd
from app.models.user import User

def auth_user (db:Session, email: str, pwd: str) -> User | None:
    #fecth the user from the user table
    user = get_user_by_email(db, email)

    #check if the user exixst before the login procedure
    if not user:
        return None

    #check if the password is correct
    if not vefify_hash_pwd(pwd, user.password_hash):
        return None

    return user

def create_user_access_token(user: User) -> str:
    return create_access_token(
            {
                "sub":str(user.id) #sub -> subject this allow to identify the owner of the token
            }
    )
    