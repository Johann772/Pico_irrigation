import time
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
from membraneKeypad import Keypad
import time

class irrigationDisplay:
    def __init__(self,sclPin = 27, sdaPin = 26,controller = None):
        self.i2c = I2C(1, scl=Pin(sclPin), sda=Pin(sdaPin))
        self.oled = SSD1306_I2C(128,64,self.i2c)
        self.selected_stations = [1]*8
        self.input_mode = "status" # status, select, runtime
        self.runtime_input = ""
        self.controller = controller
        self.timeout = time.ticks_ms()
        self.display_status = True
    
    def on(self):
        self.oled.poweron()

    def reconnect(self):
        #self.i2c = I2C(1, scl=Pin(sclPin), sda=Pin(sdaPin))
        self.oled = SSD1306_I2C(128,64,self.i2c)
        self.display_status = True

    def off(self):
        self.oled.poweroff()

    def heartbeat(self):
        dt = time.ticks_diff(time.ticks_ms(),self.timeout)
        
        if (self.display_status):
            if (self.input_mode == "status") or (self.controller.activePrograms and self.input_mode != "mode_select"):
                self.draw_status()
                  
            if  dt >= 20000:
                self.input_mode = "status"
                self.off()
                self.display_status = False

    # --- Display Functions ---
    def draw_status(self):
        self.input_mode = "status"
        self.oled.fill(0)

        # Get current time and date
        t = time.localtime()
        current_time = "{:02}:{:02} {:04}-{:02}-{:02}".format(t[3], t[4], t[0], t[1], t[2])
        self.oled.text(current_time, 0, 0)

        # Show status
        if self.controller.activePrograms:
            status = "Running"
        elif self.controller.mode:
            status = "Off"
        else:
            status = "Idle"
        self.oled.text("Status: "+status , 0, 22)

        # Show active stations if running
        if self.controller.activePrograms:
            for i in range(8):
              state = "X" if ((self.controller.stationtracker >> i)&1)  else "-"
              self.oled.text(str(i+1), i * 16, 44)
              self.oled.text(state, i * 16, 54)
        self.oled.show()

    def draw_station_select(self):
        self.oled.fill(0)
        self.oled.text("Select Stations", 0, 0)
        for i in range(8):
            state = "X" if self.selected_stations[i] else "-"
            self.oled.text(str(i+1), i * 16, 22)
            self.oled.text(state, i * 16, 34)
            #oled.text(f"{i+1}:{state}", (i % 4) * 32, 16 + (i // 4) * 12)
        self.oled.text("*=Back D=Start", 0, 56)
        self.oled.show()

    def draw_runtime_input(self):
        self.oled.fill(0)
        self.oled.text("Enter time (min):", 0, 0)
        self.oled.text(self.runtime_input, 0, 16)
        self.oled.text("*=Back D=Start", 0, 56)
        self.oled.show()

    def draw_switch_mode(self):
        if self.controller.mode:
            txt = "start"
        else:
            txt = "stop"
        self.oled.fill(0)
        self.oled.text(f"Confirm {txt}?", 0, 0)
        self.oled.text("*=Cancel D=Yes", 0, 56)
        self.oled.show()        

    # --- Keypad Callback ---
    def handle_key(self,key):
        self.timeout = time.ticks_ms()
        if not self.display_status:
            self.on()
            self.display_status = True
            return

        if self.input_mode == "status":
            if key == "A":
                self.input_mode = "mode_select"
                self.draw_switch_mode()
            else:
                self.input_mode = "select"
                self.draw_station_select()
            return
        
        if self.input_mode == "mode_select":
            if key == "*":
                self.input_mode = "status"
                self.draw_status()
            if key == "D":
                self.controller.mode = self.controller.mode^1
                self.input_mode = "status"
                self.draw_status()                
        
        if self.input_mode == "select":
            if key == "*":
              self.input_mode = "status"
              self.draw_status()
            if key == "0":
                if all(self.selected_stations):
                    self.selected_stations = [0] * 8
                else:
                    self.selected_stations = [1] * 8
                self.draw_station_select()
            elif key in "12345678":
                idx = int(key) - 1
                self.selected_stations[idx] = not self.selected_stations[idx]
                self.draw_station_select()
            elif key == "D":
                self.input_mode = "runtime"
                self.runtime_input = ""
                self.draw_runtime_input()

        elif self.input_mode == "runtime":
            if key == "*":
                self.input_mode = "select"
                self.draw_station_select()
            elif key == "C":
                self.runtime_input = ""
                self.draw_runtime_input()
            elif key == "D":
                if self.runtime_input.isdigit() and 1 <= int(self.runtime_input) <= 99:
                    #Schedule program to run
                    self.controller.programs[7] = 255
                    self.controller.stimes[7] = self.controller.getTime()[0]
                    self.controller.rtimes[7] = [int(self.runtime_input)*60*y for y in self.selected_stations]
                    self.input_mode = "status"
                    self.draw_status()
            elif key in "0123456789" and len(self.runtime_input) < 2:
                self.runtime_input += key
                self.draw_runtime_input()
