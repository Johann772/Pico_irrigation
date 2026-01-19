import os
from Telbot import Telbot
import paho.mqtt.client as mqtt

class Menu:
    def __init__(self,bot: Telbot,client):
        self.bot = bot
        self.mast_id = [1055245445,]
        self.mqtt_client = client

    def mqtt_publish(self,topic, payload):
        if self.mqtt_client.is_connected():
            result = self.mqtt_client.publish(topic, payload)
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                print("❌ Publish failed:", result.rc)
        else:
            print("⚠️ MQTT not connected, message not sent:", payload)  

    def callback(self):
        if (self.bot.getFromId() in self.mast_id):        
            id = self.bot.getFromId()
            msg = self.bot.getMsg()
            if (msg == "?"):
                self.handleComIP(id)
            if (msg == "on"):
                self.mqtt_publish("irrigation/control","on")
                self.bot.sendPlainMsg("on",id)
            if (msg == "off"):
                self.mqtt_publish("irrigation/control","off")
                self.bot.sendPlainMsg("off",id)                

    def handleComIP(self,id):
       p = os.popen('ifconfig')
       msg = p.read()
       self.bot.sendPlainMsg(msg,id)


