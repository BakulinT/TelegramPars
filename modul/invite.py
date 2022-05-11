from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from aiogram.dispatcher import FSMContext
from aiogram import Dispatcher, types

from os import path
import re

from modul.TelModul.PyClass import PyClass
from modul.file_handling import FlowData
from modul.func import authorization

flow: FlowData

class InviteClass(StatesGroup):
	waiting_for_invite_command = State()
	waiting_for_invite_group = State()
	waiting_for_invite_amount = State()

async def invite_info(message: types.Message):
	global flow
	flow = FlowData()
	if not authorization(message.from_user.id):
		await message.answer("Вы не авторизованы")
		return
	await message.answer("Для отмены действий выполните команду /close")
	invite_kb = InlineKeyboardMarkup(row_width=1).add(
		InlineKeyboardButton(text="Введите имя группы для инвайта", callback_data="btn_inv")
	)
	await message.answer("Делать инвайт можно только в свои группы, где аккаунт является администратором.\n\nВыберите способ инвайта:", reply_markup=invite_kb)
	await InviteClass.waiting_for_invite_command.set()

async def invite_command(call: types.CallbackQuery, state: FSMContext):
	text = "Выберите что-нибудь!"
	if call.data == 'btn_inv':
		text = "Выполнить инвайт по id группы (@_название_группы):"
		await call.message.answer(text)
	else:
		await call.message.answer("Выберите правильный вариант!")
		return	
	await state.update_data(callback_query=call.data)
	await InviteClass.next()

async def invite_group(message: types.Message, state: FSMContext):
	data = await state.get_data()
	name = re.sub('@', '', message.text)

	await message.answer("Введите лимит инвайта (пример: 100)" +
		"или начало инвайта и кол-во пользователей (пример: 0 100):")
	await state.update_data(invite_name=name)
	await InviteClass.next()

async def invite_amount(message: types.Message, state: FSMContext):
	data = await state.get_data()
	chat = data["invite_name"]
	try:
		proxy = flow.proxy_read()
	except IndexError:
		await message.answer("Нет прокси!")
		await state.finish()
		return
	if len(proxy) == 0:
		await message.answer("Нет прокси!")
		await state.finish()
		return
	py = PyClass(path.split(path.split(__file__)[0])[0], proxy)
	try:
		lim = [int(m) for m in message.text.split(' ')]
	except ValueError:
		await message.answer("Ошибка ввода, повторите действие!")
		return
	if len(lim) == 1:
		lim = [0, lim[0]]
	invMess = await message.answer("Инвайт: 0")
	error, count = await py.invite(invMess, chat, lim)
	try:
		pass
	except Exception as e:
		await message.answer("Возникла ошибка!")
		await message.answer('[Err]' + str(e))
		print('[Err Invite]', e)
		await state.finish()
		return
	await message.answer("Место остановки инвайта: " + str(count))
	if len(error) == 1 and error[0] == "NO_PROXY":
		await message.answer("Нет назначенных прокси!")
	for err in error:
		if err[1] == "NO_PROXY_ACCOUNT":
			await message.answer(f"Для аккаунта +{err[0]} нет прокси!")
		elif err[1] == "ERROR_CONNECT_PROXY":
			await message.answer(f"Ошибка подключения прокси {err[2]} для аккаунта +{err[0]}")
		elif err[1] == "NOT_AUTHORIZED":
			await message.answer(f"Аккаунт +{err[0]} не авторизирован!")
		elif err[1] == "NO_CHAT_":
			await message.answer(f"Для аккаунта +{err[0]} нет доступа к чату {err[2]}!")
	await state.finish()