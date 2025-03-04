import os
from hashlib import pbkdf2_hmac
import random
import string

from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def get_new_salt(n_bytes: int = 32) -> bytes:
    if not isinstance(n_bytes, int):
        n_bytes = 32  # Force in case of misuse

    return os.urandom(n_bytes)


def gen_new_key(plain_passwd: str) -> tuple:
    """
    Generate a new key and salt to store.
    Returns (key, salt)
    """
    salt = get_new_salt(32)
    return (calc_key(plain_passwd, salt), salt)


def verify_key(plain_passwd: str, salt: bytes, stored_key: bytes) -> bool:
    key_tmp = calc_key(plain_passwd, salt)
    return stored_key == key_tmp


def calc_key(passwd: str, salt: bytes) -> bytes:
    """
    Calculate a password+salt hash
    password_hash = sha256(passwd+salt) for large number of itirations
    """
    return pbkdf2_hmac(
        settings.CRYPTO_HASH_FUNCTION,
        passwd.encode(settings.CRYPTO_PASSWD_ENCODING),
        salt,
        settings.CRYTPTO_HMAC_ITIRATIONS,
    )

def generate_complex_password(length: int) -> str:
    characters = string.ascii_letters + string.digits + string.punctuation
    password = "".join(random.choice(characters) for _ in range(length))
    return password