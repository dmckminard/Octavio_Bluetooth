# coding: utf-8

import os
import subprocess
import time
import sys
from rpi_ws281x import PixelStrip, Color
from neopixel import *
from threading import Thread


#WAIT FOR INTERNET
time.sleep(10)
#INIT
subprocess.call(["aplay","/home/config/start_sound.wav"])
subprocess.call(["sudo","hciconfig","hci0","down"])
res = subprocess.call(["ping", "8.8.8.8", "-c1", "-W2", "-q"])
quit_thread_wifi = False

#INIT LED

LED_COUNT      = 5
LED_PIN        = 10
LED_FREQ_HZ    = 800000
LED_DMA        = 10
LED_BRIGHTNESS = 255
LED_INVERT     = False
LED_CHANNEL    = 0

strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

#DEF LEDS
class nowifi (Thread):
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        while True:
          for j in range(1):
            for q in reversed(range(6)):
                for i in range(strip.numPixels()):
                    strip.setPixelColor(i+q, Color(251,251,251))
                strip.show()
                time.sleep(0.3)
                for i in range(strip.numPixels()):
                    strip.setPixelColor(i+q, Color(0,0,0,0))
 #         time.sleep(0.1)
          global quit_thread_wifi
          if quit_thread_wifi :
              break

#DEF SUBPROCESS

def ruspopen(command_ruspopen):
    result = 0
    while result == 0:
        try:
            subprocess.Popen(command_ruspopen)
            result = 1
        except:
            pass

#PROGRAMME
if res!= 0: #YA PAS INTERNET
            subprocess.Popen(["sudo", "wifi-connect", "-o", "8080", "-d", "10.0.0.1,10.0.0.254", "-g", "10.0.0.1", "-s", "Octavio Setup"])
            m = nowifi()
            m.daemon = True
            m.start()
            while (res != 0):
                res = subprocess.call(["ping", "8.8.8.8", "-c1", "-W2", "-q"])
                time.sleep(0.1)
            ruscall(["sudo", "killall", "wifi-connect"])
            quit_thread_wifi = True
            m.join()
            subprocess.Popen(["python3", "/home/config/cgi/cgiserver.py", "|logger -t octavio"], cwd="/home/config/cgi")
            ruspopen(["python3", "/home/config/bin/boot.py", "|logger -t octavio"])
            sys.exit(0)

else: #YA INTERNET
            print ("Network OK, Start")
            subprocess.Popen(["python3", "/home/config/cgi/cgiserver.py", "|logger -t octavio"], cwd="/home/config/cgi")
            ruspopen(["python3", "/home/config/bin/boot.py", "|logger -t octavio"])
            sys.exit(0)
