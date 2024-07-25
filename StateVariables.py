
import json

import Log

__vars = {}

# load state variable values from file
# need to use full file paths when running from cron
def load():
    global __vars
    with open("/home/pi/curtains/variables.json", "r") as f:
        __vars = json.load(f)


def get(name: str):
    if name in __vars:
        return __vars.get(name)
    else:
        Log.write(f"Tried to get state variable with invalid name: {name}")
        return None


def set(name: str, value):
    if name in __vars:
        __vars.update({name: value})
        __write_vars()
    else:
        Log.write(f"Tried to set state variable with invalid name: {name}")


# save vars to text file which can be loaded when program next starts to remember e.g. lights are on or off
def __write_vars():
    with open("/home/pi/curtains/variables.json", "w") as f:
        json.dump(__vars, f, indent=4)
