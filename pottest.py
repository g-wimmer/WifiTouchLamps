#Testing the RC circuit to read the analog output of the potentiometer
import RPi.GPIO as GPIO
import time
import board
import neopixel

GPIO.setmode(GPIO.BCM)
pin_a = 23
pin_b = 24
num_pixels = 24
ORDER = neopixel.RGB
pixel_pin = board.D18
pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, brightness=0.2, auto_write=False, pixel_order=ORDER
)
#values range from 3-90
def wheel(pos):
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos * 3)
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos * 3)
        g = 0
        b = int(pos * 3)
    else:
        pos -= 170
        r = 0
        g = int(pos * 3)
        b = int(255 - pos * 3)
    return (r, g, b) if ORDER in (neopixel.RGB, neopixel.GRB) else (r, g, b, 0)

def discharge():
    GPIO.setup(pin_a, GPIO.IN)
    GPIO.setup(pin_b, GPIO.OUT)
    GPIO.output(pin_b, False)
    time.sleep(.005)

def charge_time():
    GPIO.setup(pin_a, GPIO.OUT)
    GPIO.setup(pin_b, GPIO.IN)
    count = 0
    GPIO.output(pin_a, True)
    while not GPIO.input(pin_b):
        count += 1
    return count

def analog_read():
    discharge()
    return charge_time()

while True:
    val = analog_read()
    print(val)
    pixels.fill(wheel(val))
    pixels.show()
    time.sleep(1)
