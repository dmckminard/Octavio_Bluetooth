#!/usr/bin/env python3.5

__author__      = "David Minard"
__copyright__   = "Octavio"

###########################################################################
#                                                                        ##
# Programme Notifications Rename / Leds changment stream - Janvier 2020  ##
#                             SERVER                                     ##
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
selected_stream = 'None'

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
# --> VOLUME CHANGED
# NEED TO PLAY BLUETOOTH
#############################

def mute():
    print('CLIENT IS MUTED')
    #CHECK IS THERE IS A CLIENT NOT MUTED
    client_alive = False
    for client in server.clients:
        if client.muted == False :
            print ('THERE IS A CLIENT ALIVE')
            client_alive = True
            break
    if client_alive == False :
        print ('NO CLIENT SEEMS ALIVE, PAUSE BLUETOOTH')
        subprocess.Popen(["python", "/home/config/bin/play_pause_control/pause_bluetooth.py"])

def unmute():
    global selected_stream
    print('CLIENT IS UN-MUTED')
    if selected_stream == 'Bluetooth' :
        print ('SET PLAY ON BLUETOOTH')
        subprocess.Popen(["python", "/home/config/bin/play_pause_control/play_bluetooth.py"])
    else :
        pass

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
    subprocess.call(["sudo", "python3", "/home/config/bin/server_add_client.py"])

####################
# --> OCTAVIO RENAME
####################
# On rename aussi le nom sur AirPlay et le nom bluetooth (via hostname debian)
def name():
    print("OCTAVIO HAS BEEN RENAMED")
    for client in server.clients:
        if client.identifier == macaddr :
            new_name = client.friendly_name
            hostname = "PRETTY_HOSTNAME= Octavio " + new_name
            name_airplay = "\"" +  new_name + "\""
            airplay = "general = {name = "+ name_airplay +" };"
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
    global selected_stream
    print("THE STREAM HAS CHANGED")
    for client in server.clients:
        if client.identifier == macaddr :
        # Check stream used by this Octavio
            actual_stream_line = str(client.group)
            if "Bluetooth" in actual_stream_line :
                selected_stream = 'Bluetooth'
                print(' STREAM BLUETOOTH ')
                colorWipe(strip, Color(0,0,51), 0) #BLUE FOR BLUETOOTH
                time.sleep(0.5)
                colorWipe(strip, Color(0,0,0), 0)
            if "Spotify" in actual_stream_line :
                selected_stream = 'Spotify'
                print(' STREAM SPOTIFY ')
                colorWipe(strip, Color(51,0,0), 0) #GREEN FOR SPOTIFY
                time.sleep(0.5)
                colorWipe(strip, Color(0,0,0), 0)
            if "Jack" in actual_stream_line :
                print(' STREAM JACK')
                colorWipe(strip, Color(0,51,0), 0) #RED FOR JACK
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
server.set_client_mute_changed_callback(mute)
server.set_client_unmute_changed_callback(unmute)

print ('STARTING NOTIFICATIONS PROGRAM')

change()

loop.run_forever()
