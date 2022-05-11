from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from aiogram.dispatcher import FSMContext
from aiogram import Dispatcher, types

from pyrogram.errors import RPCError, FloodWait, RPCError, BadRequest

from modul.TelModul.PyClass import PyClass
from modul.file_handling import FlowData
from modul.func import authorization

import re

flow: FlowData

class SetupClass(StatesGroup):
    waiting_for_setup_session = State() # setup_session
    waiting_for_setup_phone = State() # setup_phone, setup_phone_query (finish)
    waiting_for_setup_check_api = State() # setup_check_api_id
    waiting_for_setup_create_session = State() # setup_create_session
    waiting_for_setup_authorization = State() # setup_authorization

async def setup_info(message: types.Message):
	global flow
	flow = FlowData()
	if not authorization(message.from_user.id):
		await message.answer("Вы не авторизованы!")
		return

	await message.answer("Для отмены действия выполните команду /close")

	invite_kb = InlineKeyboardMarkup(row_width=1).add(
        # InlineKeyboardButton(text="Добавить аккаунт ✏", callback_data="btn_add"),
        InlineKeyboardButton(text="Список сессий", callback_data="btn_list"),
        InlineKeyboardButton(text="Удалить сессию ", callback_data="btn_del")
    )
	await message.answer("Выберите аккаунт для совершения действий:", reply_markup=invite_kb)
	await SetupClass.waiting_for_setup_session.set()

async def setup_session(call: types.CallbackQuery, state: FSMContext):
	invite_kb = None
	try:
		account = flow.read_account()
	except ValueError:
		account = []
	if call.data == "btn_add":
		text = "Введите номер телефона от аккаунта (71234567890):"
	elif call.data == "btn_del":
		text = "Сессии на удаление:"
		invite_kb = InlineKeyboardMarkup(row_width=1)
		for acc in account:
			invite_kb.add(
				InlineKeyboardButton(text='+'+acc['phone'], callback_data="btn_sel_"+acc['phone'])
			)
	elif call.data == "btn_list":
		text = "Список сессий (телефон, прокси, инвайт):"
		proxy = flow.proxy_read()
		for acc in account:
			for p in proxy:
				if p['id'] == acc['phone']:
					text += f"\n+{acc['phone']}, {p['ip']}:{p['port']}, {acc['invite']}"
					break
			else:
				text = f"\n+{acc['phone']}, {acc['invite']}"
	await call.message.answer(text, reply_markup=invite_kb)
	if call.data == "btn_list":
		await state.finish()
		return
	await state.update_data(account=account, call=call.data)
	await SetupClass.next()

async def setup_phone(message: types.Message, state: FSMContext):
	data = await state.get_data('account')
	phone = re.sub(r'\+', '', message.text)

	if len(phone) != 11:
		await message.answer(f"Номер {phone} некорректный, повторите!")
		return

	for acc in data["account"]:
		if acc['phone'] == phone:
			await message.answer(f"[Предупреждение] У вас уже создана сессия с номером {phone}! Если продолжите, то она перезапишется")
			break
	await message.answer("Введите api_id:")

	await state.update_data(phone=phone)
	await SetupClass.next()

async def setup_phone_query(call: types.CallbackQuery, state: FSMContext):
	import os
	data = await state.get_data()
	if data["call"] != "btn_del":
		await call.message.answer("Выберите правильную команду или завершите выполнение!")
		return
	phone = ""
	account = data['account']
	for i in  range(0, len(account)):
		if account[i]['phone'] == call.data.split("_")[2]:
			phone = account[i]['phone']
			account.pop(i)
			break
	try:
		flow.write_account(account) # ListAccount
		proxy = flow.proxy_read()
		for i in range(0, len(proxy)):
			if proxy[i]['id'] == phone:
				proxy[i]['id'] = '0'
				break
		flow.proxy_write(proxy)
		os.remove(os.path.split(os.path.split(__file__)[0])[0] + f"/session/{phone}.session")
		os.remove(os.path.split(os.path.split(__file__)[0])[0] + f"/config/{phone}_config.data")
		await call.message.answer(f"Удаление сессии {phone} успешно завершено!")
	except Exception as e:
		await call.message.answer(f"Не удалось удалить сессию {phone}! Err: " + e)
	await state.finish()

async def setup_check_api_id(message: types.Message, state: FSMContext):
	try:
		api_id = int(message.text)
		if api_id < 1:
			raise ValueError
	except ValueError:
		await message.answer("Api_id должен состоять из цифр и быть больше нуля!")
		return

	await state.update_data(api_id=api_id)
	await message.answer("Введите api_hash:")
	await SetupClass.next()

async def setup_create_session(message: types.Message, state: FSMContext):
	from os import path

	pathDir = path.split(path.split(__file__)[0])[0]
	data = await state.get_data()

	phone = data["phone"]
	api_id = data["api_id"]
	api_hash = message.text

	if len(api_hash) < 1:
		await message.answer("Не правильный api_hash, введите еще раз!")
		return
	# await state.update_data(api_hash=api_hash)

	proxy = flow.proxy_read() # /info/ProxyList.txt

	if len(api_hash) < 1:
		await message.answer("Api_hash должен больше нуля!")
		return
	index = None
	for i in range(0, len(proxy)):
		if proxy[i]["id"] == '0':
			proxy[i]["id"] = phone
			index = i
			break
	else:
		await message.answer("Нет свободных прокси. Добавьте новые прокси для создания сессии Telegram!")
		await state.finish()
		return
	await message.answer("Идет подключение...")

	py = PyClass(pathDir, proxy)
	try:
		send_code_info = await py.create_session(phone, api_id, api_hash, index)
	except FloodWait as e:
		await message.answer("Придется подождать " + str(e.x) + " секунд. Повторите позже")
		await state.finish()
		return
	except RPCError as e:
		await message.answer("Не удалось авторизироваться, " + e.ID)
		await state.finish()
		return
	if send_code_info is None:
		await message.answer("Вы авторизированы!")
		await state.finish()
	else:
		await state.update_data(py=py, api_hash=api_hash, send_code_info=send_code_info, proxy=proxy)
		await SetupClass.next()

async def setup_authorization(message: types.Message, state: FSMContext):
	print("setup_authorization")
	data = await state.get_data()

	phone_code = re.sub('-', '', message.text)

	if len(phone_code) != 5:
		await message.answer("Введите правильный код!")
		print('phone_code', phone_code)
		return
	print("!phone_code!", phone_code)

	# pathDir = path.split(path.split(__file__)[0])[0]

	py = data["py"]
	count = data.get('count', 0)
	proxy = data["proxy"]
	phone = data["phone"]
	api_id = data["api_id"]
	api_hash = data["api_hash"]
	send_code_info = data["send_code_info"]

	try:
		await py.create_session_code(phone, phone_code, send_code_info)
		flow.proxy_write(proxy)
		flow.conf_write(api_id, api_hash, phone)
		await message.answer("Вы успешно добавили аккаунт!")
	except BadRequest as e:
		if e.ID == "PHONE_CODE_INVALID" and count < 3:
			await message.answer("Введите код еще раз:")
			await state.update_data(count=count+1)
			return
		await message.answer("Попробуйте заново " + e.ID)
	except FloodWait as e:
		await message.answer("Придется подождать " + str(e.x) + " секунд. Повторите позже")
	except RPCError as e:
		await message.answer("Не удалось авторизироваться, " + e.ID)

	await state.finish()