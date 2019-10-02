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
GPIO.setup(17, GPIO.OUT)
GPIO.setup(27, GPIO.OUT)

prev_time = ''
calibration_started = False


async def do_pump(pump_type: str, seconds: int):
    if pump_type == 'co2':
        print('co2 pump ran')
    elif pump_type == 'water':
        return
    elif pump_type == 'fertilizer':
        return

async def do_calibration_pump(pump_type: str):
    calibration_started = not calibration_started
    if pump_type == 'co2':
        print('co2 pump ran')
    elif pump_type == 'water':
        return
    elif pump_type == 'fertilizer':
        return

    if calibration_started:
        prev_time = time.time()
        GPIO.output(17, 1)
        #self.log.info("Co2                      Calibration started.")
    else:
        elapsed_time = time.time() - prev_time
        #self.form.co2_dosing_lcd.setProperty('value', round(co2_elapsed_time, 2))
        GPIO.output(17, 0)
        #self.log.info(f"Co2                      Calibration stopped.
        return elapsed_time




async def temp():
    temp_c, temp_f = t_sensor.read_temp()
    # So we would have to make sure that we don't do read_temp more than once every 2 seconds
    # t = random.randint(1, 40)
    #return temp_c, temp_f
    return round(temp_c, 2)
