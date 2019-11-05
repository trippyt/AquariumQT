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
    "Temperature Alert": {},
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
dosage_data = {
    "Co2 Data": {},
    "Fertilizer Data": {},
    "Water Conditioner Data": {},
        }

    #"Co2 Runtime": {},
    #"Fertilizer Dosage": {},
    #"Fertilizer Runtime": {},
    #"Water Conditioner Dosage": {},
    #"Water Conditioner Runtime": {},

def load():
    if os.path.isfile('data.txt'):
        with open('data.txt', 'r') as json_file:
            data = json.loads(json_file.read())
            print(data)
            return data

def save():
    global temperature_data
    global calibration_data
    global conversion_data
    global dosage_data
    data = {
        "Conversion Data": conversion_data,
        #"Schedule Data": schedule_data,
        "Calibration Data": calibration_data,
        "Temperature Data": temperature_data,
        "Dosage Data": dosage_data,
        #"Light Hour Data": light_hour_data
    }
    with open('data.txt', 'w') as json_file:
        json_file.write(json.dumps(data, indent=4))
    print("Settings Updated")
#co2_dose: int, co2_runtime: int, fertz_dose: int, fertz_runtime: int, conditioner_dose: int, conditioner_runtime: int
def set_dosage_data():
    global dosage_data
    global calibration_data
    global conversion_data

    co2_dose = round(float(conversion_data["Co2 Ratio"]["Co2 Dosage"]), 2)
    print(f"Co2 Dosage: {co2_dose}")
    co2_per_ml = float(calibration_data["Co2 Calibration Data"]["Time per 1mL"])
    print(co2_per_ml)
    co2_runtime = co2_dose*co2_per_ml
    print(co2_runtime)
    #fertz_dose =
    #fertz_runtime =
    #conditioner_dose =
    #conditioner_runtime =
    dosage_data["Co2 Data"].update(
        {
            "Runtime": co2_runtime,
        }
    )
    save()

def conversions(tank: int, co2_ml: int, co2_water: int, co2_split_dose: int, fertz_ml: int, fertz_water: int, conditioner_ml: int, conditioner_water: int):
    print("===INSIDE UTILS===")
    global conversion_data
    global dosage_data
    tank = float(tank)
    co2_ml = float(co2_ml)
    co2_water = float(co2_water)
    co2_split_dose = float(co2_split_dose)
    fertz_ml = float(fertz_ml)
    fertz_water = float(fertz_water)
    conditioner_ml = float(conditioner_ml)
    conditioner_water = float(conditioner_water)

    conversion_data["Tank Size"].update(
        {
            "Water Volume": tank
        }
    )
    x = co2_ml*tank/co2_water
    co2_dosage = round(x, 2)
    conversion_data["Co2 Ratio"].update(
        {
            "Co2 Amount": co2_ml,
            "Co2 to Water": co2_water,
            "Co2 Dosage": co2_dosage,
            "Co2 Times a Day": co2_split_dose,
        }
    )
    dosage_data["Co2 Data"].update(
        {
            "Dosage": co2_dosage,
        }
    )
    y = (fertz_ml*tank)/fertz_water
    fertz_dosage = round(y, 2)
    conversion_data["Fertilizer Ratio"].update(
        {
            "Fertilizer Amount": fertz_ml,
            "Fertilizer to Water": fertz_water,
            "Fertilizer Dosage": fertz_dosage
        }
    )
    dosage_data["Fertilizer Data"].update(
        {
            "Dosage": fertz_dosage,
        }
    )
    y = (conditioner_ml*tank)/conditioner_water
    conditioner_dosage = round(y, 2)
    conversion_data["Water Conditioner Ratio"].update(
        {
            "Conditioner Amount": conditioner_ml,
            "Conditioner to Water": conditioner_water,
            "Conditioner Dosage": conditioner_dosage
        }
    )
    dosage_data["Water Conditioner Data"].update(
        {
            "Dosage": conditioner_dosage,
        }
    )
    set_co2_runtime()
    #set_dosage_data()
    print("Updating Conversion Data From the Client")
    print(f"New Tank Size Set: {tank}")
    print(f"New Co2 Conversion Set:{co2_ml}, {co2_water}, {co2_dosage}")
    print(f"New Fertilizer Conversion Set:{fertz_ml}, {fertz_water}, {fertz_dosage}")
    print(f"New Conditioner Dosage Conversion Set:{conditioner_ml}, {conditioner_water}, {conditioner_dosage}")
    print("===OUTSIDE UTILS===")
    save()

def set_co2_runtime():
    global calibration_data
    global dosage_data
    try:
        time_per_ml = calibration_data["Co2 Calibration Data"]["Time per 1mL"]
    except KeyError:
        print("Defaulting Co2 Calibration")
        time_per_ml = 1
    try:
        dose = dosage_data["Co2 Data"]["Dosage"]
    except KeyError:
        print("Defaulting Co2 Dosage")
        dose = 1

    runtime = round(time_per_ml*dose, 2)
    dosage_data["Co2 Data"].update(
        {
            "Runtime": runtime,
        }
    )
    print(f"Co2 Runtime: {runtime}")

def alert_data(ht: int, lt: int):
    global temperature_data
    print("New Alert Set")
    print(f"High Temperature: {ht}")
    print(f"Low Temperature: {lt}")
    temperature_data["Temperature Alert"].update(
        {
            "High Temp": ht,
            "Low Temp": lt
        }
    )
    save()

async def do_pump(pump_type: str):
    if pump_type == 'co2':
        try:
            seconds = int(dosage_data["Co2 Data"]["Runtime"])
            if seconds == 1:
                print(f"Runtime Too Short: {seconds}")
            else:
                print(f"Running Co2 for: {seconds}")
                GPIO.output(Co2_pump, 1)
        except KeyError:
            print("Error Running Dosage")
    elif pump_type == 'conditioner':
        return
    elif pump_type == 'fertilizer':
        print("Running fertz")
        GPIO.output(Fertilizer_pump, 1)
    await asyncio.sleep(seconds)
    GPIO.output(Co2_pump, 0)
    GPIO.output(Fertilizer_pump, 0)
    print("Dosing Completed")
    print(f"Dosing Ran For: {seconds}")
    return f"Dose Complete"

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
        sleep_time = 0.001
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
    print(f"Starting LED {option}")

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
        global calibration_data
        global led_pulse_loop
        cal_time = None
        led_pulse_loop = True
        cal_stop_signal = False
        led_pulse(PULSE)
        btn_pressed()
        if pump_type == 'co2':
            #stop_led_pulse()
            print(f"Running {pump_type}")
            print(f"{pump_type}                      Calibration started.")
            led_pulse(FLASH)
            start = time.time()
            GPIO.output(Co2_pump, 1)
            btn_pressed()
            print(f"Stopping {pump_type}")
            print(f"{pump_type}                      Calibration finished.")
            end = time.time()
            GPIO.output(Co2_pump, 0)
            cal_time = round(end - start, 2)
            co2_per_ml = round(cal_time/10, 2)
            print(cal_time)
            calibration_data["Co2 Calibration Data"].update(
                {
                    "Time per 10mL": cal_time,
                    "Time per 1mL": co2_per_ml
                }
            )
            stop_led_pulse()
            set_co2_runtime()
            save()
            print(calibration_data)
            return f"{cal_time} Calibration Completed"
    except ThreadKilled:
        print('calibration was cancelled!')
        stop_cal()

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