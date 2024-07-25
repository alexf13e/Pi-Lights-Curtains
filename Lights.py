
from kasa import Discover

import Log
import StateVariables as sv


NUM_EXPECTED_PLUGS = 7


async def turn_on():
    plugs = await __connect()
    for p in plugs:
        await p.turn_on()
    Log.write("Lights turned on")
    sv.set("lights_are_on", True)


async def turn_off():
    plugs = await __connect()
    for p in plugs:
        await p.turn_off()
    Log.write("Lights turned off")
    sv.set("lights_are_on", False)


async def __connect():
    plugs = []
    devices = []
    attempts = 0
    
    #hardcoded to look for 7 plugs, since thats how many there *should* be, and keep searching until it finds that many, or give up after 3 tries
    #lounge 1-4, external, hall, dining, external
    while len(devices) < NUM_EXPECTED_PLUGS and attempts < 3:
        devices = await Discover.discover(timeout=1)
        attempts += 1

    if attempts >= 3 and len(devices) < NUM_EXPECTED_PLUGS:
        Log.write(f"Only found {len(devices)} of the {NUM_EXPECTED_PLUGS} desired plugs after 3 attempts")

    for addr, dev in devices.items():
        try:
            await dev.update()
        except Exception as e:
            Log.write(f"Plug {dev.alias} at {addr} had error: {e}")
            continue
        Log.write(f"Plug {dev.alias} at {addr} connected")
        plugs.append(dev)
    return plugs
