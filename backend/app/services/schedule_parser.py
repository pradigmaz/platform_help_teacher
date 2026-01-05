"""
Парсер расписания с kis.vgltu.ru
"""
import logging
import re
import httpx
from datetime import date, timedelta
from typing import Optional
from dataclasses import dataclass
from bs4 import BeautifulSoup
import html

logger = logging.getLogger(__name__)

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

# Маппинг типов занятий
LESSON_TYPE_MAP = {
    "лек": "lecture",
    "лек.": "lecture",
    "лаб": "lab",
    "лаб.": "lab",
    "пр": "practice",
    "пр.": "practice",
}


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


class ScheduleParser:
    """Парсер расписания ВГЛТУ"""
    
    BASE_URL = "https://kis.vgltu.ru/schedule"
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        await self.client.aclose()
    
    async def fetch_schedule(self, teacher_name: str, target_date: date) -> str:
        """Получить HTML расписания на дату"""
        url = f"{self.BASE_URL}?teacher={teacher_name}&date={target_date.isoformat()}"
        logger.info(f"Fetching schedule: {url}")
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Error fetching schedule: {e}")
            # Для тестирования: если не можем получить с API, пытаемся использовать локальный файл
            try:
                with open('/app/real_schedule.html', 'r', encoding='utf-8') as f:
                    logger.info("Using local schedule file for testing")
                    return f.read()
            except:
                return ""
    
    def parse_html(self, html_content: str) -> list[ParsedLesson]:
        """Парсинг HTML расписания"""
        soup = BeautifulSoup(html_content, 'html.parser')
        lessons = []
        
        # Ищем контейнер с расписанием
        table_div = soup.find('div', class_='table')
        if not table_div:
            logger.warning("Table div not found")
            return lessons
        
        # Ищем все блоки дней (прямые потомки div с margin-bottom: 25px)
        day_blocks = []
        for child in table_div.children:
            if hasattr(child, 'name') and child.name == 'div':
                style = child.get('style', '')
                if 'margin-bottom: 25px' in style:
                    day_blocks.append(child)
        
        logger.info(f"Found {len(day_blocks)} day blocks")
        
        for day_block in day_blocks:
            # Парсим дату
            date_elem = day_block.find('strong')
            if not date_elem:
                continue
            
            date_text = html.unescape(date_elem.get_text(strip=True))
            lesson_date = self._parse_date(date_text)
            if not lesson_date:
                continue
            
            # Ищем таблицу с парами
            table = day_block.find('table')
            if not table:
                continue
            
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) < 2:
                    continue
                
                # Первая ячейка - время
                time_text = cells[0].get_text(strip=True)
                
                # Вторая ячейка - информация о паре
                # Парсим по <br/> тегам
                info_cell = cells[1]
                info_lines = []
                for content in info_cell.children:
                    if isinstance(content, str):
                        text = html.unescape(content.strip())
                        if text:
                            info_lines.append(text)
                    elif hasattr(content, 'name'):
                        if content.name == 'br':
                            continue
                        elif content.name == 'a':
                            # Это ссылка на аудиторию
                            text = html.unescape(content.get_text(strip=True))
                            if text:
                                info_lines.append(text)
                        else:
                            text = html.unescape(content.get_text(strip=True))
                            if text:
                                info_lines.append(text)
                
                # Парсим пару
                parsed = self._parse_lesson_row(time_text, info_lines, lesson_date)
                if parsed:
                    lessons.append(parsed)
        
        return lessons
    
    def _parse_date(self, date_text: str) -> Optional[date]:
        """Парсинг даты вида '01 сентября 2025'"""
        months = {
            'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
            'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
            'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
        }
        
        match = re.match(r'(\d{1,2})\s+(\w+)\s+(\d{4})', date_text)
        if not match:
            return None
        
        day = int(match.group(1))
        month_name = match.group(2).lower()
        year = int(match.group(3))
        
        month = months.get(month_name)
        if not month:
            return None
        
        try:
            return date(year, month, day)
        except ValueError:
            return None
    
    def _parse_lesson_row(self, time_text: str, info_lines: list[str], lesson_date: date) -> Optional[ParsedLesson]:
        """Парсинг строки таблицы с информацией о паре"""
        
        # Получаем номер пары по времени
        lesson_number = TIME_TO_LESSON_NUMBER.get(time_text, 0)
        if not lesson_number:
            return None
        
        # Фильтруем пустые строки
        lines = [line.strip() for line in info_lines if line.strip()]
        if not lines:
            return None
        
        logger.debug(f"Parsing lesson: {lines}")
        
        # Первая строка - тип и предмет
        first_line = lines[0]
        
        # Ищем тип занятия
        lesson_type = None
        subject = first_line
        
        for key, value in LESSON_TYPE_MAP.items():
            if first_line.lower().startswith(key):
                lesson_type = value
                # Извлекаем предмет (после типа)
                # Удаляем тип и точку/пробел после него
                subject = first_line[len(key):].lstrip('. ')
                break
        
        if not lesson_type:
            lesson_type = "lecture"  # По умолчанию
        
        # Ищем подгруппу во всех строках
        subgroup = None
        for i, line in enumerate(lines):
            if "1 п.г." in line or "1 п.г" in line:
                subgroup = 1
                # Удаляем подгруппу из строки
                lines[i] = re.sub(r'1\s*п\.?г\.?', '', line).strip()
                break
            elif "2 п.г." in line or "2 п.г" in line:
                subgroup = 2
                lines[i] = re.sub(r'2\s*п\.?г\.?', '', line).strip()
                break
        
        # Ищем группы и аудиторию в остальных строках
        groups = []
        room = None
        
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            # Группы начинаются с ИС
            if line.startswith('ИС'):
                groups.append(line)
            # Аудитория - это строка с буквами и цифрами (но не группа и не подгруппа)
            elif not line.startswith('ИС') and any(c.isdigit() for c in line) and 'п.г' not in line.lower():
                room = line
        
        if not groups:
            logger.debug(f"No groups found in lines: {lines}")
            return None
        
        logger.debug(f"Parsed: subject={subject}, type={lesson_type}, groups={groups}, subgroup={subgroup}, room={room}")
        
        return ParsedLesson(
            date=lesson_date,
            lesson_number=lesson_number,
            lesson_type=lesson_type,
            subject=subject,
            groups=groups,
            subgroup=subgroup,
            room=room
        )
    
    async def parse_range(
        self, 
        teacher_name: str, 
        start_date: date, 
        end_date: date,
        progress_callback=None
    ) -> list[ParsedLesson]:
        """Парсинг расписания за период"""
        all_lessons = []
        current_date = start_date
        total_days = (end_date - start_date).days + 1
        processed = 0
        
        # API возвращает расписание на 2 недели от указанной даты
        # Поэтому делаем запросы с шагом 14 дней
        while current_date <= end_date:
            try:
                html_content = await self.fetch_schedule(teacher_name, current_date)
                
                # Если получили пустой результат, пропускаем
                if not html_content or not html_content.strip():
                    logger.warning(f"Empty response for {current_date}")
                    processed += 14
                    if progress_callback:
                        progress = min(100, int(processed / total_days * 100))
                        await progress_callback(progress)
                    current_date += timedelta(days=14)
                    continue
                
                lessons = self.parse_html(html_content)
                
                # Фильтруем только нужный диапазон
                for lesson in lessons:
                    if start_date <= lesson.date <= end_date:
                        all_lessons.append(lesson)
                
                processed += 14
                if progress_callback:
                    progress = min(100, int(processed / total_days * 100))
                    await progress_callback(progress)
                    
            except Exception as e:
                logger.error(f"Error fetching schedule for {current_date}: {e}")
            
            current_date += timedelta(days=14)
        
        # Убираем дубликаты
        seen = set()
        unique_lessons = []
        for lesson in all_lessons:
            key = (lesson.date, lesson.lesson_number, tuple(lesson.groups), lesson.subgroup)
            if key not in seen:
                seen.add(key)
                unique_lessons.append(lesson)
        
        logger.info(f"Parsed {len(unique_lessons)} unique lessons")
        return unique_lessons


# Singleton instance
_parser: Optional[ScheduleParser] = None

async def get_parser() -> ScheduleParser:
    global _parser
    if _parser is None:
        _parser = ScheduleParser()
    return _parser
