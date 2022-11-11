import secrets
import string
from sqlalchemy.orm import Session
from . import crud


def create_random_key(length: int) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


def create_unique_random_key(db: Session) -> str:
    key = create_random_key(5)
    while crud.get_db_url_by_key(db, key, is_active=False):
        key = create_random_key(5)
    return key
