#{'ok': True, 'result': [{'update_id': 717582284, 'message': {'message_id': 1197, 'from': {'id': 1055245445, 'is_bot': False, 'first_name': 'Johann', 'language_code': 'en'}, 'chat': {'id': 1055245445, 'first_name': 'Johann', 'type': 'private'}, 'date': 1634204146, 'text':'?'}}]}	

#{'ok': True, 'result': []}

#https://api.telegram.org/bot1737713996:AAFYrAdPpek5AvrRiaprM9sclEUyd7-CJtg/getupdates?offset=-1&timeout=60

import time
import requests
import json
import threading

class Telbot:
	def __init__(self,id):
		self.id = id
		self.url = f'https://api.telegram.org/bot{self.id}/'
		self.offset = -1
		self.response = {}
		self.polling = False
		self.bot_commands = [] 
		
	def startPoll(self,callback):
		self.polling = True
		self.getUpdate(0)
		self.getUpdate(0)
		self.response = {}
		threading.Thread(target=self._polling, args=(callback,), daemon=True).start()
	
	def stopPoll(self):
		self.poll = False
	
	def _polling(self,callback):
		while self.polling:
			if self.getUpdate(60):	
				callback()				
	
	def getUpdate(self,timeout):
		try:
			print(f"Waiting for response with offset {self.offset}")
			self.response = requests.get(self.url+f'getupdates?offset={self.offset}&timeout={timeout}',timeout=60).json()
			self.offset = self.response["result"][0]["update_id"]+1
			print(self.response)
			print(self.offset)
		except:
			time.sleep(0.5)
			return False
		else:
			return True
	
	def sendMsg(self,data):
		headers = {"Content-Type" : "application/json"}
		data = json.dumps(data)
		try:
			response = requests.post(self.url+"sendMessage",headers=headers,data=data,timeout=15).json()["ok"]
		except:
			return False
		
		return response

	def sendFile(self,id,file):
		try:
			response = requests.post(self.url+f"sendDocument?chat_id={id}",files=file,timeout=15).json()["ok"]
		except:
			return 0
		
		return response			

	
	def sendPlainMsg(self,s,id):
		headers = {"Content-Type" : "application/json"}
		data = json.dumps({"chat_id": id, "text": s, "reply_markup": {"remove_keyboard":True}})
		try:
			response = requests.post(self.url+"sendMessage",headers=headers,data=data,timeout=15).json()["ok"]
		except:
			return False

		return response
	
	def getMsg(self):
		try:
			r = self.response["result"][0]["message"]["text"]
		except:
			r = ""
		finally:
			return r


	def getFromId(self):
		try:
			r = self.response["result"][0]["message"]["from"]["id"]
		except:
			r = ""
		finally:
			return r

	def addBotCommand(self,cmd,desc):
		self.bot_commands.append({"command":cmd,"description":desc})
	
	def getBotCommands(self):
		lst = []
		l = len(self.bot_commands)
		if l:
			for i in range(l):
				lst.append(self.bot_commands[i]["command"])
		return lst

	def registerBotCommands(self):
		lst = len(self.bot_commands)
		if lst:
			data = json.dumps({"commands":self.bot_commands})
			headers = {"Content-Type" : "application/json"}
			try:
				response = requests.post(self.url+"setMyCommands",headers=headers,data=data,timeout=15).json()
			except:
				return 0
			if response["ok"]:
				return 1
			else:
				return 0


