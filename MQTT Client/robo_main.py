from Telbot import Telbot
from menu import Menu
import time
import os

def isSynchronized():
	try:
		s = os.popen('timedatectl | grep synch')
		s = s.read()
		s = s.strip().split(":")[1].strip()
	except:
		return False
	if s == "yes":
		return True
	else:
		return False

while not isSynchronized():
	time.sleep(5)

bot = Telbot("1737713996:AAGAlRJQ60dfrCkQd3kGqSISmRRHGarAUsM")

menu = Menu(bot)
bot.startPoll(menu.callback)

while True:
	time.sleep(5)
			