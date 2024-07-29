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
                                      callback_data='subscription_info'))
    
    return keyboard.adjust(1).as_markup()


async def pay_requests_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    
    keyboard.add(InlineKeyboardButton(text='📊 Нужно больше запросов?',
                                      callback_data='subscription_info'))
    
    return keyboard.adjust(1).as_markup()


async def admin_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    
    keyboard.add(InlineKeyboardButton(text='Выдать статус', callback_data='give_status'),
                 InlineKeyboardButton(text='Создать промокод', callback_data='create_promo_code'))
    return keyboard.adjust(1).as_markup()


async def give_status_all_statuses_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    
    for status in await requests.get_all_statuses():
        keyboard.add(InlineKeyboardButton(text=status.name,
                                          callback_data=f'give_status_status_{status.id}'))
    return keyboard.adjust(2).as_markup()


async def create_promo_code_all_statuses_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    
    for status in await requests.get_all_statuses():
        keyboard.add(InlineKeyboardButton(text=status.name,
                                          callback_data=f'create_promo_code_status_{status.id}'))
    return keyboard.adjust(2).as_markup()


async def create_promo_code_random_generate_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    
    keyboard.add(InlineKeyboardButton(text='Сгенерировать случайную ссылку',
                                      callback_data='create_promo_code_random_generate'))
    
    return keyboard.adjust(1).as_markup()
