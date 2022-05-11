#!venv/bin/python

import re
import asyncio
import logging
from os import path

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.executor import start_polling

from pyrogram.errors import RPCError, FloodWait, BadRequest, Forbidden, RPCError
from pyrogram import Client

from modul.file_handling import FlowData
from modul.func import authorization

# @SessionTelBot

account: list
flow: FlowData = FlowData()
pathDir = path.dirname(__file__)

logger = logging.getLogger(__name__)
token = "TOKEN"

airbot = Bot(token=token)
dp = Dispatcher(airbot, storage=MemoryStorage())

Log_Format = "%(levelname)s %(asctime)s - %(message)s"
logging.basicConfig(
    filename = pathDir + "/logSessionBot.log",
    filemode = "a",
    format = Log_Format, 
    level=logging.DEBUG)
logging.error("Starting bot")

def code_write(code):
    with open(pathDir+"/code.temp", 'w', encoding='UTF-8') as f:
        f.write(code)

def code_read():
    with open(pathDir+"/code.temp", 'r', encoding='UTF-8') as f:
        for line in f:
            return re.sub('\n', '', line)

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    text = """1. Введите команду /sess с параметром 'телефон:api_id:api_hash'.
\nНапример: /sess телефон:api_id:api_hash
"""
    await message.answer(text)
    text = """2. После введите код командой /code с параметрами кода. Не забудьте вставить символ '-' между цифрами кода. 
\nНапример: /code 12-345-6 или /code 1-23456
"""
    await message.answer(text)

@dp.message_handler(commands=['sess'])
async def session(message: types.Message):
    if not authorization(message.from_user.id):
        await message.answer("Вы не авторизованы!")
        return
    await message.answer("Запуск создания сессии")
    try:
        mess = message.text.split(' ')[1]
    except IndexError:
        await message.answer("Введите правильные данные")
        return
    conf = mess.split(':')
    if len(conf) != 3:
        await message.answer("Введите правильно данные от сессии")
        return
    await create_session(message, conf)

@dp.message_handler(commands=['code'])
async def send_welcome(message: types.Message):
    if not authorization(message.from_user.id):
        await message.answer("Вы не авторизованы!")
        return
    try:
        code = re.sub('-', '', message.text.split(" ")[1])
        print("code", code, code is None, len(code) != 5, not int(code))
        if code is None or len(code) != 5 or not int(code):
            await message.answer("Введите код 2!")
            return
        code_write(code)
        print("code2", code)
    except IndexError:
        await message.answer("Введите код!")
        return
    except Exception as e:
        print(e)
        await message.answer("Введите код!")
        return
    print('fin phone_code', code)

async def create_session(message: types.Message, conf):
    from datetime import datetime
    code_write("")
    try:
        phone = conf[0]
        api_id = int(conf[1])
        api_hash = conf[2]
    except ValueError:
        await message.answer("Ввведите правильные данные для api_id!")
        return
    try:
        account = flow.read_account()
    except ValueError:
        account = []
    try:
        proxy = flow.proxy_read()
    except IndexError:
        await message.answer("Добавьте прокси для продолжения!")
        return
    index = None
    for i in range(0, len(proxy)):
        if proxy[i]["id"] == '0':
            proxy[i]["id"] = phone
            index = i
            break
    else:
        await message.answer("Нет свободных прокси. Добавьте новые прокси для создания сессии Telegram!")
        return
    for i in range(0, len(account)):
        if account[i]['phone'] == phone:
            await message.answer(f"У вас уже создана сессия с номером {phone}! Перезапись...")
            account.pop(i)
    app = Client(
        pathDir+'/session/'+phone, api_id, api_hash, 
        proxy=dict(
            hostname=proxy[index]["ip"],
            port=proxy[index]["port"],
            username=proxy[index]["user"],
            password=proxy[index]["pass"]
	))
    if not await app.connect():
        code = ''
        sent_code_info = await app.send_code(phone)
        while True:
            code = code_read()
            if code is None or len(code) != 5:
                await asyncio.sleep(6)
                continue
            break
        phone_code_inp = code
        try:
            await app.sign_in(
                phone_number=phone, 
                phone_code_hash=sent_code_info.phone_code_hash, 
                phone_code=phone_code_inp)
        except FloodWait as e:
            await message.answer("Придется подождать " + str(e.x) + " секунд. Повторите позже")
            return
        except RPCError as e:
            await message.answer("Не удалось авторизироваться, " + e.ID)
            return
        await message.answer("Вы авторизирровались")
    else:
        await message.answer("Вы авторизированы")
    account.append({
        'id': api_id,
        'phone': phone, 
        'invite': '0',
        'invite_date': datetime.today()
    })
    flow.write_account(account)
    flow.proxy_write(proxy)
    flow.conf_write(api_id, api_hash, phone)
    await app.disconnect()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)