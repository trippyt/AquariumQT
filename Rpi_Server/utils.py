import asyncio
import time
import random

import t_sensor
try:
    import RPi.GPIO as GPIO
except:
    import dummyGPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(17, GPIO.OUT) # Co2 Pump
GPIO.setup(27, GPIO.OUT) # Fertilizer Pump

calibration_started = False


async def do_pump(pump_type: str, seconds: int):
    if pump_type == 'co2':
        print("Running co2")
        GPIO.output(17, 1)
    elif pump_type == 'conditioner':
        return
    elif pump_type == 'fertilizer':
        print("Running fertz")
        GPIO.output(27, 1)
    await asyncio.sleep(int(seconds))
    GPIO.output(17, 0)
    GPIO.output(27, 0)
    return


async def stop_pump(pump_type: str):
    if pump_type == 'co2':
        print("Stopping co2")
        GPIO.output(17, 0)
    elif pump_type == 'conditioner':
        return
    elif pump_type == 'fertilizer':
        print("Stopping fertz")
        GPIO.output(27, 0)
    return




async def temp():
    temp_c, temp_f = t_sensor.read_temp()
    # So we would have to make sure that we don't do read_temp more than once every 2 seconds
    # t = random.randint(1, 40)
    #return temp_c, temp_f
    return round(temp_c, 2)
