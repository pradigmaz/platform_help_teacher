"""
HTML санитизация для защиты от XSS.
Используется для очистки контента из Tiptap/Lexical редакторов.
"""
import logging
import bleach
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Разрешённые HTML теги для редактора лекций
ALLOWED_TAGS = [
    # Структура
    'p', 'br', 'hr', 'div', 'span',
    # Заголовки
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    # Форматирование
    'strong', 'b', 'em', 'i', 'u', 's', 'strike', 'del',
    'sub', 'sup', 'mark', 'code', 'pre',
    # Списки
    'ul', 'ol', 'li',
    # Таблицы
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    # Цитаты
    'blockquote', 'q',
    # Ссылки и медиа
    'a', 'img',
    # Lexical специфичные
    'figure', 'figcaption',
]

# Разрешённые атрибуты
ALLOWED_ATTRIBUTES = {
    '*': ['class', 'id', 'style', 'data-*'],
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'title', 'width', 'height', 'loading'],
    'td': ['colspan', 'rowspan'],
    'th': ['colspan', 'rowspan', 'scope'],
    'ol': ['start', 'type'],
    'li': ['value'],
}

# Разрешённые CSS свойства
ALLOWED_STYLES = [
    'color', 'background-color', 'background',
    'font-size', 'font-weight', 'font-style', 'font-family',
    'text-align', 'text-decoration', 'text-indent',
    'margin', 'margin-top', 'margin-bottom', 'margin-left', 'margin-right',
    'padding', 'padding-top', 'padding-bottom', 'padding-left', 'padding-right',
    'border', 'border-radius',
    'width', 'height', 'max-width', 'max-height',
    'display', 'vertical-align',
]

# Разрешённые протоколы для ссылок
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto', 'tel']


def sanitize_html(html: str) -> str:
    """
    Очищает HTML от потенциально опасного контента.
    
    Удаляет:
    - <script>, <iframe>, <object>, <embed>
    - onclick, onerror и другие event handlers
    - javascript: протоколы
    - data: URLs (кроме изображений)
    
    Args:
        html: Сырой HTML из редактора
    
    Returns:
        Очищенный HTML
    """
    if not html:
        return html
    
    try:
        cleaned = bleach.clean(
            html,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            protocols=ALLOWED_PROTOCOLS,
            strip=True,  # Удалять запрещённые теги, а не экранировать
            strip_comments=True,
        )
        return cleaned
    except Exception as e:
        logger.error(f"HTML sanitization failed: {e}")
        # В случае ошибки — экранируем всё
        return bleach.clean(html, tags=[], strip=True)


def sanitize_lexical_content(content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Рекурсивно санитизирует Lexical JSON контент.
    
    Lexical хранит контент как JSON с вложенными nodes.
    Нужно найти все text nodes и HTML nodes и очистить их.
    
    Args:
        content: Lexical JSON структура
    
    Returns:
        Очищенный контент
    """
    if not isinstance(content, dict):
        return content
    
    result = {}
    
    for key, value in content.items():
        if key == 'text' and isinstance(value, str):
            # Текстовые ноды — экранируем HTML entities
            result[key] = bleach.clean(value, tags=[], strip=True)
        elif key == 'html' and isinstance(value, str):
            # HTML ноды — полная санитизация
            result[key] = sanitize_html(value)
        elif key == 'url' and isinstance(value, str):
            # URL — проверяем протокол
            result[key] = _sanitize_url(value)
        elif isinstance(value, dict):
            result[key] = sanitize_lexical_content(value)
        elif isinstance(value, list):
            result[key] = [
                sanitize_lexical_content(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value
    
    return result


def _sanitize_url(url: str) -> str:
    """Проверяет и очищает URL."""
    if not url:
        return url
    
    url_lower = url.lower().strip()
    
    # Блокируем опасные протоколы
    dangerous_protocols = ['javascript:', 'vbscript:', 'data:text']
    for proto in dangerous_protocols:
        if url_lower.startswith(proto):
            logger.warning(f"Blocked dangerous URL: {url[:50]}")
            return '#blocked'
    
    return url


def strip_all_html(text: str) -> str:
    """Полностью удаляет весь HTML, оставляя только текст."""
    if not text:
        return text
    return bleach.clean(text, tags=[], strip=True)
