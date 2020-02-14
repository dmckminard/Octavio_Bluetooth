#Modules

import RPi.GPIO as GPIO
import time
import subprocess
import sys
import os
import threading
import time
from neopixel import *
from threading import Thread

# Init
GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.IN)
res = subprocess.call(["ping", "8.8.8.8", "-c1", "-W2", "-q"])
myIP = subprocess.check_output(["hostname","-I"]).strip().decode()
print("-- BOOT : " + myIP + " --")
subprocess.Popen(["sudo", "service", "cpiped", "stop"])
subprocess.Popen(["sudo", "service", "raspotify", "stop"])
subprocess.Popen(["sudo","hciconfig","hci0","down"])
subprocess.call(["sudo", "service", "snapclient", "restart"])
stopWaiting = False
cmd = ["sudo", "service","snapclient","status"]
quit_thread = False
quit_thread_boot = False

#INIT LED

LED_COUNT      = 5
LED_PIN        = 10
LED_FREQ_HZ    = 800000
LED_DMA        = 10
LED_BRIGHTNESS = 255
LED_INVERT     = False
LED_CHANNEL    = 0

strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

# DEF FONCTIONS LEDS

def colorWipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms/10000.0)

def connected():
#             m.join()
             colorWipe(strip, Color(0, 0, 0))
             time.sleep(0.2)
             strip.setPixelColor(2, Color(0,25,0))
             strip.show()
             time.sleep(0.1)
             strip.setPixelColor(2, Color(0,251,0))
             strip.show()
             time.sleep(0.1)
             strip.setPixelColor(1, Color(0,25,0))
             strip.setPixelColor(3, Color(0,25,0))
             strip.show()
             time.sleep(0.1)
             strip.setPixelColor(1, Color(0,251,0))
             strip.setPixelColor(3, Color(0,251,0))
             strip.show()
             time.sleep(0.1)
             strip.setPixelColor(0, Color(0,25,0))
             strip.setPixelColor(4, Color(0,25,0))
             strip.show()
             time.sleep(0.1)
             strip.setPixelColor(0, Color(0,251,0))
             strip.setPixelColor(4, Color(0,251,0))
             strip.show()
             time.sleep(0.1)
             colorWipe(strip, Color(0, 0, 0))

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

#THREAD LEDS

class leds (Thread):
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
          global quit_thread_boot
          if quit_thread_boot :
              break

#Attente de la co d'un server
if res != 0 :
  print('PAS INTERNET')
while (res != 0):
      res = subprocess.call(["ping", "8.8.8.8", "-c1", "-W2", "-q"])
      time.sleep(3)
else:
    print('INTERNET OK')
    m = leds()
    m.daemon = True
    m.start()
    while(not stopWaiting) :
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        lastLine = (proc.stdout.readlines()[-1]).decode()

        print (lastLine)
        if (("Started Snapcast client.") in lastLine) :
            print ("*No server, keep searching*")
            subprocess.call(["sudo", "service", "snapclient", "restart"])
        elif ("Connected to" in lastLine) :
            print("*Server detected*")
            quit_thread_boot = True
            connected()
            ruspopen(["python3", "/home/config/bin/client.py", "|logger -t octavio"])
            print("Fermeture wait_server.py")
            GPIO.cleanup()
            sys.exit(0)

        else :
            subprocess.call(["sudo", "service", "snapclient", "restart"])
        print("\n")

