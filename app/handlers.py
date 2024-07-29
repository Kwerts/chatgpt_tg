from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest
from dotenv import load_dotenv

import app.generator as generator
import database.requests as requests
import app.keyboards as keyboards

import re
import os
import tiktoken
import string
import secrets


load_dotenv()

bot = Bot(token=os.getenv('BOT_TOKEN'))
router = Router()

bot_link = 'https://t.me/Test_2110_bot'


class Answering(StatesGroup):
    answering = State()
    
    
class GiveStatus(StatesGroup):
    tg_id = State()
    
    
class CreatePromoCode(StatesGroup):
    number_of_uses = State()
    name = State()
    

@router.message(CommandStart())
async def start(message: Message):
    start_parameter = message.text.partition(' ')[2]
    
    await requests.set_user(tg_id=message.from_user.id,
                            username=f'@{message.from_user.username}')
    
    if not start_parameter:
        await info_menu(message=message)
    else:
        link = f'{bot_link}?start={start_parameter}'
        promo_code = await requests.get_promo_code(link=link)
        if promo_code:
            if promo_code.usage_count < promo_code.number_of_uses:
                await requests.set_status(tg_id=message.from_user.id, status_id=promo_code.status_id)
                await requests.plus_usage_to_promo_code(link=link)
                
                status = await requests.get_status(status_id=promo_code.status_id)
                
                text = (
                    f'Вы получили подписку {status.name} на x дней.\n\n<b>✨Ваши преимущества:</b>'
                    f'\n\n{status.max_requests} запросов к ChatGPT-4o mini в день'
                )
                await message.answer(text=text, parse_mode='HTML')  # Доработать
            else:
                await message.answer(text='У этого промокода закончились использования.')
        else:
            await info_menu(message=message)
        
    
@router.message(Command('info'))
async def command_info(message: Message):
    await info_menu(message=message)
    
    
async def info_menu(message: Message):
    user_status_id = (await requests.get_user(tg_id=message.from_user.id)).status_id
    user_status = await requests.get_status(status_id=user_status_id)
    
    await message.answer(text=f'Привет, я бесплатный AI бот.\nAI, которые я использую: ' \
                              f'ChatGPT-4o mini (У вас есть к нему ' \
                              f'{user_status.max_requests} запросов в день).'
                              f'\n\n📊 <b>Нужно больше запросов? '
                              f'Подключите Premium-подписку за 199 руб./мес.</b>',
                         reply_markup=await keyboards.start_keyboard(tg_id=message.from_user.id),
                         parse_mode='HTML')
    
    
@router.callback_query(F.data == 'subscription_info')
async def pay_requests_menu_callback(callback: CallbackQuery):
    await pay_requests_menu(callback=callback)
    

# Тут "premium" используется вместо "subscription".
@router.message(Command('premium'))
async def pay_requests_menu_command(message: Message):
    await pay_requests_menu(message=message)
    
    
async def pay_requests_menu(callback: CallbackQuery | None = None, message: Message | None = None):
    if callback:
        await callback.answer()
    
    default_status = await requests.get_default_status()
    text = ( 
        f'Каждый день бесплатно доступно {default_status.max_requests} запросов в день к '
        f'ChatGPT-4o mini.\n\n<b>📈 Нужно больше запросов? Подключите Premium-подписку за '
        f'199 руб./мес.</b>\n\n<b>Преимущества Premium-подписки:</b>\n'
        f'◻100 запросов к ChatGPT-4o mini ежедневно\n\n<b>Нужно ещё больше запросов к '
        f'ChatGPT-4o mini?</b>\n'
        f'◻150 запросов в день за 299 руб./мес.\n◻200 запросов в день за 399 руб./мес.\n\n'
        f'<b>За покупкой обращайтесь сюда 👉 @zmxuce</b>'
    )
    if callback:
        await callback.message.answer(text=text, parse_mode='HTML')
    elif message:
        await message.answer(text=text, parse_mode='HTML')


@router.callback_query(F.data == 'admin_menu')
async def admin_menu(callback: CallbackQuery):
    await callback.answer()
    
    await callback.message.answer(text='Админ-меню.',
                                  reply_markup=await keyboards.admin_menu_keyboard())
    
    
@router.callback_query(F.data == 'give_status')
async def give_status_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    await callback.message.answer(text='Введите Telegram ID пользователя, ' \
                                       'которому вы хотите выдать статус.')
    await state.set_state(GiveStatus.tg_id)


@router.message(GiveStatus.tg_id)
async def give_status_tg_id(message: Message, state: FSMContext):
    user = await requests.get_user(tg_id=message.text)
    if user:
        await message.answer(text='Выберите статус для выдачи из списка.',
                            reply_markup=await keyboards.give_status_all_statuses_keyboard())
        await state.update_data(tg_id=message.text)
    else:
        await message.answer('Пользователь с таким Telegram ID не найден в базе данных.')
        await state.clear()
    
    
@router.callback_query(F.data.startswith('give_status_status_'))
async def give_status_status(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    status_id = callback.data.split('_')[1]
    data = await state.get_data()
    
    await requests.set_status(tg_id=data.get("tg_id"), status_id=status_id)
    
    status = await requests.get_status(status_id=status_id)
    await callback.message.answer(f'Статус успешно выдан.\nTG_ID: {data.get("tg_id")}\n' \
                                  f'Статус: {status.name}')
    
    await state.clear()
    
    
@router.callback_query(F.data == 'create_promo_code')
async def create_promo_code_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    await callback.message.answer(text='Введите количество использований для промокода:')
    await state.set_state(CreatePromoCode.number_of_uses)
    
    
@router.message(CreatePromoCode.number_of_uses)
async def create_promo_code_number_of_uses(message: Message, state: FSMContext):
    if message.text.isdigit():
        await message.answer(text=('Выберите статус, который будет выдаваться при использовании '
                                   'промокода.'),
                             reply_markup= \
                                 await keyboards.create_promo_code_all_statuses_keyboard())
        await state.update_data(number_of_uses=message.text)
    else:
        await message.answer('Введите числовое значение.')
        await state.set_state(CreatePromoCode.number_of_uses)
        
        
@router.callback_query(F.data.startswith('create_promo_code_status_'))
async def create_promo_code_status(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    await state.update_data(status_id=callback.data.split('_')[4])
    
    text = (
        f'Введите название для промокода или сгенерируйте случайное.\nНапример, если вы введёте '
        f'"example", то ссылка будет выглядеть так: "{bot_link}?start=example"'
    )
    await callback.message.answer(text=text,
                                  reply_markup= (await \
                                      keyboards.create_promo_code_random_generate_keyboard()))
    
    await state.set_state(CreatePromoCode.name)
    
    
@router.message(CreatePromoCode.name)
async def create_promo_code_name(message: Message, state: FSMContext):
    data = await state.get_data()
    
    status = await requests.get_status(status_id=data.get("status_id"))
    
    link = f'{bot_link}?start={message.text}'
    
    await requests.create_promo_code(link=link, number_of_uses=data.get("number_of_uses"), 
                                     status_id=data.get("status_id"))
    
    text = (
        f'Вы создали новый промокод по ссылке {link}.\n\n'
        f'Его можно активировать {data.get("number_of_uses")} раз и он даёт статус {status.name}.'
    )
    await message.answer(text=text)
    
    await state.clear()
    
    
@router.callback_query(F.data == 'create_promo_code_random_generate')
async def create_promo_code_random_generate(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    data = await state.get_data()
    
    status = await requests.get_status(status_id=data.get("status_id"))
    
    alphabet = string.ascii_letters + string.digits
    name = ''
    for _ in range(12):
        name += secrets.choice(alphabet)
    
    link = f'{bot_link}?start={name}'
    
    await requests.create_promo_code(link=link, number_of_uses=data.get("number_of_uses"), 
                                     status_id=data.get("status_id"))
        
    text = (
        f'Вы создали новый промокод по ссылке {bot_link}?start={name}.\n\n'
        f'Его можно активировать {data.get("number_of_uses")} раз и он даёт статус {status.name}.'
    )
    await callback.message.answer(text=text)
    
    await state.clear()
        
    
@router.message()
async def any_message(message: Message, state: FSMContext):
    user = await requests.get_user(tg_id=message.from_user.id)

    user_status = await requests.get_status(status_id=user.status_id)
    if (await state.get_state() != Answering.answering \
        and user.requests_today < user_status.max_requests):
        message_from_bot = await message.answer('Пожалуйста, подождите. AI обрабатывает ваш ' \
                                                'запрос...')
        
        encoding = tiktoken.encoding_for_model("gpt-4o-mini")
        await state.set_state(Answering.answering)

        response = await chatgpt_request(message=message)
        try:
            await bot.edit_message_text(text=response, chat_id=message.chat.id,
                                        message_id=message_from_bot.message_id,
                                        parse_mode='Markdown')
        except TelegramBadRequest as exception:
            if str(exception) == 'Telegram server says - Bad Request: MESSAGE_TOO_LONG':
                try:
                    await bot.edit_message_text(text='Сообщение для ответа слишком большое ' \
                                                     '(более, чем 4096 символов).',
                                                chat_id=message.chat.id,
                                                message_id=message_from_bot.message_id)
                except TelegramBadRequest:
                    await message.answer(text='Сообщение для ответа слишком большое' \
                                              ' (более, чем 4096 символов).')
            else:
                await message.answer(text=response, parse_mode='Markdown')

        await requests.plus_request_to_user(tg_id=message.from_user.id)

        await state.clear()
    elif user.requests_today >= user_status.max_requests:
        user = await requests.get_user(message.from_user.id)
        user_date_for_clear_requests = user.time_for_clear_requests
        
        date_for_clear_requests = user_date_for_clear_requests.split(' ')[0]
        month_for_clear_requests = date_for_clear_requests.split('-')[1]
        day_for_clear_requests = date_for_clear_requests.split('-')[2]
        time_for_clear_requests = user_date_for_clear_requests.split(' ')[1]
        hours_for_clear_requests = time_for_clear_requests.split(':')[0]
        minutes_for_clear_requests = time_for_clear_requests.split(':')[1]
        
        await message.answer(f'Запросы на сегодня кончились. Они обновятся ' \
                             f'{day_for_clear_requests}.{month_for_clear_requests} в ' \
                             f'{hours_for_clear_requests}:{minutes_for_clear_requests} по ' \
                             f'Московскому времени.',
                             reply_markup=await keyboards.pay_requests_keyboard())


async def chatgpt_request(message: Message):
    await requests.set_context(tg_id=message.from_user.id, role='user', content=message.text)

    response = await generator.chatgpt_request(request=message.text, tg_id=message.from_user.id)
    await requests.set_context(tg_id=message.from_user.id, role='assistant', content=response)

    response = re.sub(pattern=r'### (.+)', repl=r'*\1*', string=response)
    
    user_contexts = await requests.get_user_not_system_contexts(tg_id=message.from_user.id)

    user_status_id = (await requests.get_user(tg_id=message.from_user.id)).status_id

    user_status = await requests.get_status(status_id=user_status_id)

    if len(user_contexts) > user_status.max_context:
        contexts_to_delete_count = (len(user_contexts) - user_status.max_context)
        contexts_to_delete = []
        for index, context_to_delete in enumerate(user_contexts):
            if index >= contexts_to_delete_count:
                break
            contexts_to_delete.append(context_to_delete)
        await requests.remove_contexts(contexts=contexts_to_delete)
    return response
