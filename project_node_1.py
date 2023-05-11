import machine
import network
import ubinascii
import time
from machine import Pin, ADC
from umqttsimple import MQTTClient
from neopixel import NeoPixel

# WiFi Credentials
SSID = "66WIFI-2.4GHZ"
PWD = "0818316115"

# MQTT Config
MQTT_SERVER = "iotdev.smartsensedesign.net"
MQTT_USER = "chayut"
MQTT_PWD = "iotnetwork@2023"
CLIENT_ID = ubinascii.hexlify(machine.unique_id())

SUB_TOPIC = "LOLICON/BUTTON"

# Pico Config
knob = ADC(Pin(27))
ldr = ADC(Pin(26))
rgb_led = NeoPixel(Pin(22, mode = Pin.OUT), 1)

class PixelColor:
    def __init__(self, rgb):
	self.color_idx = 0
	self.intensity = 0
	self.value = [0, 0, 0]
	self.rgb = rgb
	self.is_off = False
	self.update()
    
    def toggle(self):
	self.color_idx += 1

	if self.color_idx > 2:
	    self.color_idx = 0

	self.value = [0, 0, 0]
	self.update()

    def turn_off(self):
	self.is_off = True
	self.update()

    def turn_on(self):
	self.is_off = False
	self.update()

    def update(self):
	if self.is_off:
	    self.rgb[0] = (0, 0, 0)
	    self.rgb.write()
	    return

	self.value[self.color_idx] = self.intensity
	self.rgb[0] = tuple(self.value)
	self.rgb.write()

    def set_intensity(self, intensity):
	self.intensity = int(intensity)
	self.update()

    def get_brightness(self):
	return self.intensity * 100 / 255

    def get_color_val(self):
	return tuple(self.value)

pixel_color = PixelColor(rgb_led)
	
def calculate_color_intensity():
    global knob, pixel_color
    intensity = knob.read_u16() * 255 / 65535
    pixel_color.set_intensity(intensity)

# Connecting to WiFi
nic = network.WLAN(network.STA_IF)
nic.active(True)
nic.connect(SSID, PWD)

while nic.isconnected() == False:
    pass

# Connecting to MQTT
def callback(topic, msg):
    global pixel_color
    pixel_color.toggle()

client = MQTTClient(CLIENT_ID, MQTT_SERVER, user=MQTT_USER, password=MQTT_PWD)
client.set_callback(callback)
client.connect()
client.subscribe(SUB_TOPIC)

while True:
    ldr_val = ldr.read_u16() * 100 / 65535

    if ldr_val < 50:
	pixel_color.turn_on()
    else:
	pixel_color.turn_off()

    client.check_msg()
    calculate_color_intensity()
    pixel_color.update()
    time.sleep_ms(10)

