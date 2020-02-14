#!/usr/bin/env python3.5

__author__      = "David Minard"
__copyright__   = "Octavio"

# Modules

import RPi.GPIO as GPIO
import time
import sys
import os
import subprocess
import signal
import telnetlib
import json
import re
from datetime import datetime
import time
from rpi_ws281x import PixelStrip, Color
from neopixel import *
from threading import Thread

# INIT VAR
snap_server = 'localhost'
macaddr = subprocess.getoutput("cat /sys/class/net/wlan0/address")
snap_port = 1705
status_server = {"id":1,"jsonrpc":"2.0","method":"Server.GetStatus"}
BOUTON = 12
false = False
true = True
list_clients = []
cmd = ["sudo", "service","snapserver","status"]
cmd_music = ["cat", "/proc/asound/card0/pcm0p/sub0/status"]
pause_thread = False

#INIT BUTTON
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
subprocess.call(["sudo","service","snapserver","start"])
subprocess.call(["sudo","hciconfig","hci0","up"])
subprocess.call(["sudo","hciconfig","hci0","piscan"])
subprocess.call(["sudo","service","raspotify","start"])
subprocess.call(["sudo","service","cpiped","start"])
subprocess.call(["sudo","service","snapclient","restart"])
print("\n ***SNAPSERVER STARTED*** \n")

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

#CONNEXION TELNET
try :
    telnet = telnetlib.Telnet('localhost', snap_port)
except:
    print("Telnet Connection Lost")
    ruspopen(["sudo", "python3", "/home/config/bin/scan_octavio.py"])
    GPIO.cleanup()
    quit_thread = True
    sys.exit()

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
    print("\n ---FIN PRGM SERVER--- \n")
    subprocess.call(["sudo","service","snapserver","stop"])
    quit_thread = True
    GPIO.cleanup()
    os._exit(0)

# DEF UPDATE CLIENT

def updateclient():
        global list_clients
        new_list_clients = []
        while new_list_clients == []:
            print('UPDATE CLIENT LIST')
            telnet.write(json.dumps(status_server).encode('ASCII') + b"\r\n")
            time.sleep(3)
            getstatus = telnet.read_very_eager().decode()
            mac_extractor = re.compile('([0-9a-f]{2}(?::[0-9a-f]{2}){5})', re.IGNORECASE)
            new_list_clients = re.findall(mac_extractor, getstatus)
            new_list_clients = list(set(new_list_clients))
        if len(new_list_clients) > len(list_clients) :
            list_clients = new_list_clients
            print("NEW OCTAVIO DETECTED")
            # AJOUT NOUVEAUX CLIENTS AU GROUPE - SERVER ONLY
        id_extractor = re.compile('([a-fA-F0-9]{8}[-][a-fA-F0-9]{4}[-][a-fA-F0-9]{4}[-][a-fA-F0-9]{4}[-][a-fA-F0-9]{12}[-]?)', re.IGNORECASE)
        list_group =  re.findall(id_extractor, getstatus)
        id_group = list_group[0]
        set_group = {"id":3,"jsonrpc":"2.0","method":"Group.SetClients","params":{"clients":list_clients,"id":id_group}}
        telnet.write(json.dumps(set_group).encode('ASCII') + b"\r\n")
        print("GROUP UPDATED")
        print(list_clients)

updateclient()


# CHECK SNAPSERVER STATUS
def checkServer():
#CHECK TIME
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
# CHECK STATUS
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        lastLine_long = (proc.stdout.readlines()[-1]).decode()
        lastLine = lastLine_long[:20]
        time_extractor = re.compile('([0-9]{2}[:][0-9]{2}[:][0-9]{2})', re.IGNORECASE)
        check_time = re.findall(time_extractor, lastLine)
        time = ''.join(check_time)
        time_diff = (datetime.strptime(current_time, '%H:%M:%S') - datetime.strptime(time, '%H:%M:%S')).total_seconds()
        if ("Resource temporarily unavailable" in lastLine) :
             print ("*SERVER BUG - Resource temporarily unavailable*")
             subprocess.call(["sudo", "service", "snapserver", "restart"])
        if ("NewConnection" in lastLine) :
            if time_diff < 15 :
                print('UPDATE LIST DE CLIENTS')
                updateclient()
                print("Time passed since last connection of Octavio Client : ")
                print(time_diff)
checkServer()

# DEF des boutons

def plus(channel):
    global pause_thread
    pause_thread = True
    timebutton = 0
    colorWipe(strip, Color(251,251,251), 0)
    timebutton = 0
    print('MUSIQUE SUR CE CLIENT')
    unmute = {"id":8,"jsonrpc":"2.0","method":"Client.SetVolume","params":{"id":macaddr,"volume":{"muted":false}}}
    telnet.write(json.dumps(unmute).encode('ASCII') + b"\r\n")
    print("Octavio " + macaddr + " actif")
    pause_thread = False
    while GPIO.input(4) == True:
        timebutton = timebutton + 0.1
        time.sleep(0.1)
    if 0 <= timebutton < 2:
        for i in range (len(list_clients)) :
            if (list_clients[i] != macaddr) :
                mute = {"id":8,"jsonrpc":"2.0","method":"Client.SetVolume","params":{"id":list_clients[i],"volume":{"muted":true}}}
                telnet.write(json.dumps(mute).encode('ASCII') + b"\r\n")
                print("Client " + list_clients[i] + " eteint")
    else :
#AJOUT SANS MUTE
        doubletouch()
        print('AJOUT APPAREIL OCTAVIO')
        timebutton = 0

def moins(channel):
    global pause_thread
    pause_thread = True
    colorWipe(strip, Color(0,0,0), 0)
    print('MUTE THIS OCTAVIO')
    mute = {"id":8,"jsonrpc":"2.0","method":"Client.SetVolume","params":{"id":macaddr,"volume":{"muted":true}}}
    telnet.write(json.dumps(mute).encode('ASCII') + b"\r\n")
    print("Octavio " + macaddr + " inactif")
    time.sleep(1)
    pause_thread = False

# EVENT DETECT

GPIO.add_event_detect(12, GPIO.RISING, callback=moins)
GPIO.add_event_detect(4, GPIO.RISING, callback=plus)
thread.start()

# PGME

print ("Lancement Programme MASTER")


signal.signal(signal.SIGINT, signal_handler)

try :
    while True :
        try :
            checkServer()
            time.sleep(10)
        except :
            pass
except KeyboardInterrupt:
    print("FIN PROGRAMME SERVEUR")
    GPIO.cleanup()
    quit_thread = True
    timebutton = 0
