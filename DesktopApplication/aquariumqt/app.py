import sys
import os
import time
import logging
import json
from time import gmtime, strftime
from PyQt5 import QtWidgets, QtWebSockets
from PyQt5 import QtCore, QtNetwork
from PyQt5.QtCore import QTime, QUrl, QEventLoop
from aquariumqt.form import Ui_Form

from . import dummyGPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(17,GPIO.OUT)
GPIO.setup(27,GPIO.OUT)

# all of that is going server side
# plus it gave me import errors when i ran it lol

class InfoHandler(logging.Handler):  # inherit from Handler class
    def __init__(self, textBrowser):
        super().__init__()
        self.textBrowser = textBrowser

    def emit(self, record):  # override Handler's `emit` method
        self.textBrowser.append(self.format(record))


class App(object):

    def __init__(self):
        self.fluid_conversions = None
        self.dosing = None
        self.light_control = None
        self.schedule = None
        self.completed = ''
        self.fertz_prev_time = ''
        self.conditioner_prev_time = ''
        self.nam = QtNetwork.QNetworkAccessManager()
        self.timers = []
        self.calibration_mode_on = True

        self.conversion_values = {
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

        self.conversion_data = {
            "Tank Size": {},
            "Co2 Ratio": {},
            "Fertilizer Ratio": {},
            "Water Conditioner Ratio": {},
        }

        self.schedule_data = {
            "Co2 Schedule Data": {},
            "Fertilizer Schedule Data": {},
            "Tap Schedule Data": {},
            "Water Cycle Schedule Data": {}
        }

        self.calibration_data = {
            "Co2 Calibration Data": {},
            "Fertilizer Calibration Data": {},
            "Water Conditioner Calibration Data": {},
        }

        self.light_hour_data = {
            "Mode Hours": {},
        }

        # Simple mapping for the combobox
        self.light_type_map = {
            'default': 'off',
            0: 'day',
            1: 'night',
            2: 'off',
        }

        self.temperature_data = {
            "Temperature Data": {},
        }

        self.app = QtWidgets.QApplication(sys.argv)
        self.central = QtWidgets.QWidget()
        self.window = QtWidgets.QMainWindow()
        self.form = Ui_Form()
        self.window.setCentralWidget(self.central)
        self.form.setupUi(self.central)
        #self.app.setStyle("fusion")

        self.hour_btns = [
            self.form.hours_0,
            self.form.hours_1,
            self.form.hours_2,
            self.form.hours_3,
            self.form.hours_4,
            self.form.hours_5,
            self.form.hours_6,
            self.form.hours_7,
            self.form.hours_8,
            self.form.hours_9,
            self.form.hours_10,
            self.form.hours_11,
            self.form.hours_12,
            self.form.hours_13,
            self.form.hours_14,
            self.form.hours_15,
            self.form.hours_16,
            self.form.hours_17,
            self.form.hours_18,
            self.form.hours_19,
            self.form.hours_20,
            self.form.hours_21,
            self.form.hours_22,
            self.form.hours_23,
        ]

        self.form.clear_log_button.clicked.connect(self.clear_log_button)

        self.form.day_hour_wheel.valueChanged.connect(self.log_day_hour_wheel)
        self.form.night_hour_wheel.valueChanged.connect(self.night_hour_wheel_changed)
        self.form.off_hour_wheel.valueChanged.connect(self.log_off_hour_wheel)

        self.form.TankSize_DoubleSpinBox.valueChanged.connect(self.set_tanksize_conversion)
        self.form.C02_DoubleSpinBox.valueChanged.connect(self.set_co2_conversion)
        self.form.C02toWater_DoubleSpinBox.valueChanged.connect(self.set_co2_conversion)
        self.form.Fertz_DoubleSpinBox.valueChanged.connect(self.set_fertz_conversion)
        self.form.FertztoWater_DoubleSpinBox.valueChanged.connect(self.set_fertz_conversion)
        self.form.TapSafe_DoubleSpinBox.valueChanged.connect(self.set_conditioner_conversion)
        self.form.TapSafetoWater_DoubleSpinBox.valueChanged.connect(self.set_conditioner_conversion)
        self.form.saveDoses_pushButton.clicked.connect(self.save)

        self.form.feed_pushButton.clicked.connect(self.feed_test)
        self.form.C02CalibrationButton.clicked.connect(lambda: self.enter_calibration_mode("co2"))
        self.form.c02_pushButton.clicked.connect(self.co2_manual_dose)
        self.form.FertzCalibrationButton.clicked.connect(self.fertz_calibration)
        self.form.TapSafeCalibrationButton.clicked.connect(self.conditioner_calibration)

        self.form.c02_comboBox_2.currentIndexChanged.connect(self.set_co2_conversion)
        self.form.fertz_comboBox_2.currentIndexChanged.connect(self.set_fertz_conversion)
        self.form.water_conditioner_comboBox.currentIndexChanged.connect(self.set_conditioner_conversion)

        self.form.calendarWidget.selectionChanged.connect(self.dose_sch)
        self.form.co2_sch_pushButton.clicked.connect(self.set_co2_schedule)
        self.form.fertz_sch_pushButton.clicked.connect(self.set_fertz_schedule)
        self.form.conditioner__sch_pushButton.clicked.connect(self.set_conditioner_schedule)
        self.form.water_cycle_sch_pushButton.clicked.connect(self.set_water_cycle_schedule)
        self.form.del_events_pushButton.clicked.connect(self.del_events_sch)
        self.form.repeat_comboBox.currentIndexChanged.connect(self.repeat_sch)
        self.form.hour_save_button.clicked.connect(self.set_schedule)

        self.form.sunrise_sunset_radioButton.clicked.connect(self.sun_mode)
        self.form.manual_hour_mode_radioButton.clicked.connect(self.manual_hours_mode)
        self.form.light_mode_comboBox.currentTextChanged.connect(self.toggle_mode)
        self.form.ht_alert_edit.valueChanged.connect(self.set_temp_alert)
        self.form.lt_alert_edit.valueChanged.connect(self.set_temp_alert)

        self.conditioner_calibration_started= False
        self.fertz_calibration_started = False
        self.co2_calibration_started = False

        logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
        self.log = logging.getLogger('AquariumQT')
        self.log.handlers = [InfoHandler(self.form.textBrowser)]
        self.load()
        self.start_timers()

        self.update_timer()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)

        self.client = QtWebSockets.QWebSocket("", QtWebSockets.QWebSocketProtocol.Version13, None)
        self.client.error.connect(self.on_error)
        self.client.open(QUrl("ws://192.168.1.35:5000/temp"))
        self.client.pong.connect(self.ws_receive)
        self.client.textMessageReceived.connect(self.ws_receive)

    def save(self):
        data = {
            "Conversion Data": self.conversion_data,
            "Schedule Data": self.schedule_data,
            "Calibration Data": self.calibration_data,
            #"Temperature Data": self.temperature_data,
            "Light Hour Data": self.light_hour_data
        }
        with open('data.txt', 'w') as json_file:
            json_file.write(json.dumps(data, indent=4))
        self.log.info("Settings Updated")

    def load_server(self):
        url = f"http://192.168.1.35:5000/getTemperatureAlert"
        request = QtNetwork.QNetworkRequest(QUrl(url))
        loop = QEventLoop()
        resp = self.nam.get(request)
        resp.finished.connect(loop.quit)
        print('fetching request...')
        loop.exec_()
        data = resp.readAll()
        byte_array = data
        new_data = json.loads(byte_array.data())
        self.calibration_data = new_data["Calibration Data"]
        self.temperature_data = new_data["Temperature Data"]

        self.form.ht_alert_edit.blockSignals(True)
        self.form.lt_alert_edit.blockSignals(True)
        try:
            self.form.ht_alert_edit.setValue(float(self.temperature_data["High Temp"])),
            self.form.lt_alert_edit.setValue(float(self.temperature_data["Low Temp"])),
        except KeyError:
            print("No Temperture Data on Server")
        self.form.ht_alert_edit.blockSignals(False)
        self.form.lt_alert_edit.blockSignals(False)
        print(new_data)

    def load(self):
        if os.path.isfile('data.txt'):
            with open('data.txt', 'r') as json_file:
                data = json.loads(json_file.read())

            self.conversion_data = data["Conversion Data"]
            self.schedule_data = data["Schedule Data"]
            #self.calibration_data = data["Calibration Data"]
            self.light_hour_data = data["Light Hour Data"]
            #self.temperature_data = data["Temperature Data"]
            self.form.TankSize_DoubleSpinBox.blockSignals(True)
            self.form.C02_DoubleSpinBox.blockSignals(True)
            self.form.C02toWater_DoubleSpinBox.blockSignals(True)
            self.form.Fertz_DoubleSpinBox.blockSignals(True)
            self.form.FertztoWater_DoubleSpinBox.blockSignals(True)
            self.form.TapSafe_DoubleSpinBox.blockSignals(True)
            self.form.TapSafetoWater_DoubleSpinBox.blockSignals(True)

            try:
                self.form.TankSize_DoubleSpinBox.setValue(self.conversion_data["Tank Size"]["Water Volume"])
                self.form.C02_DoubleSpinBox.setValue(self.conversion_data["Co2 Ratio"]["Co2 Amount"])
                self.form.C02toWater_DoubleSpinBox.setValue(self.conversion_data["Co2 Ratio"]["Co2 to Water"])
                self.form.Fertz_DoubleSpinBox.setValue(self.conversion_data["Fertilizer Ratio"]["Fertilizer Amount"])
                self.form.FertztoWater_DoubleSpinBox.setValue(self.conversion_data["Fertilizer Ratio"]["Fertilizer to Water"])
                self.form.TapSafe_DoubleSpinBox.setValue(self.conversion_data["Water Conditioner Ratio"]["Conditioner Amount"])
                self.form.TapSafetoWater_DoubleSpinBox.setValue(self.conversion_data["Water Conditioner Ratio"]["Conditioner to Water"])
                print("Loading Ratio Data")
            except KeyError:
                print("No Ratio Data To Load")

            self.form.TankSize_DoubleSpinBox.blockSignals(False)
            self.form.C02_DoubleSpinBox.blockSignals(False)
            self.form.C02toWater_DoubleSpinBox.blockSignals(False)
            self.form.Fertz_DoubleSpinBox.blockSignals(False)
            self.form.FertztoWater_DoubleSpinBox.blockSignals(False)
            self.form.TapSafe_DoubleSpinBox.blockSignals(False)
            self.form.TapSafetoWater_DoubleSpinBox.blockSignals(False)
            self.set_tanksize_conversion()

            try:
                self.form.co2_dosing_lcd.display(self.calibration_data["Co2 Calibration Data"]["Time"])
                self.form.co2_calibration_perml_display.display(self.calibration_data["Co2 Calibration Data"]["Time"] / 10)
                self.form.fertz_dosing_lcd.display(self.calibration_data["Fertilizer Calibration Data"]["Time"])
                self.form.conditioner_dosing_lcd.display(self.calibration_data["Water Conditioner Calibration Data"]["Time"])
                self.form.co2_seconds_display.display(self.calibration_data["Co2 Calibration Data"]["Dosing Runtime"])
                print("Loading Calibration Data")
            except KeyError:
                print("No Calibration Data To Load")

            #if self.temperature_data:
            #    self.form.ht_alert_edit.setValue(self.temperature_data["High Temp"]),
            #    self.form.lt_alert_edit.setValue(self.temperature_data["Low Temp"]),
            #    print("Loading Temperature Data")
            #else:
            #    print("No Temperature Data To Load")
            self.load_server()

    def co2_perml(self):
        time = self.calibration_data["Co2 Calibration Data"]["Time"] / 10
        self.form.co2_calibration_perml_display(time)

    def get_checked_buttons(self):
        """
       Returns a list of all checked buttons on the form
       Uses the list index to determine the hour and returns
       ONLY hours that are checked

       e.g. [0, 3, 4, 5, 6, 7, 20, 21, 22, 23]

       """
        checked = [btn.isChecked() for btn in self.hour_btns]
        selected_hours = [checked.index(n) for n in checked]
        return selected_hours

    def update_light_data(self, hours, date, light_type):
        # Start w/ an empty dict w/ keys for each hour
        # Light is 'off' by default
        default_light_type = self.light_type_map['default']
        light_data = {n: default_light_type for n in range(24)}

        # Iterate the selected hours for this date and populate the dict
        # All the light types are the same for these hours (since they were checked)
        for hour in hours:
            light_data[hour] = light_type

        # Create a date key in the main dict, containing the
        # date and the hour data for that date
        self.light_hour_data[date] = {
            "date": date,
            "light_data": light_data
        }

    def set_schedule(self):
        # First get a list of the checked buttons
        checked = self.get_checked_buttons()

        # Now get the date from the calendar
        date = self.form.calendarWidget_2.selectedDate().toString()

        # Finally get the light type based on the value of the combobox
        light_type = self.light_type_map[self.form.hour_comboBox.currentIndex()]

        # Now update the light data by passing in the list of hours, the date
        # and the light type to apply to those hours
        self.update_light_data(checked, date, light_type)
        self.save()

        # Uncheck all buttons, you don't need the if
        # statement...just set them all to False
        for btn in self.hour_btns:
            btn.setChecked(False)

    def set_btn(self):
        self.light_hour_data["Day"].update(
            {
                "Date": str(self.form.calendarWidget_2.selectedDate().toString()),
                "Time": str([btn.isChecked() for btn in self.hour_btns])
            }
        )
        print("Day")
        for btn in self.hour_btns:
            if btn.isChecked():
                btn.setStyleSheet("background-color: red")
                time.sleep(1)
                btn.setStyleSheet("background-color: blue")

    def set_temp_alert(self):
        ht = self.form.ht_alert_edit.value()
        lt = self.form.lt_alert_edit.value()
        print(f"Sending Alert Changes to Network")
        print(f"High Temperature: {ht}")
        print(f"Low Temperature: {lt}")
        url = f"http://192.168.1.35:5000/setTemperatureAlert?ht={ht}&lt={lt}"
        request = QtNetwork.QNetworkRequest(QUrl(url))
        self.nam.get(request)

    def update_timer(self):
        self.form.light_clock_display.display(strftime("%H:%M", gmtime()))

    def sun_mode(self):
        self.form.light_mode_display.setText("Sunrise / Sunset")
        self.log.info("Switched to : Sunrise / Sunset : Mode")

    def manual_hours_mode(self):
        self.form.light_mode_display.setText("Auto Mode")
        self.log.info("Switched to : Auto : Mode")

    def toggle_mode(self):
        text = str(self.form.light_mode_comboBox.currentText())
        if text == 'day':
            print("Day")
        elif text == 'night':
            print("Night")
        elif text == 'off':
            print("Off")
        self.form.light_mode_display.setText("Toggle Mode")
        self.log.info(f"Switched Toggle Mode to : {text} :")

    def set_tanksize_conversion(self):
        self.set_conversion()
        self.set_co2_conversion()
        self.set_fertz_conversion()
        self.set_conditioner_conversion()
        self.conversion_data["Tank Size"].update(
            {
                "Water Volume": self.form.TankSize_DoubleSpinBox.value()
            }
        )

    def set_co2_conversion(self):
        self.set_conversion()
        self.conversion_values["co2_dosage"] = self.conversion_values["co2_amount"] * (self.conversion_values["tank_size"] / self.conversion_values["co2_to_water"])
        a = self.conversion_values["co2_dosage"]
        self.form.C02_outLcd.setProperty('value', round(a, 2))
        x = self.form.c02_comboBox_2.currentIndex() + 1
        if x == 0:
            x = 1
        c02_dose = round(a/x, 2)
        self.form.c02_ml_outLcd.setProperty('value', c02_dose)
        self.conversion_data["Co2 Ratio"].update(
            {
                "Co2 Amount": self.form.C02_DoubleSpinBox.value(),
                "Co2 to Water": self.form.C02toWater_DoubleSpinBox.value(),
                "Co2 Dosage": round(self.conversion_values["co2_dosage"], 2)
            }
        )

    def set_co2_schedule(self):
        self.schedule_data["Co2 Schedule Data"].update(
            {
                "Date": str(self.form.calendarWidget.selectedDate().toString()),
                "Time": str(self.form.co2_timeEdit.time().toString()),
                "Repeat": self.repeat_sch()
            }
        )
        self.save()

    def set_fertz_conversion(self):
        self.set_conversion()
        self.conversion_values["fertz_dosage"] = self.conversion_values["fertz_amount"] * (self.conversion_values["tank_size"] / self.conversion_values["fertz_to_water"])
        a = self.conversion_values["fertz_dosage"]
        self.form.Fertz_outLcd.setProperty('value', round(a, 2))
        x = self.form.fertz_comboBox_2.currentIndex() + 1
        if x == 0:
            x = 1
        fertz_dose = round(a/x, 2)
        self.form.fertz_ml_display.setProperty('value', fertz_dose)
        self.conversion_data["Fertilizer Ratio"].update(
            {
                "Fertilizer Amount": self.form.Fertz_DoubleSpinBox.value(),
                "Fertilizer to Water": self.form.FertztoWater_DoubleSpinBox.value(),
                "Fertilizer Dosage": round(self.conversion_values["fertz_dosage"], 2)
            }
        )

    def set_fertz_schedule(self):
        self.schedule_data["Fertilizer Schedule Data"].update(
            {
                "Date": str(self.form.calendarWidget.selectedDate().toString()),
                "Time": str(self.form.fertz_timeEdit.time().toString()),
                "Repeat": self.repeat_sch()
            }
        )
        self.save()

    def set_conditioner_conversion(self):
        self.set_conversion()
        self.conversion_values["conditioner_dosage"] = self.conversion_values["conditioner_amount"] * (self.conversion_values["tank_size"] / self.conversion_values["conditioner_to_water"])
        a = self.conversion_values["conditioner_dosage"]
        self.form.conditioner_outLcd.setProperty('value', round(a, 2))
        x = self.form.water_conditioner_comboBox.currentIndex() + 1
        if x == 0:
            x = 1
        con_dose = round(a/x, 2)
        self.form.water_conditioner_ml_display.setProperty('value', con_dose)
        self.conversion_data["Water Conditioner Ratio"].update(
            {
                "Conditioner Amount": self.form.TapSafe_DoubleSpinBox.value(),
                "Conditioner to Water": self.form.TapSafetoWater_DoubleSpinBox.value(),
                "Conditioner Dosage": round(self.conversion_values["conditioner_dosage"], 2)
            }
        )

    def set_conditioner_schedule(self):
        self.schedule_data["Conditioner Schedule Data"].update(
            {
                "Date": str(self.form.calendarWidget.selectedDate().toString()),
                "Time": str(self.form.conditioner_timeEdit.time().toString()),
                "Repeat": self.repeat_sch()
            }
        )
        self.save()

    def set_water_cycle_schedule(self):
        self.schedule_data["Water Cycle Schedule Data"].update(
            {
                "Date": str(self.form.calendarWidget.selectedDate().toString()),
                "Time": str(self.form.water_cycle_timeEdit.time().toString()),
                "Repeat": self.repeat_sch()
            }
        )
        self.save()

    def co2_manual_dose(self):
        a = self.form.co2_calibration_perml_display.value() * self.form.c02_ml_outLcd.value()
        self.log.info(f"Dosing Co2 for {a:.2f} Seconds")
        self.calibration_data["Co2 Calibration Data"].update(
            {
                "Dosing Runtime": round(a, 2)
            }
        )
        self.save()
        GPIO.output(17, 1)

        self.completed = a / 100

        while self.completed < 100:
            self.completed += 0.0001
            self.form.progressBar.setValue(self.completed)

        time.sleep(a)
        GPIO.output(17, 0)
        self.log.info("Co2 Dosing Complete")

    def feed_test(self):
        GPIO.output(27, 1)
        print("Secondary Activated")
        time.sleep(3)
        GPIO.output(27, 0)
        print("Secondary Deactivated")

    def enter_calibration_mode(self, pump_type):
        self.calibration_mode_on = not self.calibration_mode_on
        if not self.calibration_mode_on:
            url = f"http://192.168.1.35:5000/calibrationModeOn?type={pump_type}"
            print("Entering Calibration Mode")
            request = QtNetwork.QNetworkRequest(QUrl(url))
            #loop = QEventLoop()
            resp = self.nam.get(request)
            #resp.finished.connect(loop.quit)
            #print("Waiting For Calibration Data")
            #loop.exec_()
            data = resp.readAll()
            print(data)
        else:
            self.exit_calibration_mode(pump_type)

    def exit_calibration_mode(self, pump_type):
        url = f"http://192.168.1.35:5000/calibrationModeOff?type={pump_type}"
        print("Exiting Calibration Mode")
        request = QtNetwork.QNetworkRequest(QUrl(url))
        self.nam.get(request)
#    def send_calibration_request(self, pump_type):
#        self.pump_on = not self.pump_on
#        if not self.pump_on:
#            url = f"http://192.168.1.35:5000/runPump?type={pump_type}"
#            print("starting calibration request")
#            request = QtNetwork.QNetworkRequest(QUrl(url))
#            self.nam.get(request)
#        else:
#            url = f"http://192.168.1.35:5000/stopPump?type={pump_type}"
#            print("finishing calibration request")
#            request = QtNetwork.QNetworkRequest(QUrl(url))
#            self.nam.get(request)

    def fertz_calibration(self):
        self.fertz_calibration_started = not self.fertz_calibration_started
        if self.fertz_calibration_started:
            self.fertz_prev_time = time.time()
            self.log.info("Fertilizer                      Calibration started.")
        else:
            fertz_elapsed_time = time.time() - self.fertz_prev_time
            self.form.fertz_dosing_lcd.setProperty('value', round(fertz_elapsed_time, 2))
            self.log.info(f"Fertilizer                      Calibration stopped.                      - {fertz_elapsed_time:.2f} Seconds -")
            self.calibration_data["Fertilizer Calibration Data"].update(
                {
                    "Time": round(fertz_elapsed_time, 2)
                }
            )
            self.save()

    def conditioner_calibration(self):
        self.conditioner_calibration_started = not self.conditioner_calibration_started
        if self.conditioner_calibration_started:
            self.conditioner_prev_time = time.time()
            self.log.info("Water Conditioner                      Calibration started.")
        else:
            conditioner_elapsed_time = time.time() - self.conditioner_prev_time
            self.form.conditioner_dosing_lcd.setProperty('value', round(conditioner_elapsed_time, 2))
            self.log.info(f"Water Conditioner                      Calibration stopped.                      - {conditioner_elapsed_time:.2f} Seconds -")
            self.calibration_data["Water Conditioner Calibration Data"].update(
                {
                    "Time": round(conditioner_elapsed_time, 2)
                }
            )
            self.save()

    def set_conversion(self):
        self.conversion_values["tank_size"] = self.form.TankSize_DoubleSpinBox.value()
        self.conversion_values["co2_amount"] = self.form.C02_DoubleSpinBox.value()
        self.conversion_values["co2_to_water"] = self.form.C02toWater_DoubleSpinBox.value()
        self.conversion_values["fertz_amount"] = self.form.Fertz_DoubleSpinBox.value()
        self.conversion_values["fertz_to_water"] = self.form.FertztoWater_DoubleSpinBox.value()
        self.conversion_values["conditioner_amount"] = self.form.TapSafe_DoubleSpinBox.value()
        self.conversion_values["conditioner_to_water"] = self.form.TapSafetoWater_DoubleSpinBox.value()

    def set_light_hour(self):
        self.light_hour_data["Light Hours"].update(
            {
                "Day Hour": str(self.form.day_hour_timeEdit.time().toString()),
                "Night Hour": str(self.form.night_hour_timeEdit.time().toString()),
                "Off Hour": str(self.form.off_hour_timeEdit.time().toString())
            }
        )
        self.save()

    def run(self):
        self.window.show()
        self.app.exec()

    def printvalue(self, value):
        print(value)
        self.log.info(value)

    def clear_log_button(self):
        self.form.textBrowser.clear()
        self.log.info("*" * 40)
        self.log.info("*Aquarium Monitoring*".center(15))
        self.log.info("*" * 40)

    def log_day_hour_wheel(self, value):
        hour = value // 60
        minute = value % 60
        self.form.day_hour_timeEdit.setTime(QTime(hour, minute))
        self.log.info(str(self.form.day_hour_timeEdit.time().toString()))
        self.set_light_hour()

    def night_hour_wheel_changed(self, value):
        hour = value // 60
        minute = value % 60
        self.form.night_hour_timeEdit.setTime(QTime(hour, minute))
        self.log.info(self.form.night_hour_timeEdit.time().toString())
        self.set_light_hour()

    def log_off_hour_wheel(self, value):
        hour = value // 60
        minute = value % 60
        self.form.off_hour_timeEdit.setTime(QTime(hour, minute))
        self.set_light_hour()

    def repeat_sch(self):
        idx = self.form.repeat_comboBox.currentText()
        return idx

    def del_events_sch(self):
        self.log.info("Deleted")

    def dose_sch(self):
        date = self.form.calendarWidget.selectedDate()
        self.form.date_display_LineEdit.setText(date.toString())

    def light_logic(self):
        self.set_light_hour()

    def send_request(self, pump_type, time):
        url = f"http://127.0.0.1:5000?time={time}?pump_type={pump_type}" # gonna change that later of course
        request = QtNetwork.QNetworkRequest(QUrl(url))
        self.nam.post(request)

    def handle_response(self, response):
        print(response.readAll()) # you can change this to show in the log instead if you want to

    def start_timers(self):
        return

    def ws_receive(self, text):
        self.form.tank_degrees_c_display.display(text)

    def on_error(self, error_code):
        return



def main():
    App().run()


if __name__ == '__main__':
    main()

