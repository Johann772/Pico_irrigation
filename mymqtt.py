import _thread
import time
import network
import machine
from umqtt.robust import MQTTClient

class MyMQTT():
    def __init__(self,MQTT_SERVER,CLIENT_ID,controller):
        # MQTT Parameters
        self.client = None
        self.MQTT_SERVER = MQTT_SERVER
        self.MQTT_PORT = 1883
        self.MQTT_USER = ''
        self.MQTT_PASSWORD = ''
        self.MQTT_CLIENT_ID = CLIENT_ID
        self.MQTT_KEEPALIVE = 7200
        self.MQTT_SSL = False   # set to False if using local Mosquitto MQTT broker
        self.MQTT_SSL_PARAMS = {'server_hostname': MQTT_SERVER}
        self.wifi_connected = False
        self.controller = controller
        self.flush = True
        self.timesync = False
        self.echo = False

    def connect_LAN(self):
        nic = network.WIZNET5K()
        nic.active(True)
        #nic.ifconfig()
        nic.ifconfig('dhcp')
        self.wifi_connected = True
        print('IP address :', nic.ifconfig())

        while not nic.isconnected():
            time.sleep(1)
            print(nic.regs())
            
    def connect_mqtt(self):
        try:
            self.client = MQTTClient(client_id=self.MQTT_CLIENT_ID,
                                server=self.MQTT_SERVER,
                                port=self.MQTT_PORT,
                                user=self.MQTT_USER,
                                password=self.MQTT_PASSWORD,
                                keepalive=self.MQTT_KEEPALIVE,
                                ssl=self.MQTT_SSL,
                                ssl_params=self.MQTT_SSL_PARAMS)
            self.client.connect()
        except Exception as e:
            print('Error connecting to MQTT:', e)
            raise  # Re-raise the exception to see the full traceback

    def publish_mqtt(self,topic, value):
        self.client.publish(topic, value,qos=1)
        print(topic)
        print(value)
        print("Publish Done")

    
    def subcallback(self,topic, msg):
        if self.flush:
            return
        if topic == b"time/response":
            msg = msg.decode()
            print("Received time:", msg)
            try:
                # Expected format: YYYY-MM-DD HH:MM:SS
                y, mo, d = map(int, msg.split()[0].split("-"))
                h, mi, s = map(int, msg.split()[1].split(":"))
                rtc = machine.RTC()
                rtc.datetime((y, mo, d, 0, h, mi, s, 0))
                print("RTC updated to:", rtc.datetime())
                self.timesync = True
            except Exception as e:
                print("Error parsing time:", e)
        if topic == b"irrigation/control":
            msg = msg.decode()
            print("irrigation/control", msg)
            if msg == "on":
                self.controller.mode = 0
                self.echo = True
            if msg == "off":
                self.controller.mode = 1
                self.echo = True
            if "run" in msg:
                runtimes = list(map(int, msg.split()[1:]))
                if not self.controller.activePrograms:
                    self.controller.programs[7] = 255
                    self.controller.stimes[7] = self.controller.getTime()[0]
                    self.controller.rtimes[7] = runtimes                
                self.echo = True
    
    def flush_mqtt(self):
        flush_timer = time.ticks_ms()
        while 1:
            self.client.check_msg()
            time.sleep(0.1)
            if (time.ticks_diff(time.ticks_ms(), flush_timer) > 2000):
                self.flush = False
                return
    

    def synctime(self):
        for _ in range(3):
            # Send the time request
            self.publish_mqtt(b"time/request", b"get_time")
            start = time.ticks_ms()
            while time.ticks_diff(time.ticks_ms(), start) < 2000:
                self.client.check_msg()
                if self.timesync:
                    return
                time.sleep(0.1)

        # If we get here, all retries failed
        machine.reset()

    def heartbeat(self):
        if not self.wifi_connected:
            print('Error connecting to the network... exiting program')
        else:
            #self.connect_mqtt()
            #self.client.set_callback(self.subcallback)
            #self.client.subscribe(b"time/response")
            #self.publish_mqtt(b"time/request",b"REQ")
            self.client.check_msg()
            if self.echo:
                self.publish_mqtt(b"irrigation/echo",f"mode {self.controller.mode} stations {self.controller.stationtracker}".encode())
                self.echo = False
                #self.publish_mqtt('tst', 'Hello')
                #time.sleep(0.1)
