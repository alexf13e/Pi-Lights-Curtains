
import asyncio
import time

from Curtains import LoungeCurtain, RemoteCurtain, CurtainActions
from LDR import LDR
import Lights
import Log
import Pins
import StateVariables as sv


class RemoteInputManager:
    def __init__(self, ldr: LDR, lounge_curtain: LoungeCurtain, lounge_blind: RemoteCurtain, dining_curtain: RemoteCurtain):
        # references to ldr and curtains defined in MainControl.py
        self.ldr_ref = ldr
        self.lounge_curtain_ref = lounge_curtain
        self.lounge_blind_ref = lounge_blind
        self.dining_curtain_ref = dining_curtain


    def switch_lights(self, pin: int):
        if not Pins.filter_input(pin):
            return

        Log.write("Remote requested lights")
        if sv.get("lights_are_on"):
            asyncio.run(Lights.turn_off()) # because running from an event, cannot await
        else:
            asyncio.run(Lights.turn_on())

        self.ldr_ref.ignored_for_lights = True
        self.ldr_ref.time_previous_lights_action = time.time()
        Log.write("Started ignoring LDR for lights")


    def switch_lounge_curtains(self, pin: int):
        Log.write("Remote requested lounge curtain")
        if self.request_curtain_invert(pin, self.lounge_curtain_ref):
            # only run this if the pin input filter passed and the curtain request actually succeded
            self.ldr_ref.ignored_for_lounge_curtain = True
            self.ldr_ref.time_previous_curtain_action = time.time()
            Log.write(f"Started ignoring LDR for lounge curtains")
        else:
            Log.write("remote lounge curtain filtered out")


    def switch_lounge_blind(self, pin: int):
        Log.write("Remote requested lounge blind")
        if self.request_curtain_invert(pin, self.lounge_blind_ref):
            self.ldr_ref.ignored_for_lounge_blind = True
            self.ldr_ref.time_previous_curtain_action = time.time()
            Log.write(f"Started ignoring LDR for lounge blind")
        else:
            Log.write("remote lounge blind filtered out")


    def switch_dining_curtains(self, pin: int):
        Log.write("Remote requested dining curtain")
        if self.request_curtain_invert(pin, self.dining_curtain_ref):
            self.ldr_ref.ignored_for_dining_curtain = True
            self.ldr_ref.time_previous_curtain_action = time.time()
            Log.write(f"Started ignoring LDR for dining curtains")
        else:
            Log.write("remote dining curtain filtered out")


    def request_curtain_invert(self, pin: int, curtain: LoungeCurtain | RemoteCurtain):
        if not Pins.filter_input(pin):
            return False

        time.sleep(1.25) # allow remote to finish sending to avoid interference with pi sending rf to curtain module
        return curtain.request(CurtainActions.INVERT) # return whether request was actually carried out
