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
    end_status_date: Mapped[str] = mapped_column()
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
    
    
class PromoCode(Base):
    __tablename__ = 'promocodes'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    link: Mapped[str] = mapped_column()
    status_id: Mapped[int] = mapped_column()
    status_duration_in_days: Mapped[int] = mapped_column()
    number_of_uses: Mapped[int] = mapped_column()
    usage_count: Mapped[int] = mapped_column()


async def async_main():
    async with main_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)