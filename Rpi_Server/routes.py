from quart import Quart, request, websocket
from quart.json import jsonify
import asyncio
import utils
import threading
from time import sleep
app = Quart(__name__)

@app.route('/setConversionRatios', methods=['GET', 'POST'])
async def set_conversions_ratios():
    tank = request.args.get('tank')
    co2_ml = request.args.get('co2_ml')
    co2_water = request.args.get('co2_water')
    co2_split_dose = request.args.get('co2_split_dose')
    fertz_ml = request.args.get('fertz_ml')
    fertz_water = request.args.get('fertz_water')
    conditioner_ml = request.args.get('conditioner_ml')
    conditioner_water = request.args.get('conditioner_water')
    print("===INSIDE ROUTES===")
    print(f"tank:{tank}", type(tank))
    print(f"co2_ml:{co2_ml}", type(co2_ml))
    print(f"co2_water:{co2_water}", type(co2_water))
    print(f"co2_split_dose:{co2_split_dose}", type(co2_split_dose))
    print(f"fertz_ml:{fertz_ml}", type(fertz_ml))
    print(f"fertz_water:{fertz_water}", type(fertz_water))
    print(f"conditioner_ml:{conditioner_ml}", type(conditioner_ml))
    print(f"conditioner_water:{conditioner_water}", type(conditioner_water))
    print("===OUTSIDE ROUTES===")
    utils.conversions(tank, co2_ml, co2_water, co2_split_dose, fertz_ml, fertz_water, conditioner_ml, conditioner_water)
    return f"Update Completed"

@app.route('/pauseOperation', methods=['GET', 'POST'])
async def pause_operation():
    pause_state = request.args.get('state')
    print(f"Pause State Changed: {pause_state}")
    await utils.pause_operation(pause_state)

@app.route('/startManualDose', methods=['GET', 'POST'])
async def start_manual_dose():
    pump_type = request.args.get('pump')
    print("Received Manual Dosing Request")
    print(f"Pump: {pump_type} Requested")
    await utils.do_pump(pump_type)
    return f"Dosing Completed"

@app.route('/getConversionTankSize', methods=['GET', 'POST'])
async def get_conversions_tanksize():
    print(f"Sending Tank Size")
    return jsonify(utils.load())

@app.route('/setTemperatureAlert', methods=['GET', 'POST'])
async def set_temperature_alert():
    ht = request.args.get('ht')
    lt = request.args.get('lt')
    print(f"Receiving Temperature Alert Data H:{ht} L:{lt}")
    utils.alert_data(ht, lt)
    return f"Temperature Alerts H:{ht} L:{lt}"

@app.route('/getServerData', methods=['GET'])
async def get_server_data():
    print("Sending Data to Client")
    return jsonify(utils.load())

@app.route('/calibrationModeOn', methods=['GET', 'POST'])
async def run_calibration():
    pump_type = request.args.get('type')
    print(pump_type)
    if pump_type in ['conditioner', 'co2', 'fertilizer']:
        cal_thread = threading.Thread(target=utils.start_calibration, args=(pump_type,))
        cal_thread.start()
        return f"Calibrating {pump_type} pump."
    else:
        return "Invalid pump specified"

@app.route('/calibrationModeOff', methods=['GET', 'POST'])
async def stop_calibration():
    pump_type = request.args.get('type')
    print(pump_type)
    resp = {}
    if pump_type in ['conditioner', 'co2', 'fertilizer']:
        utils.stop_cal()
        if utils.cal_time:
            resp['cal_time'] = utils.cal_time
        else:
            resp['error'] = 'Calibration was cancelled'
    else:
        resp['error'] = 'Invalid pump type'
    return jsonify(resp)

#@app.route('/runPump', methods=['GET', 'POST'])
#async def run_pump():
#    pump_type = request.args.get('type')
#    time = request.args.get('time')
#    print(time)
#    if not time:
#        time = 10
#    print(pump_type)
#    if pump_type in ['conditioner', 'co2', 'fertilizer']:
#        await utils.do_pump(pump_type, time)
#        return f"Enabling {pump_type} pump."
#    else:
#        return "Invalid pump specified"


#@app.route('/stopPump', methods=['GET', 'POST'])
#async def stop_pump():
#    pump_type = request.args.get('type')
#    print(pump_type)
#    if pump_type in ['conditioner', 'co2', 'fertilizer']:
#        await utils.stop_pump(pump_type)
#        return f"Disabling {pump_type} pump."
#    else:
#        return "Invalid pump specified"


@app.websocket('/temp')
async def temp():
    while True:
        temp = await utils.temp()
        #print(temp)
        await asyncio.sleep(2)
        #sleep(2)
        await websocket.send(str(temp))


if __name__ == '__main__':
    app.run("0.0.0.0")
