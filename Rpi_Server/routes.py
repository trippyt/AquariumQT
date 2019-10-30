from quart import Quart, request, websocket
import utils
import threading
from time import sleep
app = Quart(__name__)

@app.route('/calibrationModeOn', methods=['GET', 'POST'])
async def run_calibration():
    pump_type = request.args.get('type')
    print(pump_type)
    if pump_type in ['conditioner', 'co2', 'fertilizer']:
        cal_thread = threading.Thread(target=utils.start_calibration, args=(pump_type,)
        cal_thread.start()
        return f"Calibrating {pump_type} pump."
    else:
        return "Invalid pump specified"

@app.route('/calibrationModeOff', methods=['GET', 'POST'])
async def stop_calibration():
    pump_type = request.args.get('type')
    print(pump_type)
    if pump_type in ['conditioner', 'co2', 'fertilizer']:
        utils.stop_cal()
        return f"Finished Calibrating {pump_type} pump."
    else:
        return "Invalid pump specified"

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
        sleep(2)
        await websocket.send(str(temp))


if __name__ == '__main__':
    app.run("0.0.0.0")
