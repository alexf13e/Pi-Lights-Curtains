from datetime import date
import time
import json

# needed a way to write to a file that was accessible from all parts of
# the program without duplicating lots of code, so here it is

# tries to connect to the NAS drive and an input message, stored in variable text
# if it failes then it writes the message to a local log file
# it was unable to write to the NAS

def writeLog(text):
    currentTime = date.today()
    with open(f"/home/pi/logs/{currentTime}.txt", "a") as f:
        f.write("\n")
        f.write(text)

def writeVariable(name, value): # text to write, line to write on (counts from 0)
    data = ""
    with open("/home/pi/Variables.txt", "r") as f:
        data = json.load(f)
    data[name] = value
    with open("/home/pi/Variables.txt", "w") as f:
        json.dump(data, f)

def loadVariables():
    with open("/home/pi/Variables.txt", "r") as f:
        data = json.load(f)
        return data

