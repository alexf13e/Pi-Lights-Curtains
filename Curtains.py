
from enum import IntEnum
import RPi.GPIO as GPIO
import time

import Log
import Pins
import ReadAnalogue
import StateVariables as sv


class CurtainActions(IntEnum):
    NONE = -1
    CLOSE = 0
    OPEN = 1
    INVERT = 2


class CurtainStates(IntEnum):
    CLOSED = 0
    OPEN = 1
    RUNNING = 2


class RelayDirections(IntEnum):
    CLOSE = 0
    OPEN = 1


class LoungeCurtain:
    def __init__(self):
        self.running = False # prevent curtains from being opened/closed while already mid-way through opening/closing
        self.display_name = "lounge curtain"
        self.state_variable_name = "lounge_open"
        self.open_timeout = 13 # seconds
        self.close_timeout = 13
        self.pulse_count_limit = 210
        self.current_limit = 50
        # values obtained from testing. curtains running properly are around 10-25
        # actual voltage = read value * (3.2/1024)   3.2 = supply voltage, 1024 = maximum range of values which can be read


    def request(self, desired_action: CurtainActions):
        if self.running:
            return False

        actual_action = CurtainActions.NONE
        current_state = sv.get("lounge_open")
        match current_state:
            case True:
                current_state = CurtainStates.OPEN
            case False:
                current_state = CurtainStates.CLOSED
            case _:
                return False # state_variable_name was likely not valid, will be logged by sv.get()

        if current_state == CurtainStates.OPEN and (desired_action == CurtainActions.CLOSE or desired_action == CurtainActions.INVERT):
            actual_action = CurtainActions.CLOSE
        elif current_state == CurtainStates.CLOSED and (desired_action == CurtainActions.OPEN or desired_action == CurtainActions.INVERT):
            actual_action = CurtainActions.OPEN
        else:
            # invalid request for current curtain state, do nothing
            Log.write(f"invalid curtain request for lounge: requested {desired_action.name} when state was {current_state.name}")
            return False

        match actual_action:
            case CurtainActions.OPEN:
                self.__open()
            case CurtainActions.CLOSE:
                self.__close()

        return True


    def __open(self):
        if self.running: # this function should not be called when running if using request, but check just in case
            return

        self.running = True
        Log.write("Lounge curtains open start")

        stop_reason = self.__operate(RelayDirections.OPEN)

        self.running = False
        Log.write(f"Lounge curtains finished open with reason: {stop_reason}")
        sv.set("lounge_open", True)


    def __close(self):
        if self.running:
            return

        self.running = True
        Log.write("Lounge curtains close start")

        stop_reason = self.__operate(RelayDirections.CLOSE)

        self.running = False
        Log.write(f"Lounge curtains finished close with reason: {stop_reason}")
        sv.set("lounge_open", False)


    def __operate(self, relay_direction: RelayDirections):
        current_readings = [0, 0, 0]

        ### helper functions
        def update_current_readings():
            current_readings[2] = current_readings[1]
            current_readings[1] = current_readings[0]
            current_readings[0] = ReadAnalogue.read_curtain_motor_power()

        def check_current_limit_exceeded():
            for i in range(3):
                if current_readings[i] < self.current_limit:
                    return False
            return True
        ###

        GPIO.output(Pins.PIN_LOUNGE_SHAFT_LED, 1)           # activate shaft led power
        GPIO.output(Pins.PIN_LOUNGE_RELAY, relay_direction) # set relay to desired direction
        time.sleep(0.25)                                    # 0.25 seconds for relay to activate
        GPIO.output(Pins.PIN_LOUNGE_MOTOR, 1)               # start motor
        time.sleep(1)                                       # wait for in-rush to go

        prev_pulse = 0
        pulse_count = 0
        stop_reason = ""
        start_time = time.time()
        while True:
            update_current_readings()

            # exit loop and continue to next section if current is too high
            if check_current_limit_exceeded():
                stop_reason = "current"
                break

            if time.time() - start_time >= self.open_timeout:
                stop_reason = "timeout"
                break

            current_pulse = GPIO.input(Pins.PIN_LOUNGE_SHAFT_COUNT)
            if current_pulse == 1 and prev_pulse == 0:
                pulse_count += 1
                if pulse_count >= self.pulse_count_limit:
                    stop_reason = "pulse"
                    break

            prev_pulse = current_pulse

        GPIO.output(Pins.PIN_LOUNGE_MOTOR, 0)
        GPIO.output(Pins.PIN_LOUNGE_SHAFT_LED, 0)

        if stop_reason == "current" or stop_reason == "timeout":
            # curtains were stopped by current or time, likely want to reverse track a little
            time.sleep(0.25)
            GPIO.output(Pins.PIN_LOUNGE_RELAY, 1 - relay_direction)   # relay to opposite direction
            time.sleep(0.1)                         # wait for relay to change
            GPIO.output(Pins.PIN_LOUNGE_MOTOR, 1)   # start motor
            time.sleep(0.025)                       # keep motor on for 25ms
            GPIO.output(Pins.PIN_LOUNGE_MOTOR, 0)   # stop motor

        return stop_reason



class RemoteCurtain:
    def __init__(self, display_name, code_close, code_open, state_variable_name):
        self.display_name = display_name
        self.state_variable_name = state_variable_name
        self.running = False
        self.code_close = code_close
        self.code_open = code_open


    def request(self, desired_action: CurtainActions):
        if self.running:
            return False

        actual_action = CurtainActions.NONE
        current_state = sv.get(self.state_variable_name)
        match current_state:
            case True:
                current_state = CurtainStates.OPEN
            case False:
                current_state = CurtainStates.CLOSED
            case _:
                return False

        if current_state == CurtainStates.OPEN and (desired_action == CurtainActions.CLOSE or desired_action == CurtainActions.INVERT):
            actual_action = CurtainActions.CLOSE
        elif current_state == CurtainStates.CLOSED and (desired_action == CurtainActions.OPEN or desired_action == CurtainActions.INVERT):
            actual_action = CurtainActions.OPEN
        else:
            # invalid request for current curtain state, do nothing
            Log.write(f"invalid curtain request for {self.display_name}: requested {desired_action.name} when state was {current_state.name}")
            return False

        self.__operate(actual_action)
        return True


    def __operate(self, action: CurtainActions):
        if self.running:
            return

        self.running = True
        Log.write(f"{self.display_name} {action.name} start")

        if action == CurtainActions.OPEN:
            Pins.transmit_code(self.code_open)
        else:
            Pins.transmit_code(self.code_close)

        self.running = False
        Log.write(f"{self.display_name} finished {action.name}")
        sv.set(self.state_variable_name, action == CurtainActions.OPEN)
