
import RPi.GPIO as GPIO
import time


# rf remote inputs
PIN_REMOTE_LOUNGE_CURTAINS = 37
PIN_REMOTE_LOUNGE_BLIND = 36
PIN_REMOTE_DINING_CURTAINS = 35
PIN_REMOTE_LIGHTS = 33

# lounge curtain pins
PIN_LOUNGE_MOTOR = 12       # hi to power motor
PIN_LOUNGE_RELAY = 18       # hi to set relay to "opening" direction
PIN_LOUNGE_SHAFT_LED = 38   # hi to power LED (used for counting pulses as motor rotates)
PIN_LOUNGE_SHAFT_COUNT= 40  # hi when able to see LED through hole in disc rotated by motor

# pins for transmitting signal to other curtains
PINS_RF_TRANSMIT = [15, 16, 13, 11] # pins used for transmitting from pi to other curtain picaxe chips
RF_TRANSMIT_DURATION = 0.75         # how long the transmission pins are held hi


def init(remote_input_manager):
    # set the GPIO pins to be used by the program
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)

    GPIO.setup(PIN_REMOTE_LOUNGE_CURTAINS, GPIO.IN)
    GPIO.setup(PIN_REMOTE_LOUNGE_BLIND, GPIO.IN)
    GPIO.setup(PIN_REMOTE_DINING_CURTAINS, GPIO.IN)
    GPIO.setup(PIN_REMOTE_LIGHTS, GPIO.IN)

    GPIO.setup(PIN_LOUNGE_MOTOR, GPIO.OUT)
    GPIO.setup(PIN_LOUNGE_RELAY, GPIO.OUT)
    GPIO.setup(PIN_LOUNGE_SHAFT_LED, GPIO.OUT)
    GPIO.setup(PIN_LOUNGE_SHAFT_COUNT, GPIO.IN)

    GPIO.setup(PINS_RF_TRANSMIT[0], GPIO.OUT)
    GPIO.setup(PINS_RF_TRANSMIT[1], GPIO.OUT)
    GPIO.setup(PINS_RF_TRANSMIT[2], GPIO.OUT)
    GPIO.setup(PINS_RF_TRANSMIT[3], GPIO.OUT)

    # register events to run the input functions when the remote is used
    add_event(PIN_REMOTE_LIGHTS, remote_input_manager.switch_lights)
    add_event(PIN_REMOTE_LOUNGE_CURTAINS, remote_input_manager.switch_lounge_curtains)
    add_event(PIN_REMOTE_LOUNGE_BLIND, remote_input_manager.switch_lounge_blind)
    add_event(PIN_REMOTE_DINING_CURTAINS, remote_input_manager.switch_dining_curtains)


def add_event(pin: int, callback):
    # used for setting input events from the rf remote in RemoteInput.py
    GPIO.add_event_detect(pin, GPIO.RISING, callback, bouncetime = 250)

def filter_input(pin: int):
    # fitler out short/random inputs
    # waits a short amount of time, then checks if the input is still high
    time.sleep(0.05)
    return GPIO.input(pin) == 1


def transmit_code(code: list[int]):
    # set transmission pins to values stated by given code
    for i in range(len(PINS_RF_TRANSMIT)):
        GPIO.output(PINS_RF_TRANSMIT[i], code[i])

    time.sleep(RF_TRANSMIT_DURATION)

    # set them back to 0
    for i in range(len(PINS_RF_TRANSMIT)):
        GPIO.output(PINS_RF_TRANSMIT[i], 0)

    time.sleep(RF_TRANSMIT_DURATION)
