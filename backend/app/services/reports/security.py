"""
Модуль безопасности для публичных отчётов.

Генерация кодов и работа с PIN-кодами.
"""
import secrets
import string

from passlib.context import CryptContext

# Контекст для хеширования PIN-кодов
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Символы для генерации кода (без похожих: 0/O, 1/l/I)
CODE_ALPHABET = string.ascii_uppercase.replace('O', '').replace('I', '') + \
                string.digits.replace('0', '').replace('1', '')
CODE_LENGTH = 8


def generate_code() -> str:
    """
    Генерация криптографически безопасного 8-символьного кода.
    
    Использует secrets.choice для криптографической безопасности.
    Алфавит исключает похожие символы (0/O, 1/l/I).
    
    Returns:
        str: 8-символьный код (например: "A2B3C4D5")
    """
    return ''.join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


def hash_pin(pin: str) -> str:
    """
    Хеширование PIN-кода с использованием bcrypt.
    
    Args:
        pin: PIN-код (4-6 цифр)
        
    Returns:
        str: bcrypt хеш PIN-кода
    """
    return pwd_context.hash(pin)


def verify_pin(plain_pin: str, hashed_pin: str) -> bool:
    """
    Проверка PIN-кода.
    
    Args:
        plain_pin: Введённый PIN-код
        hashed_pin: Хеш из БД
        
    Returns:
        bool: True если PIN верный
    """
    return pwd_context.verify(plain_pin, hashed_pin)
