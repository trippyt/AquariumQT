import asyncio
from time import sleep
import time
import random
import threading
import routes
import t_sensor
import json
import os
try:
    import RPi.GPIO as GPIO
except:
    import dummyGPIO as GPIO
Co2_pump = 17 # Initializing the GPIO pin 17 for Dosage pump
Fertilizer_pump = 27 # Initializing the GPIO pin 27 for Dosage pump
led_pin = 12  # Initializing the GPIO pin 12 for LED
Button = 16  # Initializing the GPIO pin 16 for Button
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(Co2_pump, GPIO.OUT) # Co2 Pump
GPIO.setup(Fertilizer_pump, GPIO.OUT) # Fertilizer Pump
GPIO.setup(Button, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Setup Button
GPIO.setup(led_pin, GPIO.OUT)  # Notification LED pin
pwm = GPIO.PWM(led_pin, 100)  # Created a PWM object
pwm.start(0)  # Started PWM at 0% duty cycle
#flag = 0
FLASH = 0
PULSE = 1
led_pulse_loop = True
cal_stop_signal = False
cal_time = None

class ThreadKilled (Exception):
   pass

temperature_data = {
    "Temperature Data": {},
}
conversion_values = {
            "tank_size": {},
            "co2_amount": {},
            "co2_to_water": {},
            "fertz_amount": {},
            "fertz_to_water": {},
            "conditioner_amount": {},
            "conditioner_to_water": {},
            "co2_dosage": {},
            "fertz_dosage": {},
            "conditioner_dosage": {},
        }
conversion_data = {
            "Tank Size": {},
            "Co2 Ratio": {},
            "Fertilizer Ratio": {},
            "Water Conditioner Ratio": {},
        }
schedule_data = {
            "Co2 Schedule Data": {},
            "Fertilizer Schedule Data": {},
            "Tap Schedule Data": {},
            "Water Cycle Schedule Data": {}
        }
calibration_data = {
            "Co2 Calibration Data": {},
            "Fertilizer Calibration Data": {},
            "Water Conditioner Calibration Data": {},
        }

light_hour_data = {
            "Mode Hours": {},
        }

def load():
    if os.path.isfile('data.txt'):
        with open('data.txt', 'r') as json_file:
            data = json.loads(json_file.read())
            return data

def save():
    data = {
        #"Conversion Data": conversion_data,
        #"Schedule Data": schedule_data,
        "Calibration Data": calibration_data,
        "Temperature Data": temperature_data,
        #"Light Hour Data": light_hour_data
    }
    with open('data.txt', 'w') as json_file:
        json_file.write(json.dumps(data, indent=4))
    print("Settings Updated")

def alert_data(ht: int, lt: int):
        print("New Alert Set")
        print(f"High Temperature: {ht}")
        print(f"Low Temperature: {lt}")
        temperature_data.update(
            {
                "High Temp": ht,
                "Low Temp": lt
            }
        )
        save()

async def do_pump(pump_type: str, seconds: int):
    if pump_type == 'co2':
        print("Running co2")
        GPIO.output(Co2_pump, 1)
    elif pump_type == 'conditioner':
        return
    elif pump_type == 'fertilizer':
        print("Running fertz")
        GPIO.output(Fertilizer_pump, 1)
    await asyncio.sleep(int(seconds))
    GPIO.output(Co2_pump, 0)
    GPIO.output(Fertilizer_pump, 0)
    return

async def stop_pump(pump_type: str):
    if pump_type == 'co2':
        print("Stopping co2")
        GPIO.output(Co2_pump, 0)
    elif pump_type == 'conditioner':
        return
    elif pump_type == 'fertilizer':
        print("Stopping fertz")
        GPIO.output(Fertilizer_pump, 0)
    return

def led_pulse_worker(option):
    '''worker function for led pulse thread'''
    global led_pulse_loop
    if option == FLASH:
        sleep_time = 0.0001
    else: # PULSE
        sleep_time = 0.01

    while led_pulse_loop:
        for x in range(100):  # This Loop will run 100; times 0 to 100
            pwm.ChangeDutyCycle(x)  # Change duty cycle
            sleep(sleep_time)  # Delay of 10mS
        for x in range(100, 0, -1):  # Loop will run 100 times; 100 to 0
            pwm.ChangeDutyCycle(x)
            sleep(sleep_time)

    pwm.ChangeDutyCycle(0)
    # once signal to stop is received, reset flag to True
    led_pulse_loop = True

def led_pulse(option):
    pulse_thread = threading.Thread(target=led_pulse_worker, args=(option,))
    pulse_thread.start()

def stop_led_pulse():
    global led_pulse_loop
    led_pulse_loop = False

def btn_pressed():
    while GPIO.input(Button):
        sleep(0.1)
        if cal_stop_signal:
            raise ThreadKilled()
    while not GPIO.input(Button):
        sleep(0.1)
        if cal_stop_signal:
            raise ThreadKilled()

def stop_cal():
    global cal_stop_signal
    cal_stop_signal = True
    stop_led_pulse()

def start_calibration(pump_type: str):
    try:
        global cal_stop_signal
        global cal_time
        cal_time = None
        cal_stop_signal = False
        led_pulse(PULSE)
        btn_pressed()
        if pump_type == 'co2':
            print("Running co2")
            print("Co2                      Calibration started.")
            led_pulse(FLASH)
            start = time.time()
            GPIO.output(Co2_pump, 1)
            btn_pressed()
            print("Stopping co2")
            print("Co2                      Calibration finished.")
            stop_led_pulse()
            end = time.time()
            GPIO.output(Co2_pump, 0)
            cal_time = round(end - start, 2)
            print(cal_time)
            calibration_data["Co2 Calibration Data"].update(
                {
                    "Time": round(cal_time, 2)
                }
            )
            save()
    except ThreadKilled:
        print('calibration was cancelled!')
        stop_led_pulse()

async def temp():
    temp_c, temp_f = t_sensor.read_temp()
    # So we would have to make sure that we don't do read_temp more than once every 2 seconds
    # t = random.randint(1, 40)
    #return temp_c, temp_f
    return round(temp_c, 2)


# if button is pressed at anytime before the gui calibration button it will do nothing
# client gui calibration button pressed (enters calibration mode)
# sends calibration request with the dosage type to the server
# server then starts pulsing the led, and waits for the physical button to be pushed
# if the clients gui button gets pressed then cancel and turn off led
# if the physical button is pushed then start the timer and pump and make the led flash quickly
# once the user has measured 10ml press the physical button again the pump and timer stop and the led turns off
# server then saves the elapsed time for that dose calibration, and sends it to the gui to display (exits calibration mode)
# from this point the led is off and the button will be inactive again just like in the beginning