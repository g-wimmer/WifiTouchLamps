"""
Server client for the wifi enabled tor based touch lamp

By Gabriel Wimmer
"""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import time
import RPi.GPIO as GPIO
import board
import neopixel
import threading

hostName = "localhost"
serverPort = 80
pixel_pin = board.D18
num_pixels = 24
ORDER = neopixel.RGB

GPIO.setmode(GPIO.BCM)
pin_a = 23
pin_b = 24
pin_c = 17
pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, brightness=0.4, auto_write=False, pixel_order=ORDER
)

def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
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

def startupsequence(): #fun little startup light sweep
    for x in range(num_pixels):
        pixels[x] = (100,100,100)
        time.sleep(.02)
        pixels.show()
    for x in range(num_pixels):
        pixels[x] = (0,0,0)
        pixels.show()
        time.sleep(.02)

def updatecolor(old_color, new_color, update_time): #smooth change in color
    global current_color_time
    steps = 20
    diff = (old_color - new_color)/steps
    for x in range(steps):
        pixels.fill(wheel(int(old_color - (diff*x))))
        pixels.show()
        time.sleep(.02)
    pixels.fill(wheel(new_color))
    pixels.show()
    current_color_time[0] = new_color
    current_color_time[1] = update_time


class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if "getcurrentcolor" in self.path:
            if "changedtime=" not in self.path or "clientcolor=" not in self.path:
                print("request didnt contain the correct queries")
                self.send_response(400)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(bytes("query did not contain the correct variables", "utf-8"))
                return
            client_changed_time = float(self.path[self.path.index("changedtime=")+12:self.path.index("&clientcolor=")]) #gets the unix time code for when the clients color was changed
            client_color = int(self.path[self.path.index("&clientcolor=")+13:])
            if round(client_changed_time,2) < round(current_color_time[1],2):
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(bytes("<html><head><title>Gabe rocks</title></head>", "utf-8"))
                self.wfile.write(bytes("<p>Color:%dendcolor</p>" % current_color_time[0], "utf-8"))
                self.wfile.write(bytes("<p>Update time:%fendtime</p>" % current_color_time[1], "utf-8"))
                self.wfile.write(bytes("</html>", "utf-8"))
                return
            elif round(client_changed_time,2) == round(current_color_time[1],2): #if the lamps are synced, wait for changes to respond
                for x in range(90):
                    time.sleep(.1)
                    if round(client_changed_time,2) < round(current_color_time[1],2):
                        self.send_response(200)
                        self.send_header("Content-type", "text/html")
                        self.end_headers()
                        self.wfile.write(bytes("<html><head><title>Gabe rocks</title></head>", "utf-8"))
                        self.wfile.write(bytes("<p>Color:%dendcolor</p>" % current_color_time[0], "utf-8"))
                        self.wfile.write(bytes("<p>Update time:%fendtime</p>" % current_color_time[1], "utf-8"))
                        self.wfile.write(bytes("</html>", "utf-8"))
                        return
                self.send_response(201) #201 code indicates that nothing has changed
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(bytes("<html><head><title>Gabe rocks</title></head>", "utf-8"))
                self.wfile.write(bytes("<p>Color:%dendcolor</p>" % current_color_time[0], "utf-8"))
                self.wfile.write(bytes("<p>Update time:%fendtime</p>" % current_color_time[1], "utf-8"))
                self.wfile.write(bytes("</html>", "utf-8"))
                return
            else: #if the client has updated the color more recently, update the hosts color
                updatecolor(current_color_time[0], client_color, client_changed_time)
                self.send_response(201)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(bytes("<html><head><title>Gabe rocks</title></head>", "utf-8"))
                self.wfile.write(bytes("<p>Color:%dendcolor</p>" % client_color, "utf-8"))
                self.wfile.write(bytes("<p>Update time:%fendtime</p>" % client_changed_time, "utf-8"))
                self.wfile.write(bytes("</html>", "utf-8"))
                return
        else:
            self.send_response(203)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes("<html><head><title>Test Page</title></head>", "utf-8"))
            self.wfile.write(bytes("<p>Request: %s</p>" % self.path, "utf-8"))
            self.wfile.write(bytes("<body>", "utf-8"))
            self.wfile.write(bytes("<p>This is an example web server.</p>", "utf-8"))
            self.wfile.write(bytes("</body></html>", "utf-8"))

def waitfortouch():
    global potvalue
    global current_color_time
    GPIO.setup(pin_c, GPIO.IN)
    try:
        while True:
            if GPIO.input(pin_c):
                if abs(potvalue - current_color_time[0]) > 2: #only change colors if the change is significant
                    updatecolor(current_color_time[0], potvalue, round(time.time(),2))
            time.sleep(.1)
    except KeyboardInterrupt:
        pass

def startserver():
    webServer = ThreadingHTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))
    startupsequence()
    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass
    webServer.server_close()
    print("Server stopped.")

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

def readpot(): #is constantly reading the potentiometer value
    global potvalue
    potvalue = 0
    slope = 255 / (90 - 3) #90 and 3 are the range of values read from the potentiometer
    try:
        while True:
            readvalue = analog_read()
            if readvalue > 90: # prevent it from maxing out
                readvalue = 90
            readvalue = (slope * (readvalue - 3)) #this converts the potentiometer value to a value in the range of 0-255
            potvalue = int((readvalue *.7) + (potvalue *.3)) # to smooth out the jumpy values
            #potvalue = int(readvalue)
            time.sleep(1)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    global current_color_time
    current_color_time = [0,0.0]
    t1 = threading.Thread(target=startserver)
    t2 = threading.Thread(target=waitfortouch)
    t3 = threading.Thread(target=readpot)
    t1.start()
    t2.start()
    t3.start()
    t1.join()
    t2.join()
    t3.join()
    print("Exiting server")
