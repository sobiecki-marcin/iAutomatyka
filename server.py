#!/usr/bin/env python

# WS server example

import asyncio
import datetime
import random
import websockets
import json
import plc
import snap7

myplc = snap7.client.Client()
plc_IP = '192.168.10.56'
plc_RACK = 0
plc_SLOT = 1

try:
    myplc.connect(plc_IP, plc_RACK, plc_SLOT)
except ConnectionError:
    print("Upss...")


def consumer(message):
    data = json.loads(message)
    # print(data)
    if data['engine']:
        plc.set_process_inputs_bit(myplc, 0, 0, 1)
        print("engine start")
    else:
        plc.set_process_inputs_bit(myplc, 0, 0, 0)
        print("engine stop")
    if data['timer']:
        plc.set_process_inputs_bit(myplc, 0, 1, 1)
        print("timer start")
    else:
        plc.set_process_inputs_bit(myplc, 0, 1, 0)
        print("timer stop")


async def producer():
    STATE = {
        "Connected":  myplc.get_connected(),
        "Engine": plc.get_process_outputs_bit(myplc, 0, 0),
        "Timer": plc.get_process_outputs_bit(myplc, 0, 1),
        "Start": plc.get_process_outputs_bit(myplc, 0, 2),
    }
    return json.dumps({**STATE})


async def consumer_handler(websocket, path):
    async for message in websocket:
        consumer(message)


async def producer_handler(websocket, path):
    while True:
        message = await producer()
        await websocket.send(message)
        await asyncio.sleep(1)


async def handler(websocket, path):
    consumer_task = asyncio.ensure_future(
        consumer_handler(websocket, path))
    producer_task = asyncio.ensure_future(
        producer_handler(websocket, path))
    done, pending = await asyncio.wait(
        [consumer_task, producer_task],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()


start_server = websockets.serve(handler, "127.0.0.1", 5678)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
