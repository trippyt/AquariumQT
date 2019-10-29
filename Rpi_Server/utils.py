import asyncio
from time import sleep
import time
import random

import t_sensor
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

co2_calibration_started = False

led_on = True

async def led_pulse():
    global calibration
    while calibration == 1 :
        for x in range(100):  # This Loop will run 100; times 0 to 100
            pwm.ChangeDutyCycle(x)  # Change duty cycle
            sleep(0.01)  # Delay of 10mS
        for x in range(100, 0, -1):  # Loop will run 100 times; 100 to 0
            pwm.ChangeDutyCycle(x)
            sleep(0.01)
        calibration = GPIO.input(Button)


async def led_flash():
    global calibration
    while calibration == 0:
        for x in range(100):  # This Loop will run 100; times 0 to 100
            pwm.ChangeDutyCycle(x)  # Change duty cycle
            sleep(0.0001)  # Delay of 10mS
        for x in range(100, 0, -1):  # Loop will run 100 times; 100 to 0
            pwm.ChangeDutyCycle(x)
            sleep(0.0001)
        calibration = GPIO.input(Button)


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

# if button is pressed at anytime before the gui calibration button it will do nothing
# client gui calibration button pressed (enters calibration mode)
# sends calibration request with the dosage type to the server
# server then starts pulsing the led, and waits for the physical button to be pushed
# if the clients gui button gets pressed then cancel and turn off led
# if the physical button is pushed then start the timer and pump and make the led flash quickly
# once the user has measured 10ml press the physical button again the pump and timer stop and the led turns off
# server then saves the elapsed time for that dose calibration, and sends it to the gui to display (exits calibration mode)
# from this point the led is off and the button will be inactive again just like in the beginning

async def do_calibration(pump_type: str):
    global calibration
    calibration = GPIO.input(Button)
    global co2_calibration_started
    global co2_prev_time
    calibration = not False

    try:
        print("Calibration Mode")
        print(f"Button State:{calibration}")
        if calibration == 1:
            await led_pulse()

            calibration = GPIO.input(Button)

        elif calibration == 0:
            print(f"Button State:{calibration}")
            if pump_type == 'co2':
                print("Running co2")
                GPIO.output(Co2_pump, 1)
                co2_calibration_started = not co2_calibration_started
                if co2_calibration_started:
                    await led_flash()
                    co2_prev_time = time.time()
                    GPIO.output(17, 1)
                    print("Co2                      Calibration started.")
                    calibration = GPIO.input(Button)

                else:
                    co2_elapsed_time = time.time() - co2_prev_time
                    #print(f"{pump_type}{co2_elapsed_time}:2.")
                    print(round(co2_elapsed_time, 2))
                    GPIO.output(17, 0)
                    print("Co2                      Calibration finished.")
                    calibration = GPIO.input(Button)


            elif pump_type == 'conditioner':
                print("Running conditioner")
            elif pump_type == 'fertilizer':
                print("Running fertilizer")
                GPIO.output(Fertilizer_pump, 1)
            GPIO.output(Co2_pump, 0)
        while calibration == 0:
            for x in range(100):  # This Loop will run 100; times 0 to 100
                pwm.ChangeDutyCycle(x)  # Change duty cycle
                sleep(0.0001)  # Delay of 10mS
            for x in range(100, 0, -1):  # Loop will run 100 times; 100 to 0
                pwm.ChangeDutyCycle(x)
                sleep(0.0001)
                calibration = GPIO.input(Button)

    # If keyboard Interrupt (CTRL-C) is pressed
    except KeyboardInterrupt:
        pass  # Go to next line
    pwm.stop()  # Stop the PWM


async def temp():
    temp_c, temp_f = t_sensor.read_temp()
    # So we would have to make sure that we don't do read_temp more than once every 2 seconds
    # t = random.randint(1, 40)
    #return temp_c, temp_f
    return round(temp_c, 2)
