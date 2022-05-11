#!venv/bin/python

import asyncio
import logging
from os import path

from aiogram import Bot, Dispatcher, types
from aiogram.types import BotCommand
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.utils.executor import start_polling

from modul.func import *
from modul.pars import *
from modul.proxy import *
from modul.setup import *
from modul.invite import *
from modul.loging import *
from modul.config_reader import load_config

# @TelParsBot

pathDir = path.dirname(__file__)
logger = logging.getLogger(__name__)

async def close(message: types.Message, state: FSMContext):
    await message.answer("Действие отменено", reply_markup=types.ReplyKeyboardRemove())
    await state.finish()

def register_handlers_standart(dp: Dispatcher):
    dp.register_message_handler(help, commands="help")
    dp.register_message_handler(help, commands="start")
    # dp.register_message_handler(log_info, commands="log")

def register_handlers_invite(dp: Dispatcher):
    dp.register_message_handler(close, commands="close", state="*")
    dp.register_message_handler(invite_info, commands="invite", state="*")
    dp.register_callback_query_handler(invite_command, state=InviteClass.waiting_for_invite_command)
    dp.register_message_handler(invite_group, state=InviteClass.waiting_for_invite_group)
    dp.register_message_handler(invite_amount, state=InviteClass.waiting_for_invite_amount)

def register_handlers_setup(dp: Dispatcher):
    dp.register_message_handler(close, commands="close", state="*")
    dp.register_message_handler(setup_info, commands="account", state="*")
    dp.register_callback_query_handler(setup_session, state=SetupClass.waiting_for_setup_session)
    dp.register_message_handler(setup_phone, state=SetupClass.waiting_for_setup_phone)
    dp.register_callback_query_handler(setup_phone_query, state=SetupClass.waiting_for_setup_phone)
    dp.register_message_handler(setup_check_api_id, state=SetupClass.waiting_for_setup_check_api)
    dp.register_message_handler(setup_create_session, state=SetupClass.waiting_for_setup_create_session)
    dp.register_message_handler(setup_authorization, state=SetupClass.waiting_for_setup_authorization)

def register_handlers_pars(dp: Dispatcher):
    dp.register_message_handler(close, commands="close", state="*")
    dp.register_message_handler(pars_info, commands="pars", state="*")
    dp.register_callback_query_handler(pars_command, state=ParsClass.waiting_for_pars_command)
    dp.register_message_handler(pars_action, state=ParsClass.waiting_for_pars_action)
    dp.register_callback_query_handler(pars_action_button, state=ParsClass.waiting_for_pars_action)
    dp.register_message_handler(pars_limit, state=ParsClass.waiting_for_pars_limit)

def register_handlers_proxy(dp: Dispatcher):
    dp.register_message_handler(close, commands="close", state="*")
    dp.register_message_handler(proxy_info, commands="proxy", state="*")
    dp.register_callback_query_handler(proxy_select, state=ProxyClass.waiting_for_proxy_select)
    dp.register_message_handler(proxy_add, state=ProxyClass.waiting_for_proxy_fin)
    dp.register_callback_query_handler(proxy_list, state=ProxyClass.waiting_for_proxy_fin)

def register_handlers_log(dp: Dispatcher):
    dp.register_message_handler(close, commands="close", state="*")
    dp.register_message_handler(log_info, commands="log", state="*")
    dp.register_callback_query_handler(log_command_query, state=LogClass.waiting_for_log_command_query)
    dp.register_message_handler(
        log_load_doc, state=LogClass.waiting_for_log_load_doc,
        content_types=types.ContentType.DOCUMENT
    )

async def set_commands(airbot: Bot):
    commands = [
        BotCommand(command="/help", description="Помощь по командам"),
        BotCommand(command="/account", description="Работа с сессиями"),
        BotCommand(command="/proxy", description="Прокси"),
        BotCommand(command="/pars", description="Парсинг"),
        BotCommand(command="/invite", description="Инвайт"),
        BotCommand(command="/log", description="Логи")
    ]
    await airbot.set_my_commands(commands)

async def main():
    conf = load_config(pathDir)
    airbot = Bot(token=conf["token"])
    dp = Dispatcher(airbot, storage=MemoryStorage())

    register_handlers_invite(dp)
    register_handlers_standart(dp)
    register_handlers_pars(dp)
    register_handlers_setup(dp)
    register_handlers_proxy(dp)
    register_handlers_log(dp)
    await set_commands(airbot)
    
    Log_Format = "%(levelname)s %(asctime)s - %(message)s"
    # logging.basicConfig(
    #     filename = pathDir + "/logTelBot.log",
    #     filemode = "a",
    #     format = Log_Format, 
    #     level=logging.INFO) # DEBUG
    logging.basicConfig(level=logging.INFO)
    logging.error("Starting bot")

    await dp.start_polling()

if __name__ == '__main__':
    for path_name in ("/config", "/session", '/phone_date'):
        try:
            os.mkdir(pathDir + path_name)
        except FileExistsError:
            pass
    asyncio.run(main(), debug=True)
