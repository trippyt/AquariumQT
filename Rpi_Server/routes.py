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


@app.websocket('/temp')
async def temp():
    while True:
        temp = await utils.temp()
        print(temp)
        sleep(4)
        await websocket.send(str(temp))

if __name__ == '__main__':
    app.run("0.0.0.0")
