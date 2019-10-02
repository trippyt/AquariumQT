from quart import Quart, request, websocket
import utils
from time import sleep
app = Quart(__name__)


@app.route('/runPump', methods='POST')
async def run_pump():
    pump_type = request.args.get('type')
    time = request.args.get('time')
    if not (pump_type == 'water' or 'co2' or 'fertilizer'):
        return "Incorrect pump value"
    try:
        time = int(time)
    except ValueError:
        return "Invalid time value"

    await utils.do_pump(pump_type, time)
    return "Complete"

@app.route('/calibration', methods='POST')
async def calibrate_pump():
    pump_type = request.args.get('type')
    if not (pump_type == 'water' or 'co2' or 'fertilizer'):
        return "Incorrect pump value"

    await utils.do_calibration_pump(pump_type)
    return "Complete"


@app.websocket('/temp')
async def temp():
    while True:
        temp = await utils.temp()
        print(temp)
        sleep(2)
        await websocket.send(str(temp))


if __name__ == '__main__':
    app.run("0.0.0.0")
