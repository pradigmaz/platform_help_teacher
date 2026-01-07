"""
PDF Service - генерация PDF из лекций через Playwright.
Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
"""
import logging
import hashlib
from uuid import UUID
from typing import Optional, TYPE_CHECKING

# Условный импорт Playwright (может отсутствовать в dev)
try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    async_playwright = None
    Browser = None
    Page = None

from app.core.config import settings
from app.core.constants import (
    LECTURE_PDF_TIMEOUT_MS,
    LECTURE_PDF_RENDER_DELAY_MS,
)
from app.core.redis import get_redis

logger = logging.getLogger(__name__)

# Кэш PDF: TTL 1 час
PDF_CACHE_TTL = 3600


class PDFService:
    """Сервис генерации PDF из лекций."""
    
    def __init__(self):
        self._browser: Optional["Browser"] = None
    
    async def _get_browser(self) -> "Browser":
        """Lazy initialization браузера."""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError(
                "Playwright не установлен. PDF экспорт недоступен в dev режиме. "
                "Используйте production Docker образ."
            )
        
        if self._browser is None or not self._browser.is_connected():
            playwright = await async_playwright().start()
            self._browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                ]
            )
        return self._browser
    
    @staticmethod
    def _cache_key(lecture_id: UUID, updated_at_hash: str) -> str:
        """Генерирует ключ кэша для PDF."""
        return f"pdf:{lecture_id}:{updated_at_hash}"
    
    async def get_cached_pdf(self, lecture_id: UUID, updated_at_hash: str) -> Optional[bytes]:
        """Получить PDF из кэша."""
        try:
            redis = await get_redis()
            key = self._cache_key(lecture_id, updated_at_hash)
            cached = await redis.get(key)
            if cached:
                logger.info(f"PDF cache hit for lecture {lecture_id}")
                return cached.encode('latin-1')  # Redis decode_responses=True
        except Exception as e:
            logger.warning(f"Redis cache get failed: {e}")
        return None
    
    async def cache_pdf(self, lecture_id: UUID, updated_at_hash: str, pdf_bytes: bytes) -> None:
        """Сохранить PDF в кэш."""
        try:
            redis = await get_redis()
            key = self._cache_key(lecture_id, updated_at_hash)
            # Сохраняем как latin-1 строку (decode_responses=True)
            await redis.setex(key, PDF_CACHE_TTL, pdf_bytes.decode('latin-1'))
            logger.info(f"PDF cached for lecture {lecture_id}")
        except Exception as e:
            logger.warning(f"Redis cache set failed: {e}")
    
    async def generate_pdf(self, lecture_id: UUID, updated_at_hash: Optional[str] = None) -> bytes:
        """
        Генерирует PDF из лекции.
        
        Args:
            lecture_id: UUID лекции
            updated_at_hash: Хэш updated_at для кэширования
            
        Returns:
            bytes: PDF файл
        """
        # Проверяем кэш
        if updated_at_hash:
            cached = await self.get_cached_pdf(lecture_id, updated_at_hash)
            if cached:
                return cached
        
        browser = await self._get_browser()
        page: Page = await browser.new_page()
        
        try:
            # URL страницы рендера для PDF
            render_url = f"{settings.FRONTEND_URL}/lectures/render/{lecture_id}?mode=pdf"
            logger.info(f"Generating PDF for lecture {lecture_id}, URL: {render_url}")
            
            await page.goto(render_url, wait_until='networkidle')
            
            # Ждём загрузки всех визуализаций (маркер .visualization-ready)
            try:
                await page.wait_for_selector('.lecture-content', timeout=LECTURE_PDF_TIMEOUT_MS)
                # Даём время на рендер визуализаций
                await page.wait_for_timeout(LECTURE_PDF_RENDER_DELAY_MS)
            except Exception as e:
                logger.warning(f"Timeout waiting for visualizations: {e}")
            
            # Генерируем PDF
            pdf_bytes = await page.pdf(
                format='A4',
                print_background=True,
                margin={
                    'top': '1cm',
                    'bottom': '1cm',
                    'left': '1cm',
                    'right': '1cm'
                },
                scale=0.9,
            )
            
            logger.info(f"PDF generated successfully, size: {len(pdf_bytes)} bytes")
            
            # Кэшируем
            if updated_at_hash:
                await self.cache_pdf(lecture_id, updated_at_hash, pdf_bytes)
            
            return pdf_bytes
            
        finally:
            await page.close()
    
    async def close(self):
        """Закрывает браузер."""
        if self._browser and self._browser.is_connected():
            await self._browser.close()
            self._browser = None


# Singleton instance
pdf_service = PDFService()
