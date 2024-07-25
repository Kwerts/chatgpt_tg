from sqlalchemy import ForeignKey, BigInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine


main_engine = create_async_engine(url='sqlite+aiosqlite:///main_database.sqlite3')

async_session = async_sessionmaker(main_engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    status_id: Mapped[int] = mapped_column(ForeignKey('statuses.id'))
    requests_today: Mapped[int] = mapped_column()
    time_for_clear_requests: Mapped[str] = mapped_column()
    username: Mapped[str] = mapped_column()
    tg_id = mapped_column(BigInteger)


class Status(Base):
    __tablename__ = 'statuses'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    max_requests: Mapped[int] = mapped_column()
    max_context: Mapped[int] = mapped_column()
    is_default: Mapped[bool] = mapped_column()
    admin_status: Mapped[bool] = mapped_column()


class Context(Base):
    __tablename__ = 'contexts'

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column()
    role: Mapped[str] = mapped_column()
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))


async def async_main():
    async with main_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)