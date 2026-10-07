import os
from pathlib import Path

from sqlalchemy import String


def _load_env_file() -> None:
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.is_file():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


_load_env_file()
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

DB_USER = os.getenv("POSTGRES_USER", "swapi_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "swapi_pass")
DB_NAME = os.getenv("POSTGRES_DB", "swapi")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

DB_DSN = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_async_engine(DB_DSN, connect_args={"ssl": False})
DbSession = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase, AsyncAttrs):
    pass


class SwapiPeople(Base):
    __tablename__ = "people"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    birth_year: Mapped[str] = mapped_column(String)
    eye_color: Mapped[str] = mapped_column(String)
    films: Mapped[str] = mapped_column(String)
    gender: Mapped[str] = mapped_column(String)
    hair_color: Mapped[str] = mapped_column(String)
    height: Mapped[str] = mapped_column(String)
    homeworld: Mapped[str] = mapped_column(String)
    mass: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    skin_color: Mapped[str] = mapped_column(String)
    starships: Mapped[str] = mapped_column(String)
    vehicles: Mapped[str] = mapped_column(String)


async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    await engine.dispose()
