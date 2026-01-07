"""
Абстракция для внешних API с retry и circuit breaker.
"""
import logging
import httpx
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class ExternalAPIError(Exception):
    """Ошибка внешнего API."""
    pass


class ExternalAPIClient:
    """Клиент для внешних API с retry логикой."""
    
    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client
    
    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True
    )
    async def get(self, path: str, params: Optional[dict] = None) -> str:
        """GET запрос с retry."""
        client = await self._get_client()
        url = f"{self.base_url}{path}"
        
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} for {url}")
            raise ExternalAPIError(f"HTTP {e.response.status_code}: {e.response.text[:200]}")
        except httpx.TimeoutException:
            logger.error(f"Timeout for {url}")
            raise ExternalAPIError(f"Timeout fetching {url}")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error for {url}: {e}")
            raise


# Клиент для kis.vgltu.ru
kis_client = ExternalAPIClient("https://kis.vgltu.ru", timeout=30.0)
