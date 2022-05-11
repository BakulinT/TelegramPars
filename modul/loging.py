import pstats
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from aiogram.utils.deprecated import warn_deprecated
from aiogram.dispatcher import FSMContext
from aiogram import Dispatcher, types

import asyncio
import re
import os

from modul.file_handling import FlowData
from modul.func import authorization

flow: FlowData
pathDir = os.path.split(os.path.split(__file__)[0])[0]

class LogClass(StatesGroup):
    waiting_for_log_command_query = State()
    waiting_for_log_load_doc = State()

async def log_info(message: types.Message):
	global flow
	flow = FlowData()
	if not authorization(message.from_user.id):
		await message.answer("Вы не авторизованы")
		return
    
	await message.answer("Для отмены действий выполните команду /close")
	invite_kb = InlineKeyboardMarkup(row_width=2).add(
		InlineKeyboardButton(text="Скачать логи бота", callback_data="btn_log_download"),
		InlineKeyboardButton(text="Вывести логи бота", callback_data="btn_log_print"),
		InlineKeyboardButton(text="Скачать БД", callback_data="btn_data_download")
	)
	await message.answer("Выберите действие", reply_markup=invite_kb)
	await LogClass.waiting_for_log_command_query.set()

async def log_command_query(call: types.CallbackQuery, state: FSMContext):
    if call.data == "btn_data_send":
        await call.message.answer("Отправьте файл")
        await LogClass.next()
        return
    elif call.data == "btn_data_download":
        await call.message.answer("Ваши файлы:")
        account = flow.read_account()
        for acc in account:
            try:
                await call.message.answer_document(
                    open(pathDir + f"/phone_date/{acc['phone']}_mb.csv", 'rb')
                )
            except FileNotFoundError:
                pass
    elif call.data == "btn_log_print":
        TelBot = os.popen('systemctl status bot.service').read()
        SessBot = os.popen('systemctl status sess.service').read()
        await call.message.answer("TelBot:\n" + TelBot)
        await call.message.answer("SessionBot:\n" + SessBot)
    elif call.data == "btn_log_download":
        await call.message.answer("Ваш файл")
        try:
            await call.message.answer_document(
                open(pathDir + "/logTelBot.log", 'rb'))
        except FileNotFoundError:
            pass
        try:
            await call.message.answer_document(
                open(pathDir + "/logSessionBot.log", 'rb'))
        except FileNotFoundError:
            pass
    await state.finish()

async def log_load_doc(message: types.Document, state: FSMContext):
    name = "None_mb.csv"
    try:
        csv = message.document.file_name.split('.')[1]
        if csv != 'csv': # 
            raise IndexError
    except IndexError:
        await message.answer('Отправьте файл с правильным расширением!')
        return

    os.replace(pathDir + '/' + name, pathDir + '/documents/Data_' + name)
    await message.document.download(pathDir + '/' + name)
    await message.answer('Файл получен')
    await state.finish()