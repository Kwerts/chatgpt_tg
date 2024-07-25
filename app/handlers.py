from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
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


load_dotenv()

bot = Bot(token=os.getenv('BOT_TOKEN'))
router = Router()


class Answering(StatesGroup):
    answering = State()
    
    
class GiveStatus(StatesGroup):
    tg_id = State()
    

@router.message(CommandStart())
async def start(message: Message):
    default_status = await requests.get_default_status()
    await requests.set_user(tg_id=message.from_user.id,
                            username=f'@{message.from_user.username}')
    await message.answer(text=f'Привет, я бесплатный AI бот.\nAI, которые я использую: ' \
                              f'ChatGPT-4o mini (У вас есть к нему ' \
                              f'{default_status.max_requests} запросов в день).'
                              f'\n\n📊 <b>Нужно больше запросов? '
                              f'Подключите Premium-подписку за 199 руб./мес.</b>',
                         reply_markup=await keyboards.start_keyboard(tg_id=message.from_user.id),
                         parse_mode='HTML')


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
                            reply_markup=await keyboards.all_statuses_keyboard())
        await state.update_data(tg_id=message.text)
    else:
        await message.answer('Пользователь с таким Telegram ID не найден в базе данных.')
        await state.clear()
    
    
@router.callback_query(F.data.startswith('status_'))
async def give_status_status(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    status_id = callback.data.split('_')[1]
    data = await state.get_data()
    
    await requests.set_status(tg_id=data.get("tg_id"), status_id=status_id)
    
    status = await requests.get_status(status_id=status_id)
    await callback.message.answer(f'Статус успешно выдан.\nTG_ID: {data.get("tg_id")}\n' \
                                  f'Статус: {status.name}')
    
    await state.clear()
    
    
@router.callback_query(F.data == 'pay_requests_menu')
async def pay_requests_menu(callback: CallbackQuery):
    await callback.answer()
    
    default_status = await requests.get_default_status()
    text = ( 
        f'Каждый день бесплатно доступно {default_status.max_requests} запросов в день к '
        f'ChatGPT-4o mini.\n\n<b>📈 Нужно больше запросов? Подключите Premium-подписку за '
        f'199 руб./мес.</b>\n\n<b>Преимущества Premium-подписки:</b>\n'
        f'◻100 запросов к ChatGPT-4o mini ежедневно\n\n<b>Нужно ещё больше запросов к '
        f'ChatGPT-4o mini?</b>\n'
        f'◻150 запросов в день за 299 руб./мес.\n◻200 запросов в день за 399 руб./мес.'
        f'\n◻300 запросов в день за 499 руб./мес.\n\n<b>За покупкой обращайтесь сюда 👉 @zmxuce</b>'
    )
    await callback.message.answer(text=text, parse_mode='HTML')


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
        print(len(encoding.encode(f'User: {message.text}')))
        print(len(encoding.encode(f'OPENAI: {response}')))
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
    
    user_contexts = await requests.get_user_contexts(tg_id=message.from_user.id)

    user_status_id = await requests.get_user_status(tg_id=message.from_user.id)

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