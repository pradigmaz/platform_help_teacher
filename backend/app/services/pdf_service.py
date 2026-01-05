"""
PDF Service - генерация PDF из лекций через Playwright.
Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
"""
import logging
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

logger = logging.getLogger(__name__)


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
    
    async def generate_pdf(self, lecture_id: UUID) -> bytes:
        """
        Генерирует PDF из лекции.
        
        Args:
            lecture_id: UUID лекции
            
        Returns:
            bytes: PDF файл
        """
        browser = await self._get_browser()
        page: Page = await browser.new_page()
        
        try:
            # URL страницы рендера для PDF
            render_url = f"{settings.FRONTEND_URL}/lectures/render/{lecture_id}?mode=pdf"
            logger.info(f"Generating PDF for lecture {lecture_id}, URL: {render_url}")
            
            await page.goto(render_url, wait_until='networkidle')
            
            # Ждём загрузки всех визуализаций (маркер .visualization-ready)
            try:
                await page.wait_for_selector('.lecture-content', timeout=10000)
                # Даём время на рендер визуализаций
                await page.wait_for_timeout(2000)
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
