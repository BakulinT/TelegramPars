from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from aiogram.dispatcher import FSMContext
from aiogram import Dispatcher, types

import re

from modul.file_handling import FlowData
from modul.func import authorization

flow: FlowData

class ProxyClass(StatesGroup):
    waiting_for_proxy_select = State() # proxy_select
    waiting_for_proxy_fin = State() # proxy_add or proxy_select

async def proxy_info(message: types.Message):
    global flow
    flow = FlowData()
    if not authorization(message.from_user.id):
        await message.answer("Вы не авторизованы!")
        return
    await message.answer("Для отмены действия выполните команду /close")

    invite_kb = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton(text="Добавить прокси ✏", callback_data="btn_add"),
        InlineKeyboardButton(text="Вывести список прокси 📄", callback_data="btn_list"),
        InlineKeyboardButton(text="Назначить прокси аккаунтам (автоматичсеки)", callback_data="btn_appoint"),
        InlineKeyboardButton(text="Удалить 📄", callback_data="btn_dell")
    )
    await message.answer("Действие с прокси", reply_markup=invite_kb)
    await ProxyClass.waiting_for_proxy_select.set()

async def proxy_select(call: types.CallbackQuery, state: FSMContext):
    global flow
    try:
        proxy = flow.proxy_read()
    except IndexError:
        proxy = []
    invite_kb = None
    text = "Ничего не выбрано"
    lmbd = lambda x: "Свободен" if x == '0' else "Занят: " + x

    if call.data == "btn_add":
        text = "Введите прокси в виде «ip:port:user:password»:"
    elif call.data == "btn_dell":
        invite_kb = InlineKeyboardMarkup(row_width=1)
        text = "Выберите прокси для удаления"
        for i in range(0, len(proxy)):
            invite_kb.add(
                InlineKeyboardButton(text=f"[{lmbd(proxy[i]['id'])}] {proxy[i]['ip']}:{proxy[i]['port']}", callback_data="btnS_"+str(i))
            )
    elif call.data == "btn_list":
        text = "Список прокси"
        for p in proxy:
            text += f"\n[{lmbd(p['id'])}] {p['ip']}:{p['port']}"
    elif call.data == "btn_appoint":
        account = flow.read_account()
        proxyAcc = []
        appoint = 0
        start = 0
        for p in proxy:
            if p["id"] != '0':
                proxyAcc.append(p["id"])
        for acc in account:
            if acc["phone"] in proxyAcc:
                appoint += 1
                continue
            for i in range(start, len(proxy)):
                if proxy[i]["id"] == '0':
                    proxy[i]["id"] = acc["phone"]
                    start = i + 1
                    appoint += 1
                    break
            if start >= len(proxy):
                break
        flow.proxy_write(proxy)
        text = f"Назначение выполнено!\n> Всего аккаунтов: {len(account)} шт.\n> Для {appoint} аккаунтов есть прокси."
        if len(account) - appoint > 0:
            text += f"\nДля {len(account) - appoint} аккоунтов нет прокси"

    await call.message.answer(text, reply_markup=invite_kb)

    if len(proxy) == 0 and call.data != "btn_add":
        await call.message.answer("Нет прокси в списке!")
        await state.finish()
    elif call.data == "btn_list" or call.data == "btn_appoint":
        await state.finish()
    else:
        await state.update_data(proxy=proxy)
        await ProxyClass.next()

async def proxy_add(message: types.Message, state: FSMContext):
    global flow
    proxyData = await state.get_data()
    proxyData = proxyData["proxy"]
    proxy = re.sub(" ", "", message.text).split(':')
    print(proxy)
    if len(proxy) != 4:
        await message.answer("Не правильный ввод прокси, сверьтесь с шаблоном «ip:port:user:password» и повторите")
        return
    for i in range(0, len(proxyData)):
        if proxyData[i]['ip'] == proxy[0] and proxyData[i]['port'] == proxy[1]:
            proxyData.pop(i)
    try:
        proxyData.append({
                'id': "0",
                'ip': proxy[0], 
                'port': int(proxy[1]),
                'user': proxy[2],
                'pass': proxy[3]
            })
    except ValueError:
        await message.answer("Не правильный ввод прокси!")
        return
    flow.proxy_write(proxyData)
    await message.answer(f"Новый «{proxy[0]}:{proxy[1]}» прокси успешно добавлен!")
    await state.finish()

async def proxy_list(call: types.CallbackQuery, state: FSMContext):
    global flow
    btn = call.data.split('_')
    if btn[0] != "btnS":
        await call.message.answer("Не та команда!")
        return
    accounts = flow.read_account()
    proxyData = await state.get_data()
    proxyData = proxyData["proxy"]
    index = int(btn[1])
    proxyData.pop(index)
    flow.proxy_write(proxyData)

    await call.message.answer(f"Элемент «{proxyData[index]['ip']}:{proxyData[index]['port']}» успешно удален")

    await state.finish()