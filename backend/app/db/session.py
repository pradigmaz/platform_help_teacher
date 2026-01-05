from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings

# Оптимизированный движок
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    # poolclass=QueuePool,  <-- УДАЛЕНО: SQLAlchemy сама выберет AsyncAdaptedQueuePool
    pool_size=20,           # Максимум 20 соединений
    max_overflow=10,        # +10 временных при пике
    pool_timeout=30,        # Ждать соединения 30 сек
    pool_pre_ping=True,     # Проверять соединение перед использованием
)

# Фабрика сессий
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# Dependency для FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()