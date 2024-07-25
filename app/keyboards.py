from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database.requests as requests


async def start_keyboard(tg_id: int) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    
    user = await requests.get_user(tg_id=tg_id)
    for admin_status in await requests.get_admin_statuses():
        if user.status_id == admin_status.id:
            keyboard.add(InlineKeyboardButton(text='🎫Админ-меню', callback_data='admin_menu'))
            break
    
    keyboard.add(InlineKeyboardButton(text='📊 Нужно больше запросов?',
                                      callback_data='pay_requests_menu'))
    
    return keyboard.adjust(1).as_markup()


async def pay_requests_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    
    keyboard.add(InlineKeyboardButton(text='📊 Нужно больше запросов?',
                                      callback_data='pay_requests_menu'))
    
    return keyboard.adjust(1).as_markup()


async def admin_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    
    keyboard.add(InlineKeyboardButton(text='Выдать статус', callback_data='give_status'))
    return keyboard.adjust(1).as_markup()


async def all_statuses_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    
    for status in await requests.get_all_statuses():
        keyboard.add(InlineKeyboardButton(text=status.name, callback_data=f'status_{status.id}'))
    return keyboard.adjust(2).as_markup()
