
from datetime import datetime
import time

import Log
import ReadAnalogue


class LDR:
    def __init__(self):
        self.lights_off_threshold = 150         # brightness values above/below which something should happen
        self.lights_on_threshold = 260
        self.curtains_open_threshold = 130
        self.curtains_close_threshold = 150
        self.ignore_duration = 60 * 60         # number of seconds to ignore the LDR for after an action occurs
        self.ignored_for_lights = False
        self.ignored_for_lounge_curtain = False
        self.ignored_for_lounge_blind = False
        self.ignored_for_dining_curtain = False
        self.time_previous_curtain_action = 0
        self.time_previous_lights_action = 0
        self.prev_values = [-1] * 5             # number of previous readings to store for processing


    def update(self):
        # shift previous values along by one, most recent will be at index num_prev_values-1
        num_prev_values = len(self.prev_values)
        for i in range(0, num_prev_values - 1):
            self.prev_values[i] = self.prev_values[i+1]

        # set current value
        self.prev_values[num_prev_values - 1] = ReadAnalogue.read_ldr()


    def check_stop_ignoring_lights(self):
        if self.ignored_for_lights and time.time() - self.time_previous_lights_action >= self.ignore_duration:
            self.ignored_for_lights = False
            Log.write("Stopping ignoring LDR for lights")


    def check_stop_ignoring_curtains(self):
        ignored = self.ignored_for_lounge_curtain or self.ignored_for_lounge_blind or self.ignored_for_dining_curtain
        if ignored and time.time() - self.time_previous_curtain_action >= self.ignore_duration:
            self.ignored_for_lounge_curtain = False
            self.ignored_for_lounge_blind = False
            self.ignored_for_dining_curtain = False
            Log.write("Stopping ignoring LDR for curtains")


    def check_lights_want_to_be_on(self):
        # lights want to be off it is morning and all previous values have been brighter than lights_off_threshold
        # lights want to be on if it is evening and all previous values have been darker than lights_on_threshold
        current_hour = datetime.now().hour # current hour, 0-23
        if current_hour < 12:
            for val in self.prev_values:
                if val < self.lights_off_threshold or val == -1:
                    return None # not all values bright enough, so do nothing
            return False # no longer dark, lights want to be off
        else:
            for val in self.prev_values:
                if val > self.lights_on_threshold or val == -1:
                    return None
            return True


    def check_curtains_want_to_be_open(self):
        # curtains want to be open it is morning and all previous values have been brighter than curtains_open_threshold
        # curtains want to be closed if it is evening and all previous values have been darker than curtains_close_threshold
        current_hour = datetime.now().hour
        if current_hour < 12:
            for val in self.prev_values:
                if val < self.curtains_open_threshold or val == -1:
                    return None
            return True
        else:
            for val in self.prev_values:
                if val > self.curtains_close_threshold or val == -1:
                    return None
            return False
