#!/usr/bin/env python3.5

__author__      = "David Minard"
__copyright__   = "Octavio"

# IMPORT

import RPi.GPIO as GPIO
import time
import subprocess
import sys
import os
import sys, time
import telnetlib
import json
import re
from rpi_ws281x import PixelStrip, Color
from neopixel import *
from threading import Thread

# INIT VAR
snap_port = 1705
BOUTON = 13
false = False
true = True
list_clients = []
status_server = {"id":1,"jsonrpc":"2.0","method":"Server.GetStatus"}
macaddr = subprocess.getoutput("cat /sys/class/net/wlan0/address")
myIP = subprocess.check_output(["hostname","-I"]).strip().decode()
status_server = {"id":1,"jsonrpc":"2.0","method":"Server.GetStatus"}
cmd = ["sudo", "service","snapclient","status"]
cmd_music = ["cat", "/proc/asound/card0/pcm0p/sub0/status"]
pause_thread = False

#INIT BUTTONS
GPIO.setmode(GPIO.BCM)
GPIO.setup(12, GPIO.IN)
GPIO.setup(4, GPIO.IN)

#INIT LEDS
LED_COUNT      = 5
LED_PIN        = 10
LED_FREQ_HZ    = 800000
LED_DMA        = 10
LED_BRIGHTNESS = 255
LED_INVERT     = False
LED_CHANNEL    = 0

strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

#INIT SERVER
print("IP : " + myIP)
subprocess.call(["sudo","service","raspotify","stop"])
subprocess.call(["sudo","service","snapserver","stop"])
subprocess.call(["sudo","service","snapclient","restart"])
print("\n ***SNAPCLIENT STARTED*** \n")


#Cacher PA Bluetooth
subprocess.call(["sudo","hciconfig","hci0","down"])
subprocess.call(["sudo","hciconfig","hci0","noscan"])

#DEF SUBPROCESS

def ruscall(command_ruscall):
    result = 0
    while result == 0:
        try:
            subprocess.call(command_ruscall)
            result = 1
        except:
            pass

def ruspopen(command_ruspopen):
    result = 0
    while result == 0:
        try:
            subprocess.Popen(command_ruspopen)
            result = 1
            print('command success')
        except:
            pass

#DEF LEDS
def nowifi():
        while True:
          for j in range(1):
            for q in reversed(range(7)):
                for i in range(strip.numPixels()):
                    strip.setPixelColor(i+q, Color(251,251,251))
                strip.show()
                time.sleep(50/500.0)
                for i in range(strip.numPixels()):
                    strip.setPixelColor(i+q, Color(0,0,0,0))
          time.sleep(0.1)

def colorWipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms/10000.0)

def doubletouch():
    colorWipe(strip, Color(251,251,251), 0)
    time.sleep(0.3)
    colorWipe(strip, Color(0,0,0), 0)
    time.sleep(0.3)
    colorWipe(strip, Color(251,251,251), 0)

#DEF CHECK MUSIC OR NOT
class check_music (Thread):
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        while True:
            if pause_thread is False:
                procc = subprocess.Popen(cmd_music, stdout=subprocess.PIPE)
                rep = procc.communicate()[0].decode('utf-8')
                if ("RUNNING" in rep) :
                    colorWipe(strip, Color(251,251,251), 0)
                else :
                    colorWipe(strip, Color(0,0,0), 0)
                    time.sleep(1)

thread = check_music()
thread.daemon = True

# DEF du signal
def signal_handler(sig, frame):
    print("\n ---FIN PRGM CLIENT--- \n")
    quit_thread = True
    GPIO.cleanup()
    os._exit(0)

# DEF check server

def checkServer():
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    lastLine = (proc.stdout.readlines()[-1]).decode()
    print (lastLine)
    if (("Error in socket shutdown" or "Exception in Controller" or "Started Snapcast client.") in lastLine) :
        print ("*NO SERVER, REBOOTING SNAPCLIENT*")
        GPIO.cleanup()
        ruscall(["python3", "/home/config/bin/scan_octavio.py", "|logger -t octavio"])
        GPIO.cleanup()
        quit_thread = True
        sys.exit()
        return 0

    elif ("Connected to" in lastLine) :
        print("*OK*")
        global ipServ
        ipServ = lastLine.split(" ")[-1]
        print("ip server : " + ipServ)
        return 1

    return -1

checkServer()

#CONNEXION TELNET
try :
    telnet = telnetlib.Telnet(ipServ, snap_port)
    print('TELNET CONNEXION OK')
except:
    print("Telnet Connection Lost")
    ruscall(["python3", "/home/config/bin/scan_octavio.py", "|logger -t octavio"])
    GPIO.cleanup()
    quit_thread = True
    sys.exit()


# UPDATE LIST CLIENTS

def updateclient():
        global list_clients
        new_list_clients = []
        while new_list_clients == []:
            print('UPDATE CLIENT LIST')
            telnet.write(json.dumps(status_server).encode('ASCII') + b"\r\n")
            time.sleep(2)
            getstatus = telnet.read_very_eager().decode()
            mac_extractor = re.compile('([0-9a-f]{2}(?::[0-9a-f]{2}){5})', re.IGNORECASE)
            new_list_clients = re.findall(mac_extractor, getstatus)
            new_list_clients = list(set(new_list_clients))
        if new_list_clients > list_clients :
            list_clients = new_list_clients
            print("CLIENT LIST UPDATED")
        print(list_clients)

updateclient()



# DEF boutons

def plus(channel):
    global pause_thread
    pause_thread = True
    timebutton = 0
    colorWipe(strip, Color(251,251,251), 0)
    global list_clients
    print('MUSIQUE SUR CE CLIENT')
    unmute = {"id":8,"jsonrpc":"2.0","method":"Client.SetVolume","params":{"id":macaddr,"volume":{"muted":false}}}
    try :
        telnet.write(json.dumps(unmute).encode('ASCII') + b"\r\n")
    except :
        try :
            telnet = telnetlib.Telnet(ipServ, snap_port)
            telnet.write(json.dumps(unmute).encode('ASCII') + b"\r\n")
        except :
            print("Telnet Connection Lost")
            ruscall(["python3", "/home/config/bin/scan_octavio.py", "|logger -t octavio"])
            GPIO.cleanup()
            quit_thread = True
            sys.exit()
    print("Octavio " + macaddr + " actif")
    #On mute les autres clients
    while GPIO.input(4) == True:
        timebutton = timebutton + 0.1
        time.sleep(0.1)
    if 0 <= timebutton < 2:
        for i in range (len(list_clients)) :
            if (list_clients[i] != macaddr):
                mute = {"id":8,"jsonrpc":"2.0","method":"Client.SetVolume","params":{"id":list_clients[i],"volume":{"muted":true}}}
                telnet.write(json.dumps(mute).encode('ASCII') + b"\r\n")
                print("Client " + list_clients[i] + " eteint")
                updateclient()
    else :
#AJOUT SANS MUTE
        doubletouch()
        print('AJOUT APPAREIL OCTAVIO')
        timebutton = 0
    pause_thread = False

def moins(channel):
    global pause_thread
    pause_thread = True
    colorWipe(strip, Color(0,0,0), 0)
    print('MUTE THIS OCTAVIO')
    mute = {"id":8,"jsonrpc":"2.0","method":"Client.SetVolume","params":{"id":macaddr,"volume":{"muted":true}}}
    try :
        telnet.write(json.dumps(mute).encode('ASCII') + b"\r\n")
    except :
        try :
            telnet = telnetlib.Telnet(ipServ, snap_port)
            telnet.write(json.dumps(mute).encode('ASCII') + b"\r\n")
        except :
            print("Telnet Connection Lost")
            ruscall(["python3", "/home/config/bin/scan_octavio.py", "|logger -t octavio"])
            GPIO.cleanup()
            quit_thread = True
            sys.exit()
    print("Octavio " + macaddr + " actif")
    time.sleep(1)
    pause_thread = False

# EVENT DETECT

GPIO.add_event_detect(12, GPIO.RISING, callback=moins)
GPIO.add_event_detect(4, GPIO.RISING, callback=plus)
thread.start()

# PGME
print ("Lancement Programme Client")

try :
    while True :
        try:
            checkServer()
            time.sleep(10)
        except :
            pass
except KeyboardInterrupt:
    print("\n --- FIN PRGM CLIENT --- \n")
    GPIO.cleanup()
    ruscall(["python3", "/home/config/bin/scan_octavio.py", "|logger -t octavio"])
    GPIO.cleanup()
    quit_thread = True
    sys.exit()
