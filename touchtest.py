import RPi.GPIO as GPIO
import board

pin_c = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(pin_c, GPIO.IN)

print("starting loop")
while True:
    if GPIO.input(pin_c):
        print("reading touch")
