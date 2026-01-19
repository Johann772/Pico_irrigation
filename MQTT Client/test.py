from Telbot import Telbot
from menu import Menu
import time
import os

bot = Telbot("1737713996:AAGAlRJQ60dfrCkQd3kGqSISmRRHGarAUsM")

menu = Menu(bot)
bot.startPoll(menu.callback)

while True:
	time.sleep(5)
