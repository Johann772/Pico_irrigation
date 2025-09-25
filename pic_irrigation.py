import time
from machine import Pin
from machine import mem32
from machine import RTC
import sio_gpio_atomic as sio_gpio

class IrrigationControl():
    def __init__(self):
        self.programs = [0 for i in range(8)] #water days, 0 means program disabled
        self.stimes = [0 for i in range(8)] #start time for each program
        self.rtimes = [[0 for i in range(8)] for i in range(8)] #run times for each station 
        self.mode = 0 #0 = Off; 1 = Run;
        self.stationtracker = 0     #Track currently active stations
        self.programCounters = [0]*8 #Tracks the active stations in a program
        self.programTimers = [0]*8 #Tracks the active time of a station in a program
        self.activePrograms = 0 #Tracks currenly active programs
        self.modePin = Pin(22,Pin.IN,Pin.PULL_UP)
        #self.modeOutPin = Pin(25,Pin.OUT)
        self.rtc = RTC()
        #self.rtc.datetime((2025,8,5,0,0,25,0,0))
#(2025,7,29,0,11,50,50,0)
        self.prevtime = 0
        sio_gpio.setSioOutRegister(0xff)
        sio_gpio.setOutputs((0,1,2,3,4,5,6,7))

    def setTime(self):
        pass

    #def getTime(self):
    #    t = time.localtime()
    #    return((t.tm_hour*3600+t.tm_min*60+t.tm_sec,t.tm_wday+1))
    def getTime(self):
        t = self.rtc.datetime()
        return((t[4]*3600+t[5]*60+t[6],t[3]+1))

    def timediff(self,t1,t2):
        dt = (t1-t2) % 86400
        #print(dt)
        return dt
    

    #Helper function - checks if current time matches with any of the program start times
    def checkrun(self):
        counter = 1
        i = 0
        programs = 0
        curtime = self.getTime()
        for st in self.stimes:
            if (self.timediff(curtime[0],st)) <5:
                #print("true")
                if self.programs[i] & curtime[1]:
                    #ensure active program has at least one run time > 0
                    if sum(self.rtimes[i]):
                        programs = programs | counter
            counter = counter << 1
            i+=1
            self.activePrograms = self.activePrograms | programs
        return self.activePrograms
    
    def writeStationOutput(self,stations):
        if stations:
            sio_gpio.setSioOutRegister(stations^0b11111111)
        else:
            #disable all
            sio_gpio.setSioOutRegister(0b11111111)
    def getCurrentStation(self, program, counter):
        station = counter
        if station > 7:
            return 8
        while not self.rtimes[program][station]:
            station = station + 1
            if station > 7:
                break
        return station

    def heartbeat(self):
        #self.mode = self.modePin.value()
        t = self.getTime()[0]
        dt = self.timediff(t,self.prevtime)
        if dt < 1:
            return
        self.prevtime = t
        # checks the current time to see if a program must trigger on
        self.checkrun()
        #check input switch if off, disable all programs
        if self.activePrograms and not self.mode:
            #self.modeOutPin.value(1)
            stationtracker = 0
            for i in range(8):
                p = (self.activePrograms>>i) & 1
                if p:    
                    curStation = self.getCurrentStation(i,self.programCounters[i])
                    if curStation > 7:
                        if i == 7:
                            self.programs[7] = 0
                        self.activePrograms = self.activePrograms ^ 1<<i
                        self.programCounters[i] = 0
                        self.programTimers[i] = 0
                    else:
                        self.programCounters[i] = curStation                        
                        self.programTimers[i] = self.programTimers[i] + dt
                        if self.programTimers[i] > self.rtimes[i][self.programCounters[i]]:
                            self.programCounters[i] = self.getCurrentStation(i,self.programCounters[i]+1)
                            self.programTimers[i] = 0
                        if self.programCounters[i] > 7:
                            if i == 7:
                                self.programs[7] = 0
                            self.activePrograms = self.activePrograms ^ 1<<i
                            self.programCounters[i] = 0
                            self.programTimers[i] = 0
                        else:
                            stationtracker = stationtracker | (1<<(self.programCounters[i]))
            self.stationtracker = stationtracker
            self.writeStationOutput(self.stationtracker)
        else:
            self.programs[7] = 0
            self.activePrograms = 0
            self.programCounters = [0]*8
            self.programTimers = [0]*8
            self.stationtracker = 0
            #self.modeOutPin.value(0)
            self.writeStationOutput(0)
