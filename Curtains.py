import RPi.GPIO as GPIO
import Read_Analogue
import time
import FileManager

pulse_length = 0.125
current_limit = 35
# values obtained from testing. curtains running properly are around 10-25 (previous motor: 500-700)
# actual voltage = read value * (3.2/1024)   3.2 = supply voltage

lounge_running = False # prevent curtains from being opened/closed while already mid-way through opening/closing
dining_running = False
blind_running = False

# GPIO pins being used
pin_motor_lounge = 12
pin_relay_lounge = 18
pin_pulse_dining = 11
pin_pulse_blind = 16

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(pin_motor_lounge, GPIO.OUT)
GPIO.setup(pin_relay_lounge, GPIO.OUT)
GPIO.setup(pin_pulse_dining, GPIO.OUT)
GPIO.setup(pin_pulse_blind, GPIO.OUT)

lounge_open_timeout = 22
lounge_close_timeout = 20

def check(curtain, state, intent): # curtain = the curtain/blind to act on, state = true if currently open, false if closed, intent = what the program wants to do with the curtain
    newstate = state
    if (state == True) and (intent == 'close' or intent == 'invert'):
        newstate = closec(curtain) # functions are named closec and openc, as open is a default function in python
        return newstate
    if (state == False) and (intent == 'open' or intent == 'invert'):
        newstate = openc(curtain)
        return newstate
    return state

def openc(curtain):
    global lounge_running
    global dining_running
    global blind_running
    
    if curtain == 'lounge':
        if not lounge_running:
            lounge_running = True
            FileManager.writeLog(f"{time.ctime()}: Lounge curtains opening")
            GPIO.output(pin_relay_lounge, 1) # activate relay
            time.sleep(0.25) # 0.25 seconds
            GPIO.output(pin_motor_lounge, 1) # start motor
            time.sleep(1) # wait for in-rush to go
            start_time = time.time()
            while 1:
                time.sleep(0.05) # wait (in seconds) between checking current again
                current_pull = Read_Analogue.read_curtain_motor() # check current pull
                if current_pull > current_limit or time.time() - start_time >= lounge_open_timeout: break # exit loop and continue to next section if current is too high
                                                                                        # or enough time has passed since starting to assume automatic cut out has failed
            GPIO.output(pin_motor_lounge, 0) # stop motor
            time.sleep(0.1)
            GPIO.output(pin_relay_lounge, 0) # de-activate relay
            time.sleep(0.1) # wait a little bit before restarting the motor
            GPIO.output(pin_motor_lounge, 1) # start motor
            time.sleep(0.025) # keep motor on for 25ms
            GPIO.output(pin_motor_lounge, 0) # stop motor
            time.sleep(0.1)
            lounge_running = False
            FileManager.writeLog(f"{time.ctime()}: Lounge curtains finished opening")
            FileManager.writeVariable("lounge_open", True)
            return True # go back to where function was called, ignore rest of code below
        else:
            return False #ensure state is unchanged if curtain was running when asked to open/close
    
    if curtain == 'dining':
        if not dining_running:
            dining_running = True
            FileManager.writeLog(f"{time.ctime()}: Dining curtains opening")
            for i in range(4):
                GPIO.output(pin_pulse_dining, 1) # pulse dining pin on and off for how many times in range(#) 
                time.sleep(pulse_length)
                GPIO.output(pin_pulse_dining, 0)
                time.sleep(pulse_length)
            time.sleep(2) # wait some time to ensure curtain has finished opening before allowing it to be opened/closed again
            dining_running = False
            FileManager.writeLog(f"{time.ctime()}: Dining curtains finished opening")
            FileManager.writeVariable("dining_open", True)
            return True
        else:
            return False
    
    if curtain == 'blind':
        if not blind_running:
            blind_running = True
            FileManager.writeLog(f"{time.ctime()}: Lounge blind opening")
            for i in range(4):
                GPIO.output(pin_pulse_blind, 1) # pulse blind pin on and off for how many times in range(#)
                time.sleep(pulse_length)
                GPIO.output(pin_pulse_blind, 0)
                time.sleep(pulse_length)
            time.sleep(2)
            blind_running = False
            FileManager.writeLog(f"{time.ctime()}: Lounge blind finished opening")
            FileManager.writeVariable("blind_open", True)
            return True
        else:
            return False

def closec(curtain):
    global lounge_running
    global dining_running
    global blind_running
    
    if curtain == 'lounge':
        if not lounge_running:
            lounge_running = True
            FileManager.writeLog(f"{time.ctime()}: Lounge curtains closing")
            current_pull = 0
            GPIO.output(pin_motor_lounge, 1) # start motor
            time.sleep(1)
            start_time = time.time()
            while 1:
                time.sleep(0.05) # wait (in seconds) before checking current again. also provides time for initial current rush to be ignored
                current_pull = Read_Analogue.read_curtain_motor() # check current pull
                if current_pull > current_limit or time.time() - start_time >= lounge_close_timeout: break # exit loop and continue to next section if current is too high
            GPIO.output(pin_motor_lounge, 0) # stop motor
            time.sleep(0.1)
            GPIO.output(pin_relay_lounge, 1) # activate relay
            time.sleep(0.1) # wait a little bit before restarting the motor
            GPIO.output(pin_motor_lounge, 1) # start motor
            time.sleep(0.025) # keep motor on for 25ms
            GPIO.output(pin_motor_lounge, 0) # stop motor
            time.sleep(0.1)
            GPIO.output(pin_relay_lounge, 0) # de-activate relay
            lounge_running = False
            FileManager.writeLog(f"{time.ctime()}: Lounge curtains finished closing")
            FileManager.writeVariable("lounge_open", False)
            return False
        else:
            return True
    
    if curtain == 'dining':
        if not dining_running:
            dining_running = True
            FileManager.writeLog(f"{time.ctime()}: Dining curtains closing")
            for i in range(3):
                GPIO.output(pin_pulse_dining, 1) # pulse dining pin on and off for how many times in range(#)
                time.sleep(pulse_length)
                GPIO.output(pin_pulse_dining, 0)
                time.sleep(pulse_length)
            time.sleep(2)
            dining_running = False
            FileManager.writeLog(f"{time.ctime()}: Dining curtains finished closing")
            FileManager.writeVariable("dining_open", False)
            return False
        else:
            return True
    
    if curtain == 'blind':
        if not blind_running:
            FileManager.writeLog(f"{time.ctime()}: Lounge blind closing")
            blind_running = True
            for i in range(3):
                GPIO.output(pin_pulse_blind, 1) # pulse blind pin on and off for how many times in range(#)
                time.sleep(pulse_length)
                GPIO.output(pin_pulse_blind, 0)
                time.sleep(pulse_length)
            time.sleep(2)
            blind_running = False
            FileManager.writeLog(f"{time.ctime()}: Lounge blind finished closing")
            FileManager.writeVariable("blind_open", False)
            return False
        else:
            return True
