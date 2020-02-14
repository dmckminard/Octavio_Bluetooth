#!/usr/bin/env python3.6

__author__      = "David Minard"
__copyright__   = "Octavio"


######################################
#                                   ##
# Programme serveur - Janvier 2020  ##
#                                   ##
######################################

################################################
#                      MODULES
################################################

import nest_asyncio
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
status_server = {"id":1,"jsonrpc":"2.0","method":"Server.GetStatus"}
false = False
true = True
pause_check_music = False
cmd = ["sudo", "service","snapserver","status"]
cmd_music = ["cat", "/proc/asound/card0/pcm0p/sub0/status"]
cmd_client = ["sudo", "service","snapclient","status"]

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
#               INIT SNAPSERVER
# --> Lancement bluetooth, spotify, cpiped et restart snapclient
################################################

subprocess.call(["sudo","service","snapserver","start"])
subprocess.Popen(["sudo","python3","/home/config/bin/callback_server.py"])
subprocess.call(["sudo","hciconfig","hci0","up"])
subprocess.call(["sudo","hciconfig","hci0","piscan"])
subprocess.call(["sudo","service","raspotify","start"])
subprocess.call(["sudo","service","cpiped","start"])
subprocess.call(["sudo","service","snapclient","restart"])
print("\n ***SNAPSERVER STARTED*** \n")


################################################
#               CHECK DUPLICATE
# --> Check si il y n'y a pas d'autre snapserveur sur le reseau
################################################

check_another_server = subprocess.check_output(['avahi-browse', '-atl'])
if 'Snapcast  ' in str(check_another_server) :
    print("ALERT - THERE IS ANOTHER SNAPSERVER IN THE NETWORK")
    print("TRYING TO CONNECT TO SERVER")
    subprocess.call(["sudo","pkill","-9","-f","callback_server.py"])
    subprocess.call(["sudo", "service", "snapserver", "stop"])
    while True :
        proc = subprocess.Popen(cmd_client, stdout=subprocess.PIPE)
        lastLine = (proc.stdout.readlines()[-1]).decode()
        print(lastLine)
        if ("Connected to" in lastLine) :
            print("*Server detected*")
            subprocess.Popen(["python3", "/home/config/bin/client.py", "|logger -t octavio"])
            print("Fermeture server.py")
            GPIO.cleanup()
            sys.exit(0)

        else :
            print ("*No server, keep searching*")
            subprocess.call(["sudo", "service", "snapclient", "restart"])
            time.sleep(1)
    print("\n")
else :
    print('CHECK FOR ANOTHER SERVER IS OK')

################################################
#           INIT PYTHON SNAPCAST LOOP
################################################
try :
    loop = asyncio.get_event_loop()
    server = loop.run_until_complete(snapcastExpanded.control.create_server(loop, 'localhost'))

except:
    print("Snapserver connection lost")
    ruspopen(["sudo", "python3", "/home/config/bin/scan_octavio.py"])
    GPIO.cleanup()
    sys.exit()
    
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
    for client in server.clients:
        loop.run_until_complete(server.client_volume(macaddr, {'muted': False}))
        print("Octavio " + macaddr + " actif")
        pause_check_music = False
    while GPIO.input(4) == True:
        timebutton = timebutton + 0.1
        time.sleep(0.1)
    if 0 <= timebutton < 2:
    # MUTE OTHERS OCTAVIO
        for client in server.clients:
            if client.identifier != macaddr :
                loop.run_until_complete(server.client_volume(client.identifier, {'muted': True}))
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
    for client in server.clients:
        loop.run_until_complete(server.client_volume(macaddr, {'muted': True}))
    print("Octavio " + macaddr + " inactif")
    pause_check_music = False

################################################
#                 EVENT DETECT
################################################

GPIO.add_event_detect(12, GPIO.RISING, callback=moins)
GPIO.add_event_detect(4, GPIO.RISING, callback=plus)

################################################
#              LOOP FOR SERVEUR
################################################
print('################################')
print('################################')
print('# LANCEMENT PROGRAMME SERVEUR #')
print('################################')
print('################################')
while True :
    check_music()
