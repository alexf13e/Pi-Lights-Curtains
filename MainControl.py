import RPi.GPIO as GPIO
import time
import threading
import asyncio
import Read_Analogue
import Lights
import Curtains
import FileManager
import socket
import json
import distutils
from distutils import util

def pin_active_check(channel):
    # when input is detected, checks that the signal lasts long enough to be intended before calling the function to act on the input
    #checks if input is already doing something to prevent issues from buttons being pressed too often
    #print(f"detected input on {channel}")
    time.sleep(0.05) # time input must be sustained to be considered
    if GPIO.input(channel) == 1:
        #print(f"input on {channel} lasted long enough")
        get_input(channel)

def get_input(channel):
# must state that the variables declared outside the function are where
# values want to be set (otherwise a new unrelated variable will be created
# with the same name)
    global lounge_open
    global dining_open
    global blind_open
    global lights_are_on
    global ignore_ldr_lights
    global ignore_ldr_lounge_curtains
    global ignore_ldr_lounge_blind
    global ignore_ldr_dining_curtains
    global ignore_ldr_start_value
    global time_previous_lights_action
    global time_previous_curtain_action
    
    # save curent ldr value for comparison later when reactivating ldr
    ignore_ldr_start_value = ldr_values[0]
    
    if channel == pin_remote_lights:
        if lights_are_on:
            asyncio.run(Lights.Off()) # asyncio.run needed for running lights functions, as they are "asynchronous" by how the library is made.
            lights_are_on = False
            FileManager.writeLog(f"{time.ctime()}: Lights turned off by remote")
            if not ignore_ldr_lights: FileManager.writeLog(f"{time.ctime()}: LDR now ignored for lights")
            ignore_ldr_lights = True
            time_previous_lights_action = time.time()
            return
         
        if not lights_are_on:
            asyncio.run(Lights.On())
            lights_are_on = True
            FileManager.writeLog(f"{time.ctime()}: Lights turned on by remote")
            if not ignore_ldr_lights: FileManager.writeLog(f"{time.ctime()}: LDR now ignored for lights")
            ignore_ldr_lights = True
            time_previous_lights_action = time.time()
            return
    
    if channel == pin_remote_lounge_curtains:
        time.sleep(1.25) # allow remote to finish sending to avoid interference
        lounge_open = Curtains.check('lounge', lounge_open, 'invert') # tell program to think that the lounge curtains are open or closed based on what the function returns (same for blind and dining)
        if lounge_open: FileManager.writeLog(f"{time.ctime()}: Lounge curtains opened by remote")
        else: FileManager.writeLog(f"{time.ctime()}: Lounge curtains closed by remote")
        if not ignore_ldr_lounge_curtains: FileManager.writeLog(f"{time.ctime()}: LDR now ignored for lounge curtains")
        ignore_ldr_lounge_curtains = True
        time_previous_curtain_action = time.time()
        return
    
    if channel == pin_remote_lounge_blind:
        time.sleep(1.25) # allow remote to finish sending to avoid interference
        blind_open = Curtains.check('blind', blind_open, 'invert')
        if blind_open: FileManager.writeLog(f"{time.ctime()}: Lounge blind opened by remote")
        else: FileManager.writeLog(f"{time.ctime()}: Lounge blind closed by remote")
        if not ignore_ldr_lounge_blind: FileManager.writeLog(f"{time.ctime()}: LDR now ignored for lounge blind")
        ignore_ldr_lounge_blind = True
        time_previous_curtain_action = time.time()
        return
    
    if channel == pin_remote_dining_curtains:
        time.sleep(1.25) # allow remote to finish sending to avoid interference
        dining_open = Curtains.check('dining', dining_open, 'invert')
        if dining_open: FileManager.writeLog(f"{time.ctime()}: Dining curtains opened by remote")
        else: FileManager.writeLog(f"{time.ctime()}: Dining curtains closed by remote")
        if not ignore_ldr_dining_curtains: FileManager.writeLog(f"{time.ctime()}: LDR now ignored for dining curtains")
        ignore_ldr_dining_curtains = True
        time_previous_curtain_action = time.time()
        return

def areFalling(values):
    for i in range(0, len(values)-1):
        if values[i] >= values[i+1] or values[i] < 100: #prevent small changes when dark from turning the lights on
            return False
    return True # only return true if all values in the set are falling. as soon as one value is higher than the last, return false

def areRising(values):
    for i in range(0, len(values)-1):
        if values[i] <= values[i+1] or values[i] == 0:
            return False
    return True # same as above, but for rising instead of falling. also return false if any values are 0, as this causes issues on start where the program thinks values are rising when they may not be

def checkStopIgnoreLDR(lastLDRValue, darkerLevel, lighterLevel, actionTime):
    # if either the bright or dark light levels have been crossed for either the curtains or lights, the ldr values should start being listened to again
    #if (((lastLDRValue > lighterLevel and ignore_ldr_start_value < lighterLevel)
    #or (lastLDRValue < lighterLevel and ignore_ldr_start_value > lighterLevel)
    #or (lastLDRValue > darkerLevel and ignore_ldr_start_value < darkerLevel)
    #or (lastLDRValue < darkerLevel and ignore_ldr_start_value > darkerLevel))
    #and time.time() - actionTime >= actionDelay): return True
    if time.time() - actionTime >= actionDelay: return True
    # otherwise, continue ignoring
    else: return False
    
def read():
    global ldr_values
    global lounge_open
    global dining_open
    global blind_open
    global lights_are_on
    global ignore_ldr_lights
    global ignore_ldr_lounge_curtains
    global ignore_ldr_lounge_blind
    global ignore_ldr_dining_curtains
    global time_previous_lights_action
    global time_previous_curtain_action
    
    for i in range(len(ldr_values)-1, 0, -1):
        ldr_values[i] = ldr_values[i-1]
    
    ldr_values[0] = Read_Analogue.read_ldr()
    ldr_values_rising = areRising(ldr_values)
    ldr_values_falling = areFalling(ldr_values)
    
    #if ignore_ldr_start_value != -1: # if a button has been pressed since starting the program
        #if it is now light and the button was pressed when it was dark (or vice versa)
    if ignore_ldr_lights and checkStopIgnoreLDR(ldr_values[0], lights_on_value, lights_off_value, time_previous_lights_action):
        ignore_ldr_lights = False
        FileManager.writeLog(f"{time.ctime()}: LDR no longer ignored for lights")
    
    if (ignore_ldr_lounge_curtains or ignore_ldr_lounge_blind or ignore_ldr_dining_curtains) and checkStopIgnoreLDR(ldr_values[0], curtains_close_value, curtains_open_value, time_previous_curtain_action):
        ignore_ldr_lounge_curtains = False
        ignore_ldr_lounge_blind = False
        ignore_ldr_dining_curtains = False
        FileManager.writeLog(f"{time.ctime()}: LDR no longer ignored for curtains")
        
    if not ignore_ldr_lights:
        # if the last value is in the desired range, and it is getting darker
        if (ldr_values[0] < lights_on_value) and ldr_values_falling and (not lights_are_on): # check ldr value is stable and in the desired range for setting lights on or off
            asyncio.run(Lights.On())
            lights_are_on = True
            FileManager.writeVariable("lights_are_on", lights_are_on)
            FileManager.writeLog(f"{time.ctime()}: Lights turned on by LDR")
            ignore_ldr_lights = True
            time_previous_lights_action = time.time()
        # if the last value is in the desired range, and it is getting lighter
        if (ldr_values[0] > lights_off_value) and ldr_values_rising and lights_are_on:
            asyncio.run(Lights.Off())
            lights_are_on = False
            FileManager.writeVariable("lights_are_on", lights_are_on)
            FileManager.writeLog(f"{time.ctime()}: Lights turned off by LDR")
            ignore_ldr_lights = True
            time_previous_lights_action = time.time()
    
    if (ldr_values[0] > curtains_open_value) and ldr_values_rising: # check ldr value is stable and in the desired range for opening/closing curtains
        # checks that the curtain is ok to open, opens it, tells program it is open
        if not (ignore_ldr_dining_curtains or dining_open):
            dining_open = Curtains.check('dining', dining_open, 'open')
            FileManager.writeVariable("dining_open", dining_open)
            FileManager.writeLog(f"{time.ctime()}: Dining curtains opened by LDR")
            ignore_ldr_dining_curtains = True
            time_previous_curtain_action = time.time()
        
        if not (ignore_ldr_lounge_blind or blind_open):
            blind_open = Curtains.check('blind', blind_open, 'open')
            FileManager.writeVariable("blind_open", blind_open)
            FileManager.writeLog(f"{time.ctime()}: Lounge blind opened by LDR")
            ignore_ldr_lounge_blind = True
            time_previous_curtain_action = time.time()
        
        if not (ignore_ldr_lounge_curtains or lounge_open):
            lounge_open = Curtains.check('lounge', lounge_open, 'open')
            FileManager.writeVariable("lounge_open", lounge_open)
            FileManager.writeLog(f"{time.ctime()}: Lounge curtains opened by LDR")
            ignore_ldr_lounge_curtains = True
            time_previous_curtain_action = time.time()

      
    if (ldr_values[0] < curtains_close_value) and ldr_values_falling:
        # checks that the curtain is ok to close, closes it, tells program it is closed
        if (not ignore_ldr_dining_curtains) and dining_open:
            dining_open = Curtains.check('dining', dining_open, 'close')
            FileManager.writeVariable("dining_open", dining_open)
            FileManager.writeLog(f"{time.ctime()}: Dining curtains closed by LDR")
            ignore_ldr_dining_curtains = True
            time_previous_curtain_action = time.time()
            
        if (not ignore_ldr_lounge_blind) and blind_open:
            blind_open = Curtains.check('blind', blind_open, 'close')
            FileManager.writeVariable("blind_open", blind_open)
            FileManager.writeLog(f"{time.ctime()}: Lounge blind closed by LDR")
            ignore_ldr_lounge_blind = True
            time_previous_curtain_action = time.time()
            
        if (not ignore_ldr_lounge_curtains) and lounge_open:
            lounge_open = Curtains.check('lounge', lounge_open, 'close')
            FileManager.writeVariable("lounge_open", lounge_open)
            FileManager.writeLog(f"{time.ctime()}: Lounge curtains closed by LDR")
            ignore_ldr_lounge_curtains = True
            time_previous_curtain_action = time.time()

def rc_get(param):
    if param[0] == 'all':
        return fileVarsDict
    else:
        output = {}
        for varName in param:
            if varName in fileVarsDict:
                output[varName] = globals()[varName]
            else:
                output[varName] = "does not exist"
        return output

def rc_set(param):
    global fileVarsDict
    output = {}
    if param[0] in fileVarsDict:
        if isinstance(globals()[param[0]], bool):
            globals()[param[0]] = bool(distutils.util.strtobool(param[1]))
        elif isinstance(globals()[param[0]], int):
            globals()[param[0]] = int(param[1])
        else:
            globals()[param[0]] = param[1]
        fileVarsDict[param[0]] = globals()[param[0]]
        FileManager.writeVariable(param[0], globals()[param[0]])
        output[param[0]] = f"Set to {globals()[param[0]]}"
        if param[0] == "ldr_read_delay":
            createTimerThread()
    else:
        output[param[0]] = "does not exist"
    return output

def rc_run():
    endConnection = False
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            print("Waiting for connection")
            s.bind((HOST, PORT))
            s.listen(1)
            conn, addr = s.accept()
            with conn:
                print("Connected to from", addr)
                while not endConnection:
                    try:
                        data = conn.recv(1024)
                        if not data:
                            print("Received no data, ending connection")
                            endConnection = True
                        else:
                            # act on data here ----------------------
                            data = data.decode("utf-8")
                            splitData = data.split()
                            print(f"Received: {splitData}")
                            if len(splitData) <= 1:
                                returnData = {f"{splitData[0]}" : "Bad Command"}
                            else:
                                command = splitData.pop(0)
                                params = splitData.copy()
                                returnData = commandFunctions[command](params)
                            returnData = json.dumps(returnData)
                            conn.sendall(bytearray(returnData, "utf-8"))
                    except Exception as e:
                        print(f"Lost connection without proper exit, exception: {e}")
                        endConnection = True
            print("Connection Ended")
            endConnection = False
            time.sleep(3)
 
def rc_switch(param):
    output = {}
    if param[0] == "lights":
        get_input(pin_remote_lights)
        output[param[0]] = "succeded"
    elif param[0] == "dining_curtain":
        get_input(pin_remote_dining_curtains)
        output[param[0]] = "succeded"
    elif param[0] == "lounge_blind":
        get_input(pin_remote_lounge_blind)
        output[param[0]] = "succeded"
    elif param[0] == "lounge_curtain":
        get_input(pin_remote_lounge_curtains)
        output[param[0]] = "succeded"
    else:
        output[param[0]] = "failed"
    return output
            
class timer:
    def __init__(self):
        self._exit = threading.Event()
    def terminate(self):
        self._exit.set()
    def run(self, delay):
        while not self._exit.is_set():
            read()
            #print(time.time())
            time.sleep(delay)

def createTimerThread():
    global timer_thread
    global ldr_timer
    ldr_timer.terminate()
    ldr_timer = timer()
    timer_thread = threading.Thread(target = ldr_timer.run, args = (ldr_read_delay,), daemon = True)
    timer_thread.start()

print("Program running, press CTRL+C to exit")
FileManager.writeLog("--------\n--------\n")
FileManager.writeLog(f"{time.ctime()}: Program started")

fileVarsDict = FileManager.loadVariables()
# Variables that may want changing. These load from a file on startup and can be changed remotely {
lights_off_value = fileVarsDict["lights_off_value"] #150
lights_on_value = fileVarsDict["lights_on_value"] #250
curtains_open_value = fileVarsDict["curtains_open_value"] #150
curtains_close_value = fileVarsDict["curtains_close_value"] #150
lounge_open = fileVarsDict["lounge_open"] #False
dining_open = fileVarsDict["dining_open"] #False
blind_open = fileVarsDict["blind_open"] #False
lights_are_on = fileVarsDict["lights_are_on"] #False
ldr_read_delay = fileVarsDict["ldr_read_delay"] #300 # delay in seconds between reading ldr
Curtains.pulse_length = fileVarsDict["Curtains.pulse_length"]
Curtains.current_limit = fileVarsDict["Curtains.current_limit"]
Curtains.lounge_open_timeout = fileVarsDict["Curtains.lounge_open_timeout"]
Curtains.lounge_close_timeout = fileVarsDict["Curtains.lounge_close_timeout"]
# }

# Variables that may want changing. These reset to hard values on startup, and can be changed remotely {
ignore_ldr_lounge_curtains = False
ignore_ldr_lounge_blind = False
ignore_ldr_dining_curtains = False
ignore_ldr_lights = False
ignore_ldr_start_value = -1 # placeholder value for if remote is never used
time_previous_curtain_action = 0
time_previous_lights_action = 0
actionDelay = 60 * 60
# }

# Variables that most likely don't want changing. Can NOT be changed remotely {
pin_remote_lounge_curtains = 35 # GPIO pins
pin_remote_lounge_blind = 33
pin_remote_dining_curtains = 15
pin_remote_lights = 13
ldr_values = [0,0] # keep track of the last 2 ldr readings
HOST = ''
PORT = 54000
commandFunctions = {
    "get" : rc_get,
    "set" : rc_set,
    "switch" : rc_switch
    }
ldr_timer = timer() # set up timer running in background to read ldr periodically (runs function at top of program)
timer_thread = threading.Thread(target = ldr_timer.run, args = (ldr_read_delay,), daemon = True)
timer_thread.start()
remote_control_thread = threading.Thread(target = rc_run, daemon=True)
remote_control_thread.start()
# }

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(pin_remote_lounge_curtains, GPIO.IN) # lounge curtains
GPIO.setup(pin_remote_lounge_blind, GPIO.IN) # lounge blind
GPIO.setup(pin_remote_dining_curtains, GPIO.IN) # dining manual open
GPIO.setup(pin_remote_lights, GPIO.IN) # remote lights

# runs a function when a button on the remote is pressed to check which channel the input was on (pin_active_check(), near top of program)
GPIO.add_event_detect(pin_remote_lounge_curtains, GPIO.RISING, pin_active_check, bouncetime = 1000)
GPIO.add_event_detect(pin_remote_lounge_blind, GPIO.RISING, pin_active_check, bouncetime = 1000)
GPIO.add_event_detect(pin_remote_dining_curtains, GPIO.RISING, pin_active_check, bouncetime = 1000)
GPIO.add_event_detect(pin_remote_lights, GPIO.RISING, pin_active_check, bouncetime = 1000)

try:
    while True:
        time.sleep(10) # program will sit here while timer thread runs. needs seperate thread to allow input with GPIO
except KeyboardInterrupt: # exit program when ctl+c pressed
    print("Program exited, continuing to terminal")
    print("To remove program from startup, type 'sudo crontab -e' and remove the program from the bottom of the file")

