#!venv/bin/python
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

import asyncio

def authorization(userId):
    users = ()
    if userId in users:
        return True
    else:
        return False

async def dellUsers(message: types.Message):
    import invite
    await message.answer("Start invite...")
    invite.start()
    await message.answer("Завершение.")

async def help(message: types.Message):
    text = f"""Бот регистрации @SessionTelBot новой сессии.
Список команд:
/help - Помощь по командам
/account - Работа с сессиями
/proxy - Прокси
/pars - Парсинг
/invite - Инвайт
/log - Бэкап, логи
    """
    await message.answer(text)