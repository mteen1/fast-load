from sqlmodel import Session, select
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker

from app import crud
from app.core.config import settings
from app.models import User, UserCreate

engine = create_async_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    echo=False,
    future=True,
    pool_pre_ping=True,  # Add connection health check
)

async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def init_db() -> None:
    async with async_session_maker() as session:
        # Tables should be created with Alembic migrations
        # But if you don't want to use migrations, create
        # the tables un-commenting the next lines
        # from sqlmodel import SQLModel
        # async with engine.begin() as conn:
        #     await conn.run_sync(SQLModel.metadata.create_all)

        statement = select(User).where(User.email == settings.FIRST_SUPERUSER)
        result = await session.execute(statement)
        user = result.scalar_one_or_none()
        
        if not user:
            user_in = UserCreate(
                email=settings.FIRST_SUPERUSER,
                password="password",
                is_superuser=True,
            )
            await crud.create_user(session=session, user_create=user_in)
