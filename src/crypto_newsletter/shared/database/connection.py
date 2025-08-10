"""Database connection and session management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Optional

from crypto_newsletter.shared.config.settings import get_settings
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool


class DatabaseManager:
    """Database connection manager."""

    def __init__(self) -> None:
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    def initialize(self, database_url: Optional[str] = None) -> None:
        """Initialize database engine and session factory."""
        settings = get_settings()
        url = database_url or settings.database_url

        # Convert postgresql:// to postgresql+asyncpg://
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)

        # Create async engine
        self._engine = create_async_engine(
            url,
            echo=settings.debug and not settings.testing,
            poolclass=NullPool if settings.testing else None,
            pool_pre_ping=True,
            pool_recycle=3600,  # 1 hour
        )

        # Create session factory
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    @property
    def engine(self) -> AsyncEngine:
        """Get database engine."""
        if self._engine is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get session factory."""
        if self._session_factory is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._session_factory

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session context manager."""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def close(self) -> None:
        """Close database connections."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get database manager singleton."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
        _db_manager.initialize()
    return _db_manager


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session context manager."""
    db_manager = get_db_manager()
    async with db_manager.get_session() as session:
        yield session


async def close_db_connections() -> None:
    """Close all database connections."""
    global _db_manager
    if _db_manager:
        await _db_manager.close()
        _db_manager = None


def reset_db_manager() -> None:
    """Reset database manager (useful for testing)."""
    global _db_manager
    _db_manager = None
