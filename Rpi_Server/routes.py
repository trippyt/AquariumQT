from quart import Quart, request, websocket
import utils
from time import sleep
app = Quart(__name__)


@app.route('/runPump', methods=['GET', 'POST'])
async def run_pump():
    pump_type = request.args.get('type')
    time = request.args.get('time')
    print(time)
    if not time:
        time = 10
    if pump_type == 'water' or 'co2' or 'fertilizer':
        await utils.do_pump(pump_type, time)
        return f"Enabling {pump_type} pump."



@app.route('/stopPump', methods='POST')
async def stop_pump():
    return


@app.websocket('/temp')
async def temp():
    while True:
        temp = await utils.temp()
        print(temp)
        sleep(2)
        await websocket.send(str(temp))


if __name__ == '__main__':
    app.run("0.0.0.0")
