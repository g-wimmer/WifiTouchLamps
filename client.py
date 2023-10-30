import time
import RPi.GPIO as GPIO
import board
import neopixel
import threading
import requests
from requests.exceptions import Timeout

session = requests.session()
session.proxies = {}
session.proxies['http'] = 'socks5h://localhost:9050'
session.proxies['https'] = 'socks5h://localhost:9050'

url = "" #insert onion address of server here
GPIO.setmode(GPIO.BCM)
pin_a = 23
pin_b = 24
pin_c = 17
pixel_pin = board.D18
num_pixels = 24
ORDER = neopixel.RGB

pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, brightness=0.4, auto_write=False, pixel_order=ORDER
)
def updatecolor(old_color, new_color, update_time): #smooth change in color
    global current_color_time
    current_color_time[0] = new_color
    current_color_time[1] = update_time
    steps = 20
    diff = (old_color - new_color)/steps
    for x in range(steps):
        pixels.fill(wheel(int(old_color - (diff*x))))
        pixels.show()
        time.sleep(.02)
    pixels.fill(wheel(new_color))
    pixels.show()


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

def analog_read():
    discharge()
    return charge_time()

def charge_time():
    GPIO.setup(pin_a, GPIO.OUT)
    GPIO.setup(pin_b, GPIO.IN)
    count = 0
    GPIO.output(pin_a, True)
    while not GPIO.input(pin_b):
        count += 1
    return count

def startupsequence(): #fun little startup light sweep
    for x in range(num_pixels):
        pixels[x] = (100,100,100)
        time.sleep(.02)
        pixels.show()
    for x in range(num_pixels):
        pixels[x] = (0,0,0)
        pixels.show()
        time.sleep(.02)

def readpot(): #is constantly reading the potentiometer value
    global potvalue
    potvalue = 0
    slope = 255 / (111 - 1) #111 and 3 are the range of values read from the potentiometer
    try:
        while True:
            readvalue = analog_read()
            if readvalue > 111: # prevent it from maxing out
                readvalue = 90
            readvalue = (slope * (readvalue - 1)) #this converts the potentiometer value to a value in the range of 0-255
            potvalue = int((readvalue *.7) + (potvalue *.3)) # to smooth out the jumpy values
            #potvalue = int(readvalue)
            time.sleep(1)
    except KeyboardInterrupt:
        pass

def waitfortouch():
    global potvalue
    global current_color_time
    GPIO.setup(pin_c, GPIO.IN)
    try:
        while True:
            if GPIO.input(pin_c):
                if abs(potvalue - current_color_time[0]) > 2: #only change colors if the change is significant
                    updatecolor(current_color_time[0], potvalue, round(time.time(),2))
                    try:
                        r = session.get(url+"?changedtime="+str(current_color_time[1])+"&clientcolor="+str(current_color_time[0]), timeout=9)
                        if(r.status_code == 200):
                            newc = int(r.text[r.text.index("Color:")+6:r.text.index("endcolor")])
                            newt = float(r.text[r.text.index("time:")+5:r.text.index("endtime")])
                            if round(newt,1) > round(current_color_time[1],1): #incase the server has updated the color during the time that the requests was being sent
                                updatecolor(current_color_time[0], newc, newt)
                        elif r.status_code != 201:
                            print("Theres been an error: "+int(r.status_code))
                    except Timeout: #flashes red to indicate that it was unable to reach the hostlamp
                        pixels.fill((0,0,0))
                        pixels.show()
                        time.sleep(.25)
                        pixels.fill((200,10,10))
                        pixels.show()
                        time.sleep(.25)
                        pixels.fill(wheel(current_color_time[0]))
                        pixels.show()
                    except requests.exceptions.ConnectionError:
                        pixels.fill((0,0,0))
                        pixels.show()
                        time.sleep(.2)
                        pixels.fill((10,100,10))
                        pixels.show()
                        time.sleep(.2)
                        pixels.fill(wheel(current_color_time[0]))
                        pixels.show()
                        print("Lost connection to host. Retrying in 15 seconds")
                        time.sleep(.3)
            time.sleep(.1)
    except KeyboardInterrupt:
        pass

def startclient():
    try:
        timeouttime = 11
        startupsequence()
        while True:
            time.sleep(.1)
            try:
                r = session.get(url+"?changedtime="+str(current_color_time[1])+"&clientcolor="+str(current_color_time[0]), timeout=timeouttime)
                timeouttime = 11
                if r.status_code == 200:#200 indicates that the color has been updated on the host
                    newc = int(r.text[r.text.index("Color:")+6:r.text.index("endcolor")])
                    newt = float(r.text[r.text.index("time:")+5:r.text.index("endtime")])
                    print("time from server:"+str(newt))
                    print("last updated time:"+str(current_color_time[1]))
                    if round(newt,2) > round(current_color_time[1],2):
                        updatecolor(current_color_time[0], newc, newt)
                elif r.status_code != 201: #201 is for when they are in sync so if it isnt 200 or 201 there has been an error
                    print("There has been an error: "+str(r.status_code))
                else:
                    time.sleep(.05)
            except Timeout: #increase time between requests
                print("Couldnt reach the server increasing timeouttime")
                if timeouttime == 11:
                    timeouttime = 30
                elif timeouttime == 30:
                    timeouttime = 40
            except requests.exceptions.ConnectionError:
                print("Lost connection to host. Retrying in 20 seconds")
                time.sleep(20)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    global current_color_time
    current_color_time = [0,0.0]
    t1 = threading.Thread(target=startclient)
    t2 = threading.Thread(target=waitfortouch)
    t3 = threading.Thread(target=readpot)
    t1.start()
    t2.start()
    t3.start()
    t1.join()
    t2.join()
    t3.join()
    print("Exiting client")
