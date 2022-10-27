from kasa import SmartPlug, Discover
import asyncio
import FileManager

async def Connect():
    plugs = []
    devices = await Discover.discover(timeout=1)
    for addr, dev in devices.items():
        try:
            await dev.update()
        except Exception as e:
            FileManager.writeLog(f"Plug {dev.alias} at {addr} had error: {e}")
            continue
        FileManager.writeLog(f"Plug {dev.alias} at {addr} connected")
        plugs.append(dev)
    return plugs

async def On():
    plugs = await Connect()
    for p in plugs:
        await p.turn_on()
        FileManager.writeVariable("lights_are_on", True)

async def Off():
    plugs = await Connect()
    for p in plugs:
        await p.turn_off()
        FileManager.writeVariable("lights_are_on", False)

if (__name__ == "__main__"):
    asyncio.run(Off()) # for testing
