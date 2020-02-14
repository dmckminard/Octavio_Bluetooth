#!/usr/bin/env python3.5

__author__      = "David Minard"
__copyright__   = "Octavio"


######################################
#                                   ##
# Programme client - Janvier 2020  ##
#                                   ##
######################################

################################################
#                      MODULES
################################################

import asyncio
import snapcastExpanded.control
import RPi.GPIO as GPIO
import time
import sys
import os
import subprocess
import signal
from neopixel import *

################################################
#                      INIT
################################################

macaddr = subprocess.getoutput("cat /sys/class/net/wlan0/address")
myIP = subprocess.check_output(["hostname","-I"]).strip().decode()
status_server = {"id":1,"jsonrpc":"2.0","method":"Server.GetStatus"}
false = False
true = True
pause_check_music = False
cmd = ["sudo", "service","snapclient","status"]
cmd_music = ["cat", "/proc/asound/card0/pcm0p/sub0/status"]


################################################
#               INIT BUTTON
################################################

GPIO.setmode(GPIO.BCM)
GPIO.setup(12, GPIO.IN)
GPIO.setup(4, GPIO.IN)


################################################
#               INIT LEDS
################################################

LED_COUNT      = 5
LED_PIN        = 10
LED_FREQ_HZ    = 800000
LED_DMA        = 10
LED_BRIGHTNESS = 255
LED_INVERT     = False
LED_CHANNEL    = 0

strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()


################################################
#               INIT SNAPCLIENT
# --> Stop Spotify, Snapserver, restart snapclient, hide bluetooth
################################################
print("IP : " + myIP)
subprocess.call(["sudo","service","raspotify","stop"])
subprocess.call(["sudo","service","snapserver","stop"])
subprocess.call(["sudo","service","snapclient","restart"])
subprocess.call(["sudo","hciconfig","hci0","down"])
subprocess.call(["sudo","hciconfig","hci0","noscan"])
subprocess.Popen(["sudo","python3","/home/config/bin/callback_client.py"])
print("\n ***SNAPCLIENT STARTED*** \n")


################################################
#             INIT SUBPROCESS DEF
# --> Check des commandes subprocess
################################################

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


################################################
#                   DEF LEDS
################################################
    
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
        
        
################################################
#            DEF CHECK MUSIC FOR LEDS
################################################

def check_music():
        while True:
            if pause_check_music is False:
              procc = subprocess.Popen(cmd_music, stdout=subprocess.PIPE)
              rep = procc.communicate()[0].decode('utf-8')
              if ("RUNNING" in rep) :
                  colorWipe(strip, Color(251,251,251), 0)
              else :
                  colorWipe(strip, Color(0,0,0), 0)
              time.sleep(1)

################################################
#              DEF SIGNAL SIGTERM
################################################

def signal_handler(sig, frame):
    print("\n ---FIN PRGM SERVER--- \n")
    subprocess.call(["sudo","service","snapserver","stop"])
    GPIO.cleanup()
    os._exit(0)

################################################
#              GET IP SERVEUR
################################################

def checkServer():
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    lastLine = (proc.stdout.readlines()[-1]).decode()
    print (lastLine)
    if (("Error in socket shutdown" or "Exception in Controller" or "Started Snapcast client.") in lastLine) :
        print ("*NO SERVER, REBOOTING SNAPCLIENT*")
        GPIO.cleanup()
        ruscall(["python3", "/home/config/bin/scan_octavio.py", "|logger -t octavio"])
        GPIO.cleanup()
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


################################################
#           INIT PYTHON SNAPCAST LOOP
################################################
try :
    loop = asyncio.get_event_loop()
    server = loop.run_until_complete(snapcastExpanded.control.create_server(loop, ipServ))
except:
    print("Snapserver connection lost")
    ruspopen(["sudo", "python3", "/home/config/bin/scan_octavio.py"])
    GPIO.cleanup()
    sys.exit()


################################################
#              DEF DES BOUTONS
################################################

def plus(channel):
    global pause_check_music
    pause_check_music = True
    timebutton = 0
    colorWipe(strip, Color(251,251,251), 0)
    timebutton = 0
    print('MUSIQUE SUR CE CLIENT')
    # UNMUTE THIS OCTAVIO
    try :
        loop.run_until_complete(server.client_volume(macaddr, {'muted': False}))
    except :
        print("SNAPSERVER CONNECTION LOST")
        ruscall(["python3", "/home/config/bin/scan_octavio.py", "|logger -t octavio"])
        GPIO.cleanup()
        sys.exit()
    print("Octavio " + macaddr + " actif")
    pause_check_music = False
    while GPIO.input(4) == True:
        timebutton = timebutton + 0.1
        time.sleep(0.1)
    if 0 <= timebutton < 2:
    # MUTE OTHERS OCTAVIO
        for client in server.clients:
            if client.identifier != macaddr :
                try :
                    loop.run_until_complete(server.client_volume(client.identifier, {'muted': True}))
                except :
                    print("SNAPSERVER CONNECTION LOST")
                    ruscall(["python3", "/home/config/bin/scan_octavio.py", "|logger -t octavio"])
                    GPIO.cleanup()
                    sys.exit()
    else :
    # AJOUT SANS MUTE
        doubletouch()
        print('AJOUT APPAREIL OCTAVIO')
        timebutton = 0
        
def moins(channel):
    global pause_check_music
    pause_check_music = True
    colorWipe(strip, Color(0,0,0), 0)
    print('MUTE THIS OCTAVIO')
    try :
        loop.run_until_complete(server.client_volume(macaddr, {'muted': True}))
    except :
        print("SNAPSERVER CONNECTION LOST")
        ruscall(["python3", "/home/config/bin/scan_octavio.py", "|logger -t octavio"])
        GPIO.cleanup()
        sys.exit()
    print("Octavio " + macaddr + " inactif")
    time.sleep(1)
    pause_check_music = False

################################################
#                 EVENT DETECT
################################################

GPIO.add_event_detect(12, GPIO.RISING, callback=moins)
GPIO.add_event_detect(4, GPIO.RISING, callback=plus)

################################################
#              LOOP FOR CLIENT
################################################
print('################################')
print('################################')
print('# LANCEMENT PROGRAMME CLIENT #')
print('################################')
print('################################')

while True :
    check_music()
