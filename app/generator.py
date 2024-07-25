from openai import AsyncOpenAI
from dotenv import load_dotenv

from database.requests import get_user_contexts

import os
import httpx


load_dotenv()

client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'),
                     http_client=httpx.AsyncClient(proxies=os.getenv('PROXY'),
                                                   transport=httpx.HTTPTransport(
                                                       local_address='0.0.0.0')))


async def chatgpt_request(request: str, tg_id: int) -> str:
    messages_list = []

    
    for context in await get_user_contexts(tg_id=tg_id):
        messages_list.append({"role": context.role, "content": context.content})
    
    messages_list.append({"role": "system", "content": "Your reply messages must contain a maximum of 4000 characters."})
    messages_list.append({"role": 'user', "content": request})

    chat_completion = await client.chat.completions.create(
        messages = messages_list,
        model="gpt-4o-mini", # gpt-4o-mini gpt-3.5-turbo
    )
    return chat_completion.choices[0].message.content
