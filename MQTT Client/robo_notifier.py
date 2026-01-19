import os
import json
from Telbot import Telbot
from datetime import datetime
import time


class RoboNotifier:
    def __init__(self,bot: Telbot):
        self.bot = bot
        self.deadTime = 20
        self.halt = False
        self.needInit = True
                 
    def initialize(self):
        with open('zones.json','r') as f:
            self.zones.update(json.load(f))
            self.statusTime = time.time()
            if len(self.zones["zones"]):
                for i in range(len(self.zones["zones"])):
                    self.zones["zones"][i]["status_flag"] = 0
            self.needInit = False
    
    def haltLoop(self):
        self.halt = True
        self.needInit = True
        time.sleep(1)
        
    def resumeLoop(self):
        self.halt = False
    
    def reInit(self):
        self.needInit = True
    
    def loop(self):      
        try:
            if not(self.ser.isOpen()):
                self.ser.open()
        except:
            self.ser.close()
            if not (self.usbFail):
                if not (self.usbFailLog):
                    self.logEvent("Failed to connect to receiver. Please check USB connection.")
                    self.usbFailLog = True
                if (self.bot.sendPlainMsg("Failed to connect to receiver. Please check USB connection.",self.groupId)):
                    self.usbFail = True
            return
        
        self.usbFailLog = False
        self.usbFail = False
        self.statusTime = time.time()
        l = len(self.zones['zones'])
        if l:
            for i in range(l):
                self.zones['zones'][i]['status_flag'] = 0

    

