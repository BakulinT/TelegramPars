from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from aiogram.dispatcher import FSMContext
from aiogram import Dispatcher, types

from os import path
import asyncio
import re

from modul.TelModul.PyClass import PyClass
from modul.file_handling import FlowData
from modul.func import authorization

constExit = False
flow: FlowData

class ParsClass(StatesGroup):
    waiting_for_pars_command = State() # pars_command
    waiting_for_pars_action = State() # pars_action_pars, pars_action_button
    waiting_for_pars_limit = State() # pars_limit

async def pars_info(message: types.Message):
    global flow
    flow = FlowData()
    if not authorization(message.from_user.id):
        await message.answer("Вас нет в списках " + str(message.from_user.id))
        return

    await message.answer("Для отмены действия выполните команду /close")
    invite_kb = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton(text="Парс всех аккаунтов", callback_data="btn_pars_all"),
        InlineKeyboardButton(text="Парс для опредленного номера", callback_data="btn_pars_phone"),
        InlineKeyboardButton(text="Добавить имя группы в список 💾", callback_data="btn_write_save"),
        InlineKeyboardButton(text="Вывести список групп 📄", callback_data="btn_print"),
        InlineKeyboardButton(text="Удалить из списка группу ❌📄", callback_data="btn_dell"),
        InlineKeyboardButton(text="Круглосуточный парсинг 🕓", callback_data="btn_regl")
    )
    await message.answer("Выберите способ инвайта:", reply_markup=invite_kb)
    await ParsClass.waiting_for_pars_command.set()

async def pars_command(call: types.CallbackQuery, state: FSMContext):
    global flow
    group = flow.group_read()
    accounts = flow.read_account()
    pars_kb = None
    selt = call.data
    text = ""
    if selt == "btn_pars_all" or selt == "btn_write_save":
        text = "Введите имя группы (@_название_группы):"
    elif selt == "btn_print":
        text = "Список групп:"
        for i in range(0, len(group)):
            text += f'\n[{i}] @' + group[i]
        await call.message.answer(text)
        await state.finish()
        return
    elif selt == "btn_pars_phone":
        pars_kb = pars_kb = InlineKeyboardMarkup(row_width=2)
        text = "Телефон для парса:"
        for acc in accounts:
            pars_kb.add(InlineKeyboardButton( text='+' + acc['phone'], callback_data="btn_" + acc['phone'] ))
    elif selt == "btn_dell":
        pars_kb = pars_kb = InlineKeyboardMarkup(row_width=2)
        text = "Выберите группу для удаления из списка:"
        for gr in range(0, len(group)):
            pars_kb.add(InlineKeyboardButton( text='@'+group[gr], callback_data="btn_"+str(gr) ))
    elif selt == "btn_regl":
        text = "Выберите действие:"
        pars_kb = InlineKeyboardMarkup(row_width=2).add(
            InlineKeyboardButton(text="Запустить 🚀", callback_data="start"),
            InlineKeyboardButton(text="Остановить ⛔", callback_data="stop")
        )
    await call.message.answer(text, reply_markup=pars_kb)
    await state.update_data(select=selt, group=group)
    await ParsClass.next()

async def pars_action(message: types.Message, state: FSMContext):
    global flow
    selt = await state.get_data()
    name = re.sub('@', '', message.text)
    await state.update_data(name=name)
    
    if selt["select"] == "btn_write_save":
        if len(name) > 0:
            flow.group_write(group=[name])
            await message.answer(f"@{name} добавлен в список")
        else:
            await message.answer(f"Введите корректное название группы!")
            return
        await state.finish()
    elif selt["select"] == "btn_pars_all":
        await message.answer("Введите лимит на парсинг пользователей")
        await ParsClass.next()

async def pars_action_button(call: types.CallbackQuery, state: FSMContext):
    selt = await state.get_data()

    if selt['select'] == "btn_pars_phone":
        try:
            phone = call.data.split("_")[1]
            if len(phone) < 7:
                raise IndexError
        except IndexError:
            await call.message.answer("Выберите правильный вариант ил повторите попытку еще раз!")
            return
        await call.message.answer("Введите имя группы и лимит парсинга через пробел (@имя_группы 100)")
        await state.update_data(phone_pars=phone)
        await ParsClass.next()
        return
    if selt['select'] == "btn_regl":
        if call.data == "start":
            await state.finish()
            await call.message.answer("Запуск круглосуточного: " + str(constExit))
            status = await pars_while_start(call)
            if status:
                await call.message.answer("Круглосуточноый парсинг уже запущен!")
            elif status == "None proxy":
                await call.message.answer("Нет свободных прокси!")
            return
        elif call.data == "stop":
            await call.message.answer("Остановка круглосуточного прасинга: " + str(constExit))
            await pars_while_stop()
    elif selt['select'] == "btn_dell":
        global flow
        try:
            index = int(call.data[4:])
            group = selt['group']
            name = group[index]
            group.pop(index)
            flow.group_write(group=group, mod="w")
            await call.message.answer(f"Группа @{name} удалена из списка!")
        except ValueError:
            await call.message.answer("Ошибка! Выберите из списка!")
            return
        except IndexError:
            await call.message.answer("Нет данной группы в списке, повторите попытку заново!")
    await state.finish()

async def pars_limit(message: types.Message, state: FSMContext):
    global flow
    data = await state.get_data()
    phone = data.get("phone_pars", None)
    mess_data = message.text.split(" ")
    print(mess_data)
    try:
        if len(mess_data) == 2:
            name = re.sub('@', '', mess_data[0])
            limit = int(mess_data[1])
        else:
            name = data["name"]
            if message.text == "":
                raise ValueError
            limit = int(message.text)
    except ValueError:
        await message.answer("Введите правильный лимит!")
        return
    except KeyError as e:
        print(e.args[0] == 'name')
        if e.args[0] == 'name':
            await message.answer("Введите правильные данные!")
            return
        raise KeyError(e)
    proxy = flow.proxy_read()
    if len(proxy) == 0:
        await message.answer("Нет прокси!")
        await state.finish()
        return
    
    await message.answer(
        f"Начало парсинга ({limit} польз.). Если большое кол-во пользователей, то может занять много времени...", "")
    parsMess = await message.answer(f"Телефон: load, [0/load]\nСпарсено пользователей: [0/{limit}]")
    py = PyClass(path.split(path.split(__file__)[0])[0], proxy)
    error = await py.pars(parsMess, name, limit, phone_sel=phone)
    try:
        pass
    except Exception as e:
        await message.answer("Возникла ошибка!")
        # logger.error('[Err]', e)
        print('[Err Pars]', e, type(e))
        await message.answer('[Err]' + str(e))
        await state.finish()
        return
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
    await message.answer("Парсинг завершен")
    await state.finish()

async def pars_while_start(call: types.CallbackQuery):
    from datetime import datetime, time

    global flow
    global constExit
    gvtime = time(00, 30)
    gvmin = gvtime.hour * 60 + gvtime.minute
    if constExit:
        return True
    constExit = True
    proxy = flow.proxy_read()
    if len(proxy) == '0':
        return "None proxy"
    py = PyClass(path.split(path.split(__file__)[0])[0], proxy)
    while constExit:
        totime = datetime.today().time()
        tomin = totime.hour * 60 + totime.minute
        print("Проверка", totime)
        if abs(tomin - gvmin) > 31:
            await asyncio.sleep(1800)
            continue
        # await call.message.answer("Запускаю круглосуточный парсинг указанных групп...")
        print("Pars")
        group = flow.group_read()
        if len(group) == 0:
            await call.message.answer("[Предупреждение] У вас нет групп в списке.")
        for chat in group:
            try:
                await py.pars(None, chat, 200)
            except Exception as e:
                await call.message.answer(f"Возникла ошибка при парсе группы {chat}!")
                await call.message.answer(f"Круглосуточный парсинг остановлен!")
                # logger.error('[Err]', e)
                print('[Err]', e)
                await call.message.answer('[Err]' + str(e))
                constExit = False
                break
            """
            if check == "CHAT_ADMIN_REQUIRED":
                await call.message.answer("Метод требует прав администратора чата")
            elif check == "None proxy":
                await call.message.answer("Нет назначенных прокси!")
            elif check == "Add group":
                await call.message.answer(f"Добавте группу {chat} в аккаунте!")
            else:
                await call.message.answer(f"Парсинг для групп прошел успешно. Всего спарсено {check} поль.")
            if len(error) > 0:
                text = "[Предупреждение] Для следующих сессий нет авторизации:"
                for err in error:
                    text += "\n> " + err
                await call.message.answer(text)
            """
            await asyncio.sleep(60)

async def pars_while_stop():
    global constExit
    constExit = False