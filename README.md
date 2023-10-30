This is the code for a pair of wifi/tor enabled touch lamps. A pair of two lamps can be connected to any two different wifi networks and be able to interactivly syncronize their colors. Touching one lamp will cause the other to change to the first lamps color. No central server is required for the lights to communicate. The dial on the side of the lamp is used to control the color of your lamp.

Lamp Hardware Specification:

Hardware wise, the two lamps are identical. They consist of the following:<br>
Raspberry Pi Zero W<br>
Capacitive Touch Sensor<br>
Potentiometer<br>
Resistor-Capacitor Cirtcuit (to serve as an analog to digital for the potentiometer)<br>
Neopizel Light Ring<br>
3 Volt to 5 Volt step up circuit to power the neopixel<br>
3D Printed Housing to hold the electronics. The top half is printed in a white filament to serve as a diffuser for the light (files included in repo)<br>

The two lamps are divided into client and server. Each can operate independently of the other if the other lamp is offline. 

The server is a simple http python server that constantly waits for a color change from the client. Upon recieving notice that the client has changed color, the server will update its own. The client periodically sends a heartbeat to the server even if no color changes have occured. The server will hold onto this http request and wait to respond for a period of time. If the server changes its color, it will immeditaly respond to the held request from the client to inform it of this change. This system was put in place to ensure that the lamps are not repeatedly bouncing requests back and forth continously and instead only communicate around once every minute.

The lamps do not operate on the clearnet. Instead the server makes use of the Tor network to host its http server. This was done for multiple reasons. The first of which was security. By using an onion link, only the client which is hardcoded with the link, will be able to find this server. This adds a layer of security and prevents potential DDOS attacks. The second reason is that the Tor network will allow the webserver to function regardless of where it is located and without control over the network it is connected to. A normal webserver would require network administrator rights to provide a fixed ip, port forwarding and other such conveniences. The tor network allows the client to always find the server if the server is connected to the Tor network. By not needing network administration powers, these lamps to not require some central server to communicate. Removing a central server or some dependence on a cloud service was one of the main goals of this project.

Both lamps make use of a potentiometer to control the color of the neopixels. The RC-circuit works as an analog to digital converter for the potentiometer. The potentiometer will now roughly serve as a dial that controls the colors. To smooth the values from the rc-circuit, the lamps use a simple moving average of the inputs.