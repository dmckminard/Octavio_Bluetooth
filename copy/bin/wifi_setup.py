# coding: utf-8

import os
import subprocess
import time
import sys
from neopixel import *
from threading import Thread

#INIT
subprocess.call(["sudo","hciconfig","hci0","down"])
res = subprocess.call(["ping", "8.8.8.8", "-c1", "-W2", "-q"])
quit_thread_wifi = False
ap_ready = False
cmd = ["sh", "/home/config/bin/look_snapserver.sh"]

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

#DEF RUSPOPEN

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
class nowifi (Thread):
    def __init__(self):
        Thread.__init__(self)

    def run(self):
      while quit_thread_wifi == False:
        for a in range (16):
            colorWipe(strip, Color(a*16,a*16,a*16))
            strip.show()
        for b in reversed(range (16)):
            colorWipe(strip, Color(b*16,b*16,b*16))
            strip.show()
        time.sleep(0.5)
        if quit_thread_wifi == True:
            break

def colorWipe(strip, color, wait_ms=50):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms/10000.0)

def connected():
             colorWipe(strip, Color(0, 0, 0))
             time.sleep(0.2)
             strip.setPixelColor(2, Color(0,25,0))
             strip.show()
             time.sleep(0.1)
             strip.setPixelColor(2, Color(26,251,26))
             strip.show()
             time.sleep(0.1)
             strip.setPixelColor(1, Color(0,25,0))
             strip.setPixelColor(3, Color(0,25,0))
             strip.show()
             time.sleep(0.1)
             strip.setPixelColor(1, Color(26,251,26))
             strip.setPixelColor(3, Color(26,251,26))
             strip.show()
             time.sleep(0.1)
             strip.setPixelColor(0, Color(0,25,0))
             strip.setPixelColor(4, Color(0,25,0))
             strip.show()
             time.sleep(0.1)
             strip.setPixelColor(0, Color(26,251,26))
             strip.setPixelColor(4, Color(26,251,26))
             strip.show()
             time.sleep(0.1)
             colorWipe(strip, Color(0, 0, 0))

#PROGRAMME
if res!= 0: #YA PAS INTERNET
                    print('START AP CONFIGURATION')
                    os.chdir('/home/config/bin')
                    os.system('docker run -d --privileged --net host -v $(pwd)/wificfg.json:/cfg/wificfg.json -v /etc/wpa_supplicant/:/etc/wpa_supplicant cjimti/iotwifi')
                    time.sleep(30)
                    m = nowifi()
                    m.daemon = True
                    m.start()
                    while (res != 0):
                            res = subprocess.call(["ping", "8.8.8.8", "-c1", "-W2", "-q"])
                            time.sleep(0.1)
                    print('WAITING WIFI TO SETUP')
                    time.sleep(5)
                    subprocess.call(["sudo", "killall", "hostapd"])
                    subprocess.call(["sudo", "ifconfig", "uap0", "down"])
                    quit_thread_wifi = True
                    m.join()
                    connected()
                    subprocess.Popen(["python3", "/home/config/cgi/cgiserver.py", "|logger -t octavio"], cwd="/home/config/cgi")
                    subprocess.Popen(cmd)
                    sys.exit(0)

else: #YA INTERNET
            print ("Network OK, Start")
            connected()
            subprocess.Popen(["python3", "/home/config/cgi/cgiserver.py", "|logger -t octavio"], cwd="/home/config/cgi")
            subprocess.Popen(cmd)
            sys.exit(0)


