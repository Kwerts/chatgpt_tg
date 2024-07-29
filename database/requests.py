from sqlalchemy import select
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database.models import async_session
from database.models import User, Status, Context, PromoCode


time_for_clear_requests_in_min = 1440


async def main() -> None:
    async with async_session() as session:
        users_for_clear_requests = (await session.scalars(select(User).where
                                                         (User.time_for_clear_requests 
                                                          <= datetime.now())))
        for user_for_clear_requests in users_for_clear_requests.all():
            await clear_user_requests(tg_id=user_for_clear_requests.tg_id)
        
        users = await session.scalars(select(User))
        for user in users.all():
            await clear_user_requests_scheduler(tg_id=user.tg_id)


async def set_user(tg_id: int, username: str) -> None:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        default_status_id = (await get_default_status()).id
        
        time_for_clear_requests = (datetime.now() 
                                   + timedelta(minutes=time_for_clear_requests_in_min))

        if not user:
            session.add(User(requests_today=0, username=username, tg_id=tg_id,
                             time_for_clear_requests=time_for_clear_requests,
                             status_id=default_status_id, end_status_date='r'))
            await session.commit()
            await clear_user_requests_scheduler(tg_id=tg_id)
            
            
async def clear_user_requests_scheduler(tg_id: int) -> None:
    scheduler = AsyncIOScheduler()
    
    scheduler.add_job(clear_user_requests, 'interval', minutes=time_for_clear_requests_in_min,
                      kwargs={"tg_id": tg_id})
    scheduler.start()
            
            
async def clear_user_requests(tg_id: int) -> None:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        user.requests_today = 0
        time_for_clear_requests = (datetime.now() 
                                   + timedelta(minutes=time_for_clear_requests_in_min))
        user.time_for_clear_requests = time_for_clear_requests
        await session.commit()


async def get_user(tg_id: int) -> User:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        return user
    

async def plus_request_to_user(tg_id: int) -> None:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        user.requests_today += 1
        await session.commit()


async def get_user_not_system_contexts(tg_id: int) -> None:
    async with async_session() as session:
        user_id = (await session.scalar(select(User).where(User.tg_id == tg_id))).id
        not_system_contexts = await session.scalars(select(Context).where(
            Context.user_id == user_id, Context.role != 'system'))
        return not_system_contexts.all()


async def set_context(tg_id: int, role: str, content: str) -> None:
    async with async_session() as session:
        user_id = (await session.scalar(select(User).where(User.tg_id == tg_id))).id
        session.add(Context(content=content, role=role, user_id=user_id))
        await session.commit()


async def remove_contexts(contexts: Context) -> None:
    async with async_session() as session:
        for context in contexts:
            await session.delete(context)
        await session.commit()
        
        
async def get_status(status_id: int) -> Status:
    async with async_session() as session:
        status = await session.scalar(select(Status).where(Status.id == status_id))
        return status
    
    
async def get_all_statuses() -> list[Status]:
    async with async_session() as session:
        statuses = await session.scalars(select(Status))
        return statuses.all()


async def get_default_status() -> Status:
    async with async_session() as session:
        default_status = await session.scalar(select(Status).where(Status.is_default == True))
        return default_status
    
    
async def get_admin_statuses() -> list[Status]:
    async with async_session() as session:
        admin_statuses = await session.scalars(select(Status).where(Status.admin_status == True))
        return admin_statuses.all()
    
    
async def set_status(tg_id: int, status_id: int, status_duration_in_days: int = 30) -> None:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        user.status_id = status_id
        user.end_status_date = datetime.now() + timedelta(days=status_duration_in_days)
        await session.commit()
        
        
async def clear_status_scheduler(tg_id: int, end_status_date: str) -> None:
    scheduler = AsyncIOScheduler()
    
    scheduler.add_job(clear_user_requests, 'interval', minutes=time_for_clear_requests_in_min,
                      kwargs={"tg_id": tg_id})
    scheduler.start()  # ДОРАБОТАТЬ ТУТ
    
        
        
async def create_promo_code(link: str, number_of_uses: int, status_id: int) -> None:
    async with async_session() as session:
        session.add(PromoCode(link=link, status_id=status_id, number_of_uses=number_of_uses,
                              usage_count=0, status_duration_in_days=30))
        await session.commit()
        
        
async def get_promo_code(link: str) -> PromoCode | None:
    async with async_session() as session:
        promo_code = await session.scalar(select(PromoCode).where(PromoCode.link == link))
        return promo_code
    
    
async def plus_usage_to_promo_code(link: str) -> None:
    async with async_session() as session:
        promo_code = await session.scalar(select(PromoCode).where(PromoCode.link == link))
        promo_code.usage_count += 1
        await session.commit()