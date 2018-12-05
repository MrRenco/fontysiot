from network import LoRa
import socket
import ubinascii
import struct
import machine
import math
import os
import time
import utime
import gc
import pycom
from machine import RTC
from machine import SD
from L76GNSS import L76GNSS
from pytrack import Pytrack
from LIS2HH12 import LIS2HH12

# Initialise LoRa in LORAWAN mode.
# Please pick the region that matches where you are using the device:
# Asia = LoRa.AS923
# Australia = LoRa.AU915
# Europe = LoRa.EU868
# United States = LoRa.US915
lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868)

# create an ABP authentication params
dev_addr = struct.unpack(">l", ubinascii.unhexlify('26011196'))[0]
nwk_swkey = ubinascii.unhexlify('5FEE91FAE5C63D17DC1FE98ED3D16DFD')
app_swkey = ubinascii.unhexlify('9072E58B8FC9B9622C76BE85F6E21440')

# join a network using ABP (Activation By Personalization)
lora.join(activation=LoRa.ABP, auth=(dev_addr, nwk_swkey, app_swkey))

# create a LoRa socket
s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

# set the LoRaWAN data rate
s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)

# make the socket blocking
# (waits for the data to be sent and for the 2 receive windows to expire)
s.setblocking(True)

gc.enable()
# deactivate heartbeat
pycom.heartbeat(False)
# setup rtc
rtc = machine.RTC()
rtc.ntp_sync("pool.ntp.org")
utime.sleep_ms(750)
print('\nRTC Set from NTP to UTC:', rtc.now())
utime.timezone(7200)
print('Adjusted from UTC to EST timezone', utime.localtime(), '\n')

# setup GPS
py = Pytrack()
l76 = L76GNSS(py, timeout=30)

# display the reset reason code and the sleep remaining in seconds
# possible values of wakeup reason are:
# WAKE_REASON_ACCELEROMETER = 1
# WAKE_REASON_PUSH_BUTTON = 2
# WAKE_REASON_TIMER = 4
# WAKE_REASON_INT_PIN = 8
print("Wakeup reason: " + str(py.get_wake_reason()) + "; Aproximate sleep remaining: " + str(py.get_sleep_remaining()) + " sec")
time.sleep(0.5)

# enable wakeup source from INT pin
py.setup_int_pin_wake_up(False)

# enable activity and also inactivity interrupts, using the default callback handler
py.setup_int_wake_up(True, True)

acc = LIS2HH12()
# enable the activity/inactivity interrupts
# set the accelereation threshold to 2000mG (2G) and the min duration to 200ms
acc.enable_activity_interrupt(1500, 160)

# check if we were awaken due to activity
if acc.activity():
    pycom.rgbled(0xFF0000)
    coord = l76.coordinates()
    #f.write("{} - {}\n".format(coord, rtc.now()))

    print("{} - {} - {}".format(coord, rtc.now(), gc.mem_free()))
    print("ACTIVITY!")
    s.send(bytes([0x01, 0x02, 0x03]))
    s.setblocking(False)
else:
    pycom.rgbled(0x00FF00)  # timer wake-up

# go to sleep for 5 minutes maximum if no accelerometer interrupt happens
py.setup_sleep(20)
py.go_to_sleep()
# send some data


# make the socket non-blocking
# (because if there's no data received it will block forever...)
# s.setblocking(False)

# get any data received (if any...)
# data = s.recv(64)
# print(data)
