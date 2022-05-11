from pyrogram.errors import RPCError, FloodWait, RPCError, BadRequest, Forbidden
from pyrogram.raw.functions.channels import InviteToChannel, GetParticipants, GetParticipant
from pyrogram.raw.functions.messages import GetDialogs
from pyrogram.raw.types import InputPeerUser, InputPeerEmpty, InputPeerChannel, ChannelParticipantsRecent

from pyrogram.raw import functions, types
from pyrogram import Client

from aiogram.dispatcher import FSMContext
from aiogram import types

from datetime import datetime
import requests
import asyncio
import logging
import csv

from modul.file_handling import FlowData

class PyClass:
    def __init__(self, pathDir, proxy):
        self.flow = FlowData()
        self.pathDir = pathDir
        self.proxy = proxy
        self.logger = logging.getLogger('PyClassLog')
        self.logger.propagate = False
        handler = logging.FileHandler(self.pathDir + "/LogPyClass.log")
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter(fmt="%(levelname)s %(asctime)s - %(message)s"))
        self.logger.addHandler(handler)
    
    async def pars(self, message: types.Message, chat, limit=200, phone_sel: str = None):
        self.logger.info(f"Start func<pars>, chat={chat}, limit={limit}, phone_sel={phone_sel}")
        proxyList = []
        error = []
        if limit < 1: return []
        if limit > 10000: limit = 10000
        for proxy in self.proxy:
            if proxy["id"] != '0' and phone_sel is None or phone_sel == proxy["id"]:
                proxyList.append(proxy)
        if len(proxyList) == 0:
            self.logger.error(f"NO_PROXY")
            return ["NO_PROXY"]
        for i, proxy in enumerate(proxyList):
            count = 0
            if self._check_proxy(proxy) != 200:
                self.logger.error(f"ERROR_CONNECT_PROXY: phone={proxy['id']}, proxy={proxy['ip']}:{proxy['port']}")
                error.append([proxy['id'], "ERROR_CONNECT_PROXY", f"{proxy['ip']}:{proxy['port']}"])
                continue
            if message is not None:
                await message.edit_text(text=f"Телефон: {proxy['id']} [{i+1}/{len(proxyList)}]\nСпарсено пользователей: [{count}/{limit}]")
            usersList = []
            try:
                with open(self.pathDir + f"/phone_date/{proxy['id']}_mb.csv", "r", encoding='UTF-8') as file:
                    rows = csv.reader(file, delimiter=",", lineterminator="\n")
                    for row in rows:
                        usersList.append(row[1])
            except FileNotFoundError:
                with open(self.pathDir + f"/phone_date/{proxy['id']}_mb.csv", "w", encoding='UTF-8') as file:
                    pass
            except IndexError:
                pass
            conf = self.flow.conf_read(proxy["id"])
            phone = conf['phone']
            api_id = conf["id"]
            api_hash = conf["hash"]
            app = Client(
                self.pathDir+'/session/'+phone, api_id, api_hash, 
                proxy=dict(
                    hostname=proxy['ip'],
                    port=proxy['port'],
                    username=proxy['user'],
                    password=proxy['pass']
            ))
            if not await app.connect():
                self.logger.error(f"NOT_AUTHORIZED: phone={phone}, proxy={proxy['ip']}:{proxy['port']}")
                error.append([phone, "NOT_AUTHORIZED", f"{proxy['ip']}:{proxy['port']}"])
                await app.disconnect()
                await asyncio.sleep(10)
                continue
            chack = 0
            while True:
                chatsList = []
                result = await app.send( GetDialogs(
                    offset_date=0,
                    offset_id=0,
                    offset_peer=InputPeerEmpty(),
                    limit=200,
                    hash=0
                ))
                chats = {}
                chatsList.extend(result.chats)
                for cht in chatsList:
                    try:
                        if cht.username == chat:
                            cht.access_hash
                            chats = cht
                            self.logger.info(f"Chat find: phone: {phone}, chat: {chat}, data: {cht.id} {cht.username} {cht.title} {cht.id} {cht.access_hash}")
                            break
                    except:
                        continue
                else:
                    chack += 1
                    if chack == 2:
                        self.logger.error(f"No chat: phone={phone}, chat={chat}")
                        break
                    try:
                        await app.join_chat("@" + chat)
                    except BadRequest as e:
                        self.logger.error(f"BadRequest: phone={phone}, chat={chat}, message={e.ID}")
                        if e.ID == "USERNAME_INVALID":
                            error.append([phone, "USERNAME_INVALID", chat])
                            break
                    continue
                break
            while True:
                participants = []
                if count >= limit:
                    break
                try:
                    participants = await app.send(GetParticipants(
                        channel=InputPeerChannel(channel_id=chats.id, access_hash=chats.access_hash),
                        filter=ChannelParticipantsRecent(),
                        offset=count,
                        limit=limit,
                        hash=0
                    ))
                except FloodWait as e:
                    self.logger.warning(f"FloodWait: phone={phone}, sleep={e.x}, message={e.ID}")
                    if e.x > 600:
                        break
                    await asyncio.sleep(e.x)
                    continue
                except BadRequest as e:
                    self.logger.error(f"BadRequest: phone={phone}, message={e}")
                    break
                if len(participants.users) == 0:
                    self.logger.info(f"Stop func<pars>, count={count}, error={str(error)}")
                    break
                part = []
                for p in participants.users:
                    count += 1
                    if str(p.id) in usersList:
                        continue
                    if p.username:
                        username = p.username
                    else:
                        username= ""
                    if p.first_name:
                        first_name= p.first_name
                    else:
                        first_name= ""
                    if p.last_name:
                        last_name= p.last_name
                    else:
                        last_name= ""
                    name = (first_name + ' ' + last_name).strip()
                    u = {}
                    u['username'] = username
                    u['id'] = p.id
                    u["hash"] = p.access_hash
                    u['name'] = name
                    part.append(u)
                self.flow.users_write(part, chat, proxy["id"])
                if message is not None and len(participants.users):
                    await message.edit_text(text=f"Телефон: {proxy['id']}, [{i+1}/{len(proxyList)}]\nСпарсено пользователей: [{count}/{limit}]")
                await asyncio.sleep(10)
            await app.disconnect()
            await asyncio.sleep(10)
        self.logger.info(f"Stop func<pars>, count={count}, error={str(error)}")
        return error

    async def invite(self, message: types.Message, chat, step):
        self.logger.info(f"Start func<invite>, chat={chat}, step={step}")
        proxyList = []
        error = []
        start = step[0]
        limit = self.flow.config_limit()
        count, temp = 0, 0 # start
        try:
            account = self.flow.read_account()
        except ValueError:
            account = []
        for proxy in self.proxy:
            if proxy["id"] != '0':
                proxyList.append(proxy)
        if len(proxyList) == 0:
            self.logger.error(f"NO_PROXY")
            return ['NO_PROXY'], 0

        for proxy in proxyList:
            self.logger.info(f"Proxy_account: ID={proxy['id']}, IP={proxy['ip']}")
            if self._check_proxy(proxy) != 200:
                self.logger.error(f"ERROR_CONNECT_PROXY: phone={proxy['id']}, proxy={proxy['ip']}:{proxy['port']}")
                error.append([proxy['id'], "ERROR_CONNECT_PROXY", f"{proxy['ip']}:{proxy['port']}"])
                continue
            try:
                users = self.flow.user_read(proxy["id"])
            except IndexError:
                users = []
            except FileNotFoundError:
                users = []
            index = 0
            for i in range(0, len(account)):
                if account[i]["phone"] == proxy["id"]:
                    index = i
                    break
            else:
                self.logger.error(f"NO_PROXY_ACCOUNT: ID={proxy['id']}, account={str(account)}")
                error.append([proxy["id"], "NO_PROXY_ACCOUNT"])
                continue
            self.logger.info(f"Account: account[index]={account[index]}")
            conf = self.flow.conf_read(proxy["id"])
            phone = conf['phone']
            api_id = conf["id"]
            api_hash = conf["hash"]
            app = Client(
                self.pathDir+'/session/'+phone, api_id, api_hash, 
                proxy=dict(
                    hostname=proxy['ip'],
                    port=proxy['port'],
                    username=proxy['user'],
                    password=proxy['pass']
            ))
            if not await app.connect():
                self.logger.error(f"NOT_AUTHORIZED: phone={phone}, proxy={proxy['ip']}:{proxy['port']}")
                error.append([phone, "NOT_AUTHORIZED"])
                await app.disconnect()
                await asyncio.sleep(10)
                continue
            chatsList = []
            result = await app.send( GetDialogs(
                offset_date=0,
                offset_id=0,
                offset_peer=InputPeerEmpty(),
                limit=400,
                hash = 0
                
            ))
            chats = {}
            chatsList.extend(result.chats)
            for cht in chatsList:
                try:
                    if cht.username == chat:
                        cht.access_hash
                        chats = cht
                        self.logger.info(f"Chat find: phone: {phone}, chat: {chat}, data: {cht.id} {cht.username} {cht.title} {cht.id} {cht.access_hash}")
                        break
                except AttributeError:
                    continue
            else:
                self.logger.error(f"NO_CHAT: phone={phone}, chat={chat}")
                error.append([phone, "NO_CHAT", chat])
                await app.disconnect()
                await asyncio.sleep(10)
                continue
            target_group_entity = InputPeerChannel(channel_id=chats.id, access_hash=chats.access_hash)
            diff = datetime.today() - account[index]['invite_date']
            if diff.days >= 1 and diff.seconds > 180:
                account[index]['invite'] = 0
            if account[index]['invite'] == 0:
                account[index]['invite_date'] = datetime.today()
            for usr in range(start, len(users)):
                if count >= step[1]:
                    break
                if account[index]['invite'] >= int(limit['invite']):
                    start = usr
                    break
                try:
                    self.logger.info(f"user_id: phone_acc={account[index]['phone']}, count={count}, invite={account[index]['invite']} | user={users[usr]['telid']}:{users[usr]['name']}")
                    user_to_add = InputPeerUser(user_id=users[usr]['id'], access_hash=users[usr]['hash'])
                    try:
                        await app.send(
                            GetParticipant(channel=target_group_entity, participant=user_to_add))
                        self.logger.info(f"Пользователь есть в группе")
                        continue
                    except BadRequest as e:
                        if e.ID != "USER_NOT_PARTICIPANT":
                            raise BadRequest(e)
                    
                    if len(users[usr]['telid']) > 0:
                        invite = await app.add_chat_members(cht.username, users[usr]['telid'])
                    else:
                        invite =  await app.send( InviteToChannel(channel=target_group_entity, users=[user_to_add]) )
                    if invite:
                        account[index]['invite'] += 1
                        count += 1
                    self.logger.info(f"INVITE: phone={phone}, count={count}, limit={account[index]['invite']} ")
                except FloodWait as e:
                    self.logger.error(f"FloodWait: sleep={e.x}, e={e}")
                    if e.x > 500:
                        break
                    await asyncio.sleep(e.x)
                except Forbidden as e:
                    self.logger.error(f"Forbidden: {e.ID}, {e}")
                except TimeoutError as e:
                    self.logger.error(f"TimeoutError: {e.ID}, {e}")
                    break
                except BadRequest as e:
                    self.logger.error(f"BadRequest: {e}")
                    if e.ID == "USER_ID_INVALID":
                        self.logger.error(f"[USER_ID_INVALID]: count={count}, acc={account[index]}, users={users[usr]}")
                    elif e.ID == 'USERS_TOO_MUCH':
                        break
                    await asyncio.sleep(0.05)
                    continue
                except RPCError as e:
                    self.logger.error(f"RPCError: count={count}, acc={account[index]}, users={users[usr]}, {e}")
                    break
                if temp != count:
                    await message.edit_text("Инвайт: " + str(count))
                    temp = count
                if usr != len(users) - 1:
                    await asyncio.sleep(int(limit["invite_speed"]) + 15)
            await app.disconnect()
            self.flow.write_account(account)
            await asyncio.sleep(10)
        self.logger.info(f"Stop func<invite>, count={count}, error={str(error)}")
        return error, count

    def _check_proxy(self, proxy):
        url = "https://google.com"
        name = f"socks5h://{proxy['user']}:{proxy['pass']}@{proxy['ip']}:{proxy['port']}"
        proxy = {
            'http': name,
            'https': name
        }
        req = requests.Session()
        req.proxies = proxy
        try:
            result = req.get(url, timeout=20)
        except requests.exceptions.ConnectionError as e:
            return 0
        except requests.exceptions.ConnectTimeout as e:
            return 0
        except requests.exceptions.HTTPError as e:
            return 0
        except requests.exceptions.Timeout as e:
            return 0
        return result.status_code
