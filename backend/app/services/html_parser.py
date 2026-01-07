"""
HTML парсер расписания ВГЛТУ
"""
import logging
import re
import html
from datetime import date
from typing import Optional
from dataclasses import dataclass, field

from bs4 import BeautifulSoup

from app.services.schedule_constants import TIME_TO_LESSON_NUMBER, LESSON_TYPE_TEXT_MAP

logger = logging.getLogger(__name__)

MONTHS = {
    'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
    'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
    'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
}

# Паттерны для распознавания подгрупп (Fix #19)
SUBGROUP_PATTERNS = [
    (r'1\s*п\.?г\.?', 1),
    (r'1\s*п/г', 1),
    (r'1п\.?г\.?', 1),
    (r'подгр\.?\s*1', 1),
    (r'2\s*п\.?г\.?', 2),
    (r'2\s*п/г', 2),
    (r'2п\.?г\.?', 2),
    (r'подгр\.?\s*2', 2),
]

# Паттерны для распознавания групп (Fix #21)
# Поддержка разных факультетов ВГЛТУ
GROUP_PATTERNS = [
    r'^ИС[-\s]?\d',      # ИС-241, ИС241
    r'^ЛД[-\s]?\d',      # Лесное дело
    r'^ЛХ[-\s]?\d',      # Лесное хозяйство
    r'^МТ[-\s]?\d',      # Механические технологии
    r'^ЭК[-\s]?\d',      # Экономика
    r'^СТ[-\s]?\d',      # Строительство
    r'^ДИ[-\s]?\d',      # Дизайн
    r'^АР[-\s]?\d',      # Архитектура
    r'^[А-ЯЁ]{2,3}[-\s]?\d{2,3}',  # Общий паттерн: 2-3 буквы + цифры
]


@dataclass
class ParsedLesson:
    """Распарсенное занятие"""
    date: date
    lesson_number: int
    lesson_type: str  # lecture, lab, practice
    subject: str
    groups: list[str]
    subgroup: Optional[int]  # 1, 2 или None (вся группа)
    room: Optional[str]


@dataclass
class ParseResult:
    """Результат парсинга с метаданными (Fix #20)"""
    lessons: list[ParsedLesson] = field(default_factory=list)
    is_empty: bool = False
    structure_changed: bool = False
    error: Optional[str] = None


class ScheduleHtmlParser:
    """Парсер HTML расписания"""
    
    def parse(self, html_content: str) -> list[ParsedLesson]:
        """Парсинг HTML расписания (legacy interface)"""
        result = self.parse_with_metadata(html_content)
        return result.lessons
    
    def parse_with_metadata(self, html_content: str) -> ParseResult:
        """Парсинг HTML расписания с метаданными"""
        if not html_content or not html_content.strip():
            return ParseResult(is_empty=True)
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Fix #18: Fallback стратегии для поиска контейнера
        table_div = self._find_schedule_container(soup)
        if not table_div:
            logger.error("Schedule container not found - HTML structure may have changed")
            return ParseResult(structure_changed=True, error="Schedule container not found")
        
        day_blocks = self._find_day_blocks(table_div)
        
        # Fix #20: Различаем пустое расписание и ошибку парсинга
        if not day_blocks:
            # Проверяем есть ли вообще контент
            if table_div.get_text(strip=True):
                logger.warning("Day blocks not found but container has content - structure changed?")
                return ParseResult(structure_changed=True, error="Day blocks not found")
            return ParseResult(is_empty=True)
        
        logger.info(f"Found {len(day_blocks)} day blocks")
        
        lessons = []
        for day_block in day_blocks:
            date_elem = day_block.find('strong')
            if not date_elem:
                continue
            
            date_text = html.unescape(date_elem.get_text(strip=True))
            lesson_date = self._parse_date(date_text)
            if not lesson_date:
                continue
            
            table = day_block.find('table')
            if not table:
                continue
            
            for row in table.find_all('tr'):
                parsed = self._parse_row(row, lesson_date)
                if parsed:
                    lessons.append(parsed)
        
        return ParseResult(lessons=lessons, is_empty=len(lessons) == 0)
    
    def _find_schedule_container(self, soup) -> Optional:
        """Fix #18: Найти контейнер расписания с fallback стратегиями"""
        # Стратегия 1: div.table (основная)
        container = soup.find('div', class_='table')
        if container:
            return container
        
        # Стратегия 2: div с таблицами внутри
        for div in soup.find_all('div'):
            if div.find('table'):
                tables = div.find_all('table')
                if len(tables) >= 1:
                    logger.warning("Using fallback: found div with tables")
                    return div
        
        # Стратегия 3: body если есть таблицы
        if soup.find('table'):
            logger.warning("Using fallback: searching in body")
            return soup.body or soup
        
        return None
    
    def _find_day_blocks(self, table_div) -> list:
        """Найти блоки дней в HTML с fallback"""
        day_blocks = []
        
        # Стратегия 1: div с margin-bottom: 25px
        for child in table_div.children:
            if hasattr(child, 'name') and child.name == 'div':
                style = child.get('style', '')
                if 'margin-bottom' in style:
                    day_blocks.append(child)
        
        if day_blocks:
            return day_blocks
        
        # Стратегия 2: div содержащие strong (дату) и table
        for div in table_div.find_all('div', recursive=False):
            if div.find('strong') and div.find('table'):
                day_blocks.append(div)
        
        return day_blocks
    
    def _parse_row(self, row, lesson_date: date) -> Optional[ParsedLesson]:
        """Парсинг строки таблицы"""
        cells = row.find_all('td')
        if len(cells) < 2:
            return None
        
        time_text = cells[0].get_text(strip=True)
        info_lines = self._extract_info_lines(cells[1])
        
        return self._parse_lesson_row(time_text, info_lines, lesson_date)
    
    def _extract_info_lines(self, info_cell) -> list[str]:
        """Извлечь строки информации из ячейки"""
        info_lines = []
        for content in info_cell.children:
            if isinstance(content, str):
                text = html.unescape(content.strip())
                if text:
                    info_lines.append(text)
            elif hasattr(content, 'name') and content.name != 'br':
                text = html.unescape(content.get_text(strip=True))
                if text:
                    info_lines.append(text)
        return info_lines
    
    def _parse_date(self, date_text: str) -> Optional[date]:
        """Парсинг даты вида '01 сентября 2025'"""
        match = re.match(r'(\d{1,2})\s+(\w+)\s+(\d{4})', date_text)
        if not match:
            return None
        
        day = int(match.group(1))
        month_name = match.group(2).lower()
        year = int(match.group(3))
        
        month = MONTHS.get(month_name)
        if not month:
            return None
        
        try:
            return date(year, month, day)
        except ValueError:
            return None
    
    def _parse_lesson_row(self, time_text: str, info_lines: list[str], lesson_date: date) -> Optional[ParsedLesson]:
        """Парсинг строки с информацией о паре"""
        lesson_number = TIME_TO_LESSON_NUMBER.get(time_text, 0)
        if not lesson_number:
            return None
        
        lines = [line.strip() for line in info_lines if line.strip()]
        if not lines:
            return None
        
        logger.debug(f"Parsing lesson: {lines}")
        
        lesson_type, subject = self._parse_type_and_subject(lines[0])
        subgroup, lines = self._extract_subgroup(lines)
        groups, room = self._extract_groups_and_room(lines[1:])
        
        if not groups:
            logger.debug(f"No groups found in lines: {lines}")
            return None
        
        return ParsedLesson(
            date=lesson_date,
            lesson_number=lesson_number,
            lesson_type=lesson_type,
            subject=subject,
            groups=groups,
            subgroup=subgroup,
            room=room
        )
    
    def _parse_type_and_subject(self, first_line: str) -> tuple[str, str]:
        """Извлечь тип занятия и предмет"""
        for key, value in LESSON_TYPE_TEXT_MAP.items():
            if first_line.lower().startswith(key):
                subject = first_line[len(key):].lstrip('. ')
                return value, subject
        return "lecture", first_line
    
    def _extract_subgroup(self, lines: list[str]) -> tuple[Optional[int], list[str]]:
        """Fix #19: Извлечь подгруппу с расширенными паттернами"""
        subgroup = None
        for i, line in enumerate(lines):
            for pattern, sg_num in SUBGROUP_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    subgroup = sg_num
                    lines[i] = re.sub(pattern, '', line, flags=re.IGNORECASE).strip()
                    return subgroup, lines
        return subgroup, lines
    
    def _extract_groups_and_room(self, lines: list[str]) -> tuple[list[str], Optional[str]]:
        """Fix #21: Извлечь группы с поддержкой разных факультетов"""
        groups = []
        room = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Проверяем все паттерны групп
            is_group = False
            for pattern in GROUP_PATTERNS:
                if re.match(pattern, line, re.IGNORECASE):
                    groups.append(line)
                    is_group = True
                    break
            
            # Если не группа и содержит цифры — возможно аудитория
            if not is_group and any(c.isdigit() for c in line):
                if 'п.г' not in line.lower() and 'п/г' not in line.lower():
                    room = line
        
        return groups, room
