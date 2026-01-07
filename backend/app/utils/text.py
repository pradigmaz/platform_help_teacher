"""
Утилиты для работы с текстом.
Единая точка для нормализации ФИО и других текстовых операций.
"""
import re
from typing import Optional


def normalize_fio(text: str) -> str:
    """
    Нормализация ФИО: убирает лишние пробелы, каждое слово с заглавной.
    Используется для сравнения и отображения.
    """
    if not text:
        return ""
    return ' '.join(word.capitalize() for word in text.strip().split())


def normalize_fio_for_comparison(text: str) -> str:
    """
    Нормализация ФИО для сравнения: lowercase, убирает лишние пробелы.
    """
    if not text:
        return ""
    return ' '.join(text.lower().split())


def sanitize_name(raw_name: str, pattern: str = r'[^а-яёА-ЯЁa-zA-Z\s\-]') -> Optional[str]:
    """
    Очищает имя от мусора (цифры, спецсимволы).
    Возвращает None если результат невалидный.
    """
    if not isinstance(raw_name, str):
        return None
    
    clean = re.sub(pattern, ' ', raw_name)
    clean = " ".join(clean.split())
    
    parts = [p.strip().capitalize() for p in clean.split() if len(p.strip()) > 1]
    
    if len(parts) >= 2:
        return " ".join(parts[:3])
    return None


def fio_matches(name1: str, name2: str, threshold: float = 0.85) -> bool:
    """
    Проверка совпадения ФИО (fuzzy).
    Совпадает если:
    - Точное совпадение
    - Фамилия+имя совпадают (без отчества)
    - Фамилия совпадает + имя начинается так же (сокращения)
    - Расстояние Левенштейна для фамилии <= 1 (опечатки)
    """
    n1 = normalize_fio_for_comparison(name1)
    n2 = normalize_fio_for_comparison(name2)
    
    if not n1 or not n2:
        return False
    
    if n1 == n2:
        return True
    
    parts1 = n1.split()
    parts2 = n2.split()
    
    if not parts1 or not parts2:
        return False
    
    surname1, surname2 = parts1[0], parts2[0]
    
    # Фамилия должна совпадать (или быть очень похожей)
    if surname1 != surname2:
        # Допускаем 1 опечатку в фамилии
        if _levenshtein_distance(surname1, surname2) > 1:
            return False
    
    # Если есть имя — проверяем
    if len(parts1) >= 2 and len(parts2) >= 2:
        name1_first, name2_first = parts1[1], parts2[1]
        # Точное совпадение имени
        if name1_first == name2_first:
            return True
        # Сокращённое имя (Ал. -> Александр)
        min_len = min(len(name1_first), len(name2_first), 2)
        if name1_first[:min_len] == name2_first[:min_len]:
            return True
        # Допускаем 1 опечатку в имени
        if _levenshtein_distance(name1_first, name2_first) <= 1:
            return True
    
    # Если только фамилия совпала точно — тоже ок
    return surname1 == surname2


def _levenshtein_distance(s1: str, s2: str) -> int:
    """Вычисляет расстояние Левенштейна между двумя строками."""
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def fio_similarity(fio1: str, fio2: str) -> float:
    """
    Сравнение ФИО. Возвращает 0.0-1.0.
    """
    parts1 = fio1.lower().split()
    parts2 = fio2.lower().split()
    if not parts1 or not parts2:
        return 0.0
    if parts1 == parts2:
        return 1.0
    matches = sum(1 for p1 in parts1 if p1 in parts2)
    total = max(len(parts1), len(parts2))
    return matches / total if total > 0 else 0.0
