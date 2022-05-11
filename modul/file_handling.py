from datetime import datetime
import configparser
from os import path
import csv, re

class FlowData:
	def __init__(self):
		self.pathDir = path.split(path.split(__file__)[0])[0]

	def config_limit(self, path=r"/info/limit.conf"):
		config = configparser.ConfigParser()
		config.read(self.pathDir + path)
		return config["Limit"]

	def proxy_read(self, path=r"/info/ProxyList.txt"):
		proxy = []
		with open(self.pathDir + path, 'r', encoding='UTF-8') as f:
			for line in f:
				l = re.sub('\n', '', line).split(':')
				proxy.append({
					'id': l[0],
					'ip': l[1],
					'port': int(l[2]),
					'user': l[3],
					'pass': l[4]
				})
		return proxy

	def proxy_write(self, proxy=[], path=r"/info/ProxyList.txt"):
		with open(self.pathDir + path, 'w', encoding='UTF-8') as f:
			for p in proxy:
				f.write(":".join([
					p['id'],
					p['ip'],
					str(p['port']),
					p['user'],
					p['pass']
				]) + "\n")

	def user_read(self, phone, path=r"/phone_date/"):
		users = []
		with open(self.pathDir + path + f"{phone}_mb.csv", "r", encoding='UTF-8') as f:
			rows = csv.reader(f, delimiter=",", lineterminator="\n")
			for row in rows:
				user = {}
				user['username'] = row[0]
				user['id'] = int(row[1])
				user['hash'] = int(row[2])
				user['name'] = row[3]
				user['chat'] = row[len(row) - 1]
				users.append(user)
		return users

	def user_read_id(self, phone, path=r"/phone_date/"):
		users = []
		with open(self.pathDir + path + f"{phone}_mb.csv", "r", encoding='UTF-8') as f:
			rows = csv.reader(f, delimiter=",", lineterminator="\n")
			for row in rows:
				users.append( int(row[1]) )
		return users
	
	def user_read(self, phone, path=r"/phone_date/"):
		users = []
		with open(self.pathDir + path + f"{phone}_mb.csv", "r", encoding='UTF-8') as f:
			rows = csv.reader(f, delimiter=",", lineterminator="\n")
			for row in rows:
				u = {}
				u['telid'] = row[0]
				u["id"] = int(row[1])
				u["hash"] = int(row[2])
				u["name"] = row[3]
				users.append(u)
		return users
	
	def users_write(self, part, chat, phone, path=r"/phone_date/"):
		with open(self.pathDir + path + f"{phone}_mb.csv", "a", encoding='UTF-8') as f:
			writer = csv.writer(f, delimiter=",", lineterminator="\n")
			for user in part:
				writer.writerow([
					re.sub('"', '', user['username']), user['id'], user['hash'], re.sub('"', '', user['name']), chat
				])
	
	def group_read(self, path=r"/info/Group.txt"):
		group = []
		with open(self.pathDir + path, 'r', encoding='UTF-8') as f:
			for line in f:
				group.append(re.sub('\n', '', line))
		return group

	def group_write(self, group=[], mod='a'):
		with open(self.pathDir + r"/info/Group.txt", mod, encoding='UTF-8') as f:
			for gr in group:
				f.write(gr + '\n')

	def read_account(self, path=r"/info/ListAccount.txt"):
		"""
			id phone invite sms invite_date sms_date
		"""
		account = []
		with open(self.pathDir + path, 'r', encoding='UTF-8') as f:
			for line in f:
				user = {}
				l = re.sub('\n', '', line).split(',')
				user['id'] 			= int(l[0])
				user['phone'] 		= l[1]
				user['invite']	 	= int(l[2])
				user['invite_date'] = datetime.strptime(l[3], "%d/%m/%Y %H:%M")
				account.append(user)
		return account

	def write_account(self, account, path=r"/info/ListAccount.txt"):
		'''
		id phone invite sms invite_date sms_date
		'''
		with open(self.pathDir + path, 'w', encoding='UTF-8') as f:
			for acc in account:
				f.write(','.join([
					str(acc['id']),
					acc['phone'],
					str(acc['invite']),
					acc['invite_date'].strftime("%d/%m/%Y %H:%M")
				]) + '\n')

	def active_session_read(self, path=r"/active.temp"):
		try:
			with open(self.pathDir + path, 'r', encoding='UTF-8') as f:
				for line in f:
					session = re.sub('\n', '', line)
					return session
		except FileNotFoundError:
			self.active_session_write()
			return None

	def active_session_write(self, phone="", path=r"/active.temp"): 
		with open(self.pathDir + path, 'w', encoding='UTF-8') as f:
			f.write(phone)

	def conf_read(self, phone, path=r"/config/"):
		cpass = configparser.RawConfigParser()
		cpass.read(self.pathDir+path+phone+"_config.data")
		if len(cpass) == 0:
			return False
		print(cpass, self.pathDir, path+phone)
		return cpass["cred"]

	def conf_write(self, id, hash, phone, path=r"/config/"):
		cpass = configparser.RawConfigParser()
		cpass.add_section('cred')

		cpass.set('cred', 'id', id)
		cpass.set('cred', 'hash', hash)
		cpass.set('cred', 'phone', phone)

		# id phone invite sms invite_date sms_date
		toDay = datetime.today()
		account = self.read_account()
		for i in range(0, len(account)):
			if account[i]["id"] == id:
				account.pop(i)
				break
		account.append({
			'id': id,
			'phone': phone,
			'invite': '0',
			'sms': '0',
			'invite_date': toDay,
			'sms_date': toDay,
			'proxy': 0
			})
		self.write_account(account)

		setup = open(self.pathDir+path+str(phone)+"_config.data", 'w', encoding='UTF-8')
		cpass.write(setup)
		setup.close()