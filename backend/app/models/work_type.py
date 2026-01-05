import enum


class WorkType(str, enum.Enum):
    """Типы работ для аттестации"""
    TEST = "TEST"                        # Контрольная работа
    INDEPENDENT_WORK = "INDEPENDENT_WORK"  # Самостоятельная работа
    COLLOQUIUM = "COLLOQUIUM"            # Коллоквиум
    FINAL_PROJECT = "FINAL_PROJECT"      # Итоговый проект
