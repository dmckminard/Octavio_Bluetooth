#!/usr/bin/env python3.5

__author__      = "David Minard"
__copyright__   = "Octavio"

###########################################################################
#                                                                        ##
# Programme Notifications Rename / Leds changment stream - Janvier 2020  ##
#                                                                        ##
###########################################################################

################################################
#                      MODULES
################################################

import time
import asyncio
import snapcastExpanded.control
import subprocess
import RPi.GPIO as GPIO
from neopixel import *
import sys

macaddr = subprocess.getoutput("cat /sys/class/net/wlan0/address")

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
#                   DEF LEDS
################################################

def colorWipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms/10000.0)

################################################
#           INIT PYTHON SNAPCAST LOOP
################################################
try :
    loop = asyncio.get_event_loop()
    server = loop.run_until_complete(snapcastExpanded.control.create_server(loop, 'localhost'))
except:
    print("Snapserver connection lost")
    colorWipe(strip, Color(0,0,0), 0)
    GPIO.cleanup()
    sys.exit()

################################################
#             INIT NOTIFICATIONS
################################################

#############################
# --> SNAPSERVER DECONNECTED
#############################

def disc(exception):
    print("disconnect",str(exception))
    print('QUIT NOTIF PGME')
    GPIO.cleanup()
    sys.exit()

#############################
# --> NOUVEL APPAREIL OCTAVIO
#############################
# On ajoute l'appareil au groupe du serveur
# A MODIFIER
def conn():
    print("NEW CLIENT DETECTED, ADDING TO GROUP")
    
####################
# --> OCTAVIO RENAME
####################
# On rename aussi le nom sur AirPlay et le nom bluetooth (via hostname debian)
def name():
    print("OCTAVIO HAS BEEN RENAMED")
    for client in server.clients:
        if client.identifier == macaddr :
            new_name = client.friendly_name
            hostname = "PRETTY_HOSTNAME=" + new_name
            name_airplay = "\"" +  new_name + "\""
            airplay = "general = {name = "+ name_airplay +" };"


            # HOSTNAME BLUETOOTH - ON LE FAIT PAS POUR EVITER DES CONFUSIONS POUR LE CLIENT
#            fichier = open("/etc/machine-info", "w")
#            fichier.write(hostname)
#            fichier.close()
#            subprocess.call(["sudo", "service", "bluetooth", "restart"])
            # AIRPLAY
            lines = open("/usr/local/etc/shairport-sync.conf").read().splitlines()
            lines[-1] = airplay
            open('/usr/local/etc/shairport-sync.conf','w').write('\n'.join(lines))
#            lines.close()
            subprocess.call(["sudo", "service", "shairport-sync", "restart"])
            print('NAME FOR BLUETOOTH AND AIRPLAY CHANGED')

############################
# --> OCTAVIO STREAM CHANGED
############################
# On indique via les leds le nouveau stream
def change():
    print("THE STREAM HAS CHANGED")
    for client in server.clients:
        if client.identifier == macaddr :
        # Check stream used by this Octavio
            actual_stream_line = str(client.group)
            if "Bluetooth" in actual_stream_line :
                print(' STREAM BLUETOOTH ')
                colorWipe(strip, Color(0,0,251), 0) #BLUE FOR BLUETOOTH
                time.sleep(0.5)
                colorWipe(strip, Color(0,0,0), 0)
            if "Spotify" in actual_stream_line :
                print(' STREAM SPOTIFY ')
                colorWipe(strip, Color(0,251,0), 0) #GREEN FOR SPOTIFY
                time.sleep(0.5)
                colorWipe(strip, Color(0,0,0), 0)
            if "Jack" in actual_stream_line :
                print(' STREAM JACK')
                colorWipe(strip, Color(251,0,0), 0) #RED FOR JACK
                time.sleep(0.5)
                colorWipe(strip, Color(0,0,0), 0)

def update():
    pass

###########################
# FONCTIONS GESTION SERVEUR
###########################
server.set_on_disconnect_callback(disc)
server.set_client_connect_callback(conn)
server.set_client_name_changed_callback(name)
server.set_stream_change_callback(change)
server.set_stream_update_callback(update)


print('STARTING NOTIFICATIONS PROGRAM')
loop.run_forever()
