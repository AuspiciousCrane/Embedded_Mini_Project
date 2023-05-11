import machine
from machine import Pin
import network
import ubinascii
import time
from umqttsimple import MQTTClient

# WiFi Credentials
SSID = "SSID"
PWD = "PASSWORD"

# MQTT Config
MQTT_SERVER = "iotdev.smartsensedesign.net"
MQTT_USER = "USER"
MQTT_PWD = "PASSWORD"
CLIENT_ID = ubinascii.hexlify(machine.unique_id())

PUB_TOPIC = "LOLICON/BUTTON"

# Connecting to WiFi
nic = network.WLAN(network.STA_IF)
nic.active(True)
nic.connect(SSID, PWD)

while nic.isconnected() == False:
    pass

# Connecting to MQTT
client = MQTTClient(CLIENT_ID, MQTT_SERVER, user=MQTT_USER, password=MQTT_PWD)
client.connect()

# Pin Config
btn_input = Pin(3, mode = Pin.IN, pull = Pin.PULL_UP)

# Pin Callback Config
def btn_callback(p):
    global client
    client.publish(PUB_TOPIC, "1")

btn_input.irq(btn_callback, trigger = Pin.IRQ_FALLING)

# Superloop
while True:
    time.sleep_ms(1000)

