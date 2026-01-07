"""
Константы для модуля расписания.
Единый источник истины для backend.
"""
from app.models.schedule import LessonType

# Маппинг времени на номер пары
TIME_TO_LESSON_NUMBER = {
    "08:30-10:00": 1,
    "10:10-11:40": 2,
    "11:50-13:20": 3,
    "13:40-15:10": 4,
    "15:20-16:50": 5,
    "17:00-18:30": 6,
    "18:40-20:10": 7,
    "20:20-21:50": 8,
}

# Обратный маппинг: номер пары -> время
LESSON_NUMBER_TO_TIME = {v: k for k, v in TIME_TO_LESSON_NUMBER.items()}

# Маппинг текста типа занятия (из парсера) -> строка
LESSON_TYPE_TEXT_MAP = {
    "лек": "lecture",
    "лек.": "lecture",
    "лаб": "lab",
    "лаб.": "lab",
    "пр": "practice",
    "пр.": "practice",
}

# Маппинг строки -> enum LessonType
LESSON_TYPE_ENUM_MAP = {
    "lecture": LessonType.LECTURE,
    "lab": LessonType.LAB,
    "practice": LessonType.PRACTICE,
}

# Шаг парсинга (API kis.vgltu.ru возвращает 2 недели)
PARSE_STEP_DAYS = 14

# Порог пустых недель для определения конца семестра
SEMESTER_END_EMPTY_WEEKS_THRESHOLD = 2

# Максимальный номер пары
MAX_LESSON_NUMBER = 8

# Дни недели (для валидации)
WEEKDAY_SUNDAY = 6
