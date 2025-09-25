from pic_irrigation import IrrigationControl
import time
from membraneKeypad import Keypad
from irrigDisplay import irrigationDisplay
from mymqtt import MyMQTT
from machine import WDT
import sys
import uio

#time.sleep(0.1)
ic = IrrigationControl()
disp = irrigationDisplay(sclPin = 27, sdaPin = 26, controller = ic)
kp = Keypad(callback=disp.handle_key)

mqtt = MyMQTT(MQTT_SERVER=b'192.168.3.40',CLIENT_ID=b"raspberrypi_picow",controller=ic)
try:
    mqtt.connect_LAN()
    mqtt.connect_mqtt()
    mqtt.client.set_callback(mqtt.subcallback)
    mqtt.flush_mqtt()

    mqtt.client.subscribe(b"time/response")
    mqtt.client.subscribe(b"irrigation/control")
    mqtt.synctime() #Function blocks until time is received
except Exception as e:
    machine.reset()

# --- Setup ---
wdt = WDT(timeout=6000)  # 10 second watchdog
tm = time.ticks_ms()

ic.prevtime = ic.getTime()[0]
ic.programs[0] = 255
ic.stimes[0] = 6*3600+30*60
ic.rtimes[0] = [240,240,240,240,240,240,240,240]

ic.programs[1] = 255
ic.stimes[1] = 13*3600+30*60
ic.rtimes[1] = [240,240,240,240,240,240,240,240]

fail_timeout = 0
fail_counter = 0
while True:
    # Check for MQTT messages (non-blocking)
    # Feed watchdog to prevent reset
    wdt.feed()
    mqtt.heartbeat()
    
    try:

        # Run device-specific heartbeats
        ic.heartbeat()
        
        disp.heartbeat()
        
        fail_counter = 0

    except OSError as e:
        if (time.ticks_diff(time.ticks_ms(), fail_timeout) >= 5000) or fail_counter == 0:       
            fail_counter += 1            
            fail_timeout = time.ticks_ms()            
            print("OSError in main loop:", e)
            mqtt.publish_mqtt(b'errors',f'OLED raised error. Count: {fail_counter}')
        try:
            disp.reconnect()
        except Exception as re:
            print("Reconnect failed:", re)          
            #machine.reset()  # fallback

    except Exception as e:
        # Any other unexpected error → log and reset
        mqtt.publish_mqtt(b'errors',b'Fatal error in main loop:')        
        print("Fatal error in main loop:", e)
        machine.reset()


    # Fire periodic task (every 40s)
    if time.ticks_diff(time.ticks_ms(), tm) >= 40000:
        mqtt.publish_mqtt(b"heartbeat", f"{ic.rtc.datetime()} {ic.mode} {ic.stationtracker} ")
        tm = time.ticks_ms()

    # Small delay to reduce CPU load        
    time.sleep(0.1)




