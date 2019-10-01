import asyncio
import time
import random
'''
import t_sensor
try:
    import RPi.GPIO as GPIO
except:
    import dummyGPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(17, GPIO.OUT)
GPIO.setup(27, GPIO.OUT)
'''

async def do_pump(pump_type: str, seconds: int):
    if pump_type == 'co2':
        print('co2 pump ran')
    elif pump_type == 'water':
        return
    elif pump_type == 'fertilizer':
        return


async def temp():
    # temp_c, temp_f = t_sensor.read_temp()
    # So we would have to make sure that we don't do read_temp more than once every 2 seconds
    t = random.randint(1, 40)
    return t

