
import asyncio
import threading
import time

from Curtains import LoungeCurtain, RemoteCurtain, CurtainActions
from LDR import LDR
import Lights
import Log
import Pins
from RemoteInput import RemoteInputManager
import StateVariables as sv


class Timer:
    def __init__(self):
        self._exit = threading.Event()

    def terminate(self):
        self._exit.set()

    def run(self, callback, interval: int, ldr: LDR, lounge_curtain: LoungeCurtain, lounge_blind: RemoteCurtain, dining_curtain: RemoteCurtain):
        while not self._exit.is_set():
            asyncio.run(callback(ldr, lounge_curtain, lounge_blind, dining_curtain))
            time.sleep(interval)


async def update_lights(ldr: LDR):
    if not ldr.ignored_for_lights:
        lights_changed = False
        match ldr.check_lights_want_to_be_on():
            case True:
                if not sv.get("lights_are_on"):
                    Log.write("LDR requested lights on")
                    await Lights.turn_on() # await to prevent log entries getting mixed
                    lights_changed = True

            case False:
                if sv.get("lights_are_on"):
                    Log.write("LDR requested lights off")
                    await Lights.turn_off()
                    lights_changed = True

            # may return None, meaning no change wants to happen

        if lights_changed:
            ldr.time_previous_lights_action = time.time()
            ldr.ignored_for_lights = True
            Log.write("Started ignoring LDR for lights")


def update_curtain(curtain: LoungeCurtain | RemoteCurtain, want_to_be_open: bool):
    currently_open = sv.get(curtain.state_variable_name)
    match want_to_be_open:
        case True:
            if not currently_open:
                Log.write(f"LDR requested {curtain.display_name} open")
                return curtain.request(CurtainActions.OPEN)

        case False:
            if currently_open:
                Log.write(f"LDR requested {curtain.display_name} close")
                return curtain.request(CurtainActions.CLOSE)

    return False


def update_curtains(ldr: LDR, lounge_curtain: LoungeCurtain, lounge_blind: RemoteCurtain, dining_curtain: RemoteCurtain):
    want_to_be_open = ldr.check_curtains_want_to_be_open()

    if not ldr.ignored_for_lounge_blind:
        if update_curtain(lounge_blind, want_to_be_open):
            ldr.time_previous_curtain_action = time.time()
            ldr.ignored_for_lounge_blind = True
            Log.write("Started ignoring LDR for lounge blind")

    if not ldr.ignored_for_dining_curtain:
        if update_curtain(dining_curtain, want_to_be_open):
            ldr.time_previous_curtain_action = time.time()
            ldr.ignored_for_dining_curtain = True
            Log.write("Started ignoring LDR for dining curtain")

    if not ldr.ignored_for_lounge_curtain: # do lounge curtains last as they take time
        if update_curtain(lounge_curtain, want_to_be_open):
            ldr.time_previous_curtain_action = time.time()
            ldr.ignored_for_lounge_curtain = True
            Log.write("Started ignoring LDR for lounge curtain")


async def update(ldr: LDR, lounge_curtain: LoungeCurtain, lounge_blind: RemoteCurtain, dining_curtain: RemoteCurtain):
    ldr.update()
    ldr.check_stop_ignoring_lights()
    ldr.check_stop_ignoring_curtains()

    await update_lights(ldr)
    update_curtains(ldr, lounge_curtain, lounge_blind, dining_curtain)



if __name__ == "__main__":
    print("Program running, press CTRL+C to exit")
    Log.write_without_time("--------\n--------\n")
    Log.write("Program started")


    ldr = LDR()
    ldr_read_interval = 60 # number of seconds between getting a new reading from the ldr

    lounge_curtain = LoungeCurtain()
    lounge_blind = RemoteCurtain("Lounge blind", [0, 0, 1, 0], [0, 0, 1, 1], "blind_open")
    dining_curtain = RemoteCurtain("Dining curtain", [0, 1, 0, 0], [0, 1, 0, 1], "dining_open")

    remote_input_manager = RemoteInputManager(ldr, lounge_curtain, lounge_blind, dining_curtain)

    sv.load()
    Pins.init(remote_input_manager)

    timer = Timer() # set up timer running in background to read ldr periodically
    timer_thread = threading.Thread(target = timer.run, args = (update, ldr_read_interval, ldr, lounge_curtain, lounge_blind, dining_curtain), daemon = True)
    timer_thread.start()


    try:
        while True:
            time.sleep(10) # program will sit here while timer thread runs. needs seperate thread to allow input with GPIO
    except KeyboardInterrupt: # exit program when ctl+c pressed
        print("Program exited, continuing to terminal")
        print("To remove program from startup, type 'crontab -e' and remove the line containing MainControl.py")

