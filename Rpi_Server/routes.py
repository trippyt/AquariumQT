from quart import Quart, request, websocket
from quart.json import jsonify
import utils
import threading
from time import sleep
app = Quart(__name__)

@app.route('/setConversionTankSize', methods=['GET', 'POST'])
async def set_conversions_tanksize():
    data = request.args.get('data')
    print(f"New Tank Size Set: {data}")
    utils.conversions_tanksize(data)
    return f"TankSize {data}"

@app.route('/setTemperatureAlert', methods=['GET', 'POST'])
async def set_temperature_alert():
    ht = request.args.get('ht')
    lt = request.args.get('lt')
    print(f"Receiving Temperature Alert Data H:{ht} L:{lt}")
    utils.alert_data(ht, lt)
    return f"Temperature Alerts H:{ht} L:{lt}"

@app.route('/getTemperatureAlert', methods=['GET'])
async def get_temperature_alert():
    print("Sending Data")
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
        #await asyncio.sleep(2)
        sleep(2)
        await websocket.send(str(temp))


if __name__ == '__main__':
    app.run("0.0.0.0")
