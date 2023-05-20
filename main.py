import machine
import network
import ubinascii
import time
from machine import Pin, ADC, Timer
from umqttsimple import MQTTClient
from neopixel import NeoPixel
from EEPROM import AT24C

# WiFi Credentials
SSID = "Shoukaku"
PWD = "00000000"

# MQTT Config
MQTT_SERVER = "danceoftaihou.live"
MQTT_USER = "google"
MQTT_PWD = "enpassant"
CLIENT_ID = ubinascii.hexlify(machine.unique_id())

SUB_TOPIC = "LOLICON/BUTTON"

# Pico Config
class PixelColor:
    def __init__(self, rgb):
	self.color_idx = 0
	self.intensity = 0
	self.value = [0, 0, 0]
	self.rgb = rgb
	self.is_off = False
	self.is_master_off = False
	self.mqtt = None
	self.update()
    
    def toggle(self):
	self.color_idx += 1

	if self.color_idx > 2:
	    self.color_idx = 0

	#self.value = [0, 0, 0]
	self.update()

    def turn_off(self):
	if self.is_off:
	    return
	self.is_off = True

	if self.mqtt is not None:
	    self.mqtt.publish("LOLICON/ONOFF", "OFF")

	self.update()

    def turn_on(self):
	if not self.is_off:
	    return
	self.is_off = False
	if self.mqtt is not None:
	    self.mqtt.publish("LOLICON/ONOFF", "ON")
	self.update()

    def toggle_master_on_off(self):
	if self.is_master_off:
	    self.is_master_off = False
	else:
	    self.is_master_off = True

    def update(self):
	if self.is_off or self.is_master_off:
	    self.rgb[0] = (0, 0, 0)
	    self.rgb.write()
	    return
	self.value[self.color_idx] = self.intensity
	self.rgb[0] = tuple(self.value)

	if self.mqtt is not None:
	    self.mqtt.publish("LOLICON/RGB", str(self.value))
	self.rgb.write()

    def set_intensity(self, intensity):
	self.intensity = int(intensity)
	self.update()

    def get_brightness(self):
	return self.intensity * 100 / 255

    def set_mqtt_client(self, client):
	self.mqtt = client

    def get_color_val(self):
	return tuple(self.value)

    def set_color_val(self, val):
	self.value = val
	self.color_idx = self.value.index(max(self.value))

	
# Declaring Functions
def calculate_color_intensity():
    global knob, pixel_color
    intensity = knob.read_u16() * 255 / 65535
    pixel_color.set_intensity(intensity)

def poll_ldr(p):
    global ldr, pixel_color
    ldr_val = ldr.read_u16() * 100 / 65535

    if ldr_val < 50:
	pixel_color.turn_on()
    else:
	pixel_color.turn_off()

def write_to_eeprom(i):
    global eeprom, pixel_color
    color_val = pixel_color.get_color_val()
    color_val = str(color_val)
    while len(color_val) is not 16:
	color_val = color_val + ")"
    rgb_str = str.encode(color_val)
    
    eeprom.write(0, rgb_str)
    print("SAVED")

def btn_callback(i):
    global pixel_color
    pixel_color.toggle()

# Declaring Variables
knob = ADC(Pin(27))
ldr = ADC(Pin(26))
rgb_led = NeoPixel(Pin(22, mode = Pin.OUT), 1)
btn = Pin(3, mode = Pin.IN, pull = Pin.PULL_UP)

ldr_timer = Timer(period = 500, mode = Timer.PERIODIC, callback = poll_ldr)
eeprom_timer = Timer(period = 1000, mode = Timer.PERIODIC, callback = write_to_eeprom)

btn.irq(btn_callback, trigger = Pin.IRQ_FALLING)

pixel_color = PixelColor(rgb_led)
eeprom = AT24C()

# Try Reading value of EEPROM
color_str = bytearray(16)

try:
    eeprom.read(0, color_str)
    print(color_str.decode())
    read_color = list(map(lambda t: t.strip(), color_str.decode().strip('()').split(',')))
    read_color = list(map(lambda x: int(x), read_color))
    pixel_color.set_color_val(read_color)
except:
    pass

# Connecting to WiFi
nic = network.WLAN(network.STA_IF)
nic.active(True)
nic.connect(SSID, PWD)

while nic.isconnected() == False:
    pass

# Connecting to MQTT
def callback(topic, msg):
    global pixel_color
    pixel_color.toggle_master_on_off()

client = MQTTClient(CLIENT_ID, MQTT_SERVER, user=MQTT_USER, password=MQTT_PWD)
client.set_callback(callback)
client.connect()
client.subscribe(SUB_TOPIC)

pixel_color.set_mqtt_client(client)

while True:
    client.check_msg()
    calculate_color_intensity()
    pixel_color.update()
    time.sleep_ms(10)

