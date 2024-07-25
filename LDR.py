
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
        self.prediction_error_threshold = 100   # if difference between actual and predicted value is greater than this,
                                                # ignore actual value
        self.ignored_for_lights = False
        self.ignored_for_lounge_curtain = False
        self.ignored_for_lounge_blind = False
        self.ignored_for_dining_curtain = False
        self.time_previous_curtain_action = 0
        self.time_previous_lights_action = 0
        self.prev_values = [-1] * 5             # number of previous readings to store for processing
        self.trend_m = 0
        self.trend_c = 0


    def get_predicted_reading(self):
        predicted = self.trend_m * (len(self.prev_values) + 1) + self.trend_c
        return max(predicted, 0) # brightness value cannot go below 0


    def get_trend_direction(self):
        if self.trend_m > 0: return 1
        if self.trend_m < 0: return -1
        return 0


    def get_trend_valid(self):
        for i in range(0, len(self.prev_values)):
            if self.prev_values[i] == -1:
                # if the program hasnt been running long enough for prev_values be full, cannot use trend prediction
                return False
        return True


    def get_current_value(self):
        return self.prev_values[len(self.prev_values) - 1]


    def update_values(self, current_value):
        # shift previous values along by one, most recent will be at index num_prev_values-1
        num_prev_values = len(self.prev_values)
        for i in range(0, num_prev_values - 1):
            self.prev_values[i] = self.prev_values[i+1]

        # set current value
        self.prev_values[num_prev_values - 1] = current_value


    def update_trend_equation(self):
        # https://medium.com/geekculture/linear-regression-from-scratch-in-python-without-scikit-learn-a06efe5dedb6
        # https://www.desmos.com/calculator/ldunrmiw4v

        N = len(self.prev_values)
        mean_x = (N + 1) / 2 # x will be 1...N, so the mean will be the middle value
        mean_y = 0
        for i in range(0, N):
            mean_y += self.prev_values[i]
        mean_y /= N

        numer = 0
        denom = 0
        for i in range(0, N):
            x = i + 1
            numer += (x - mean_x) * (self.prev_values[i] - mean_y)
            denom += (x - mean_x) ** 2

        self.trend_m = numer / denom
        self.trend_c = mean_y - self.trend_m * mean_x


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

        #               __________(3)___________
        #              /                        \
        #            (3)                        (3)
        # -----------/----------------------------\---------------------------------- dark threshold here and below
        #           /                              \
        #         (2)                              (4)
        #         /                                  \
        #        /                                    \
        # ------/--------------------------------------\----------------------------- bright threshold here and above
        #      /                                        \
        #    (1)                                        (1)
        # ___/                                            \___________(1)____________

        trend_valid = self.get_trend_valid()
        trend_direction = self.get_trend_direction()
        current_brightness = self.get_current_value()
#        Log.write(f"trend_direction = {trend_direction}, current_brightness = {current_brightness}, lights_on/off = {self.lights_on_threshold}/{self.lights_off_threshold}, curtains_close/open = {self.curtains_close_threshold}/{self.curtains_open_threshold}, trend_m = {self.trend_m}, trend_c = {self.trend_c}")

        if current_brightness <= self.lights_on_threshold and current_brightness < self.lights_off_threshold:
            return True     # (1)

        if current_brightness > self.lights_on_threshold and current_brightness >= self.lights_off_threshold:
            return False    # (3)

        if trend_valid and trend_direction == 1:
            return False     # (2)

        if trend_valid and trend_direction == -1:
            return True    # (4)

        return None # (unlikely but) possible for trend to be 0 between thresholds, in which case the state wants to
                    # stay the same


    def check_curtains_want_to_be_open(self):
        trend_valid = self.get_trend_valid()
        trend_direction = self.get_trend_direction()
        current_brightness = self.get_current_value()

        if current_brightness <= self.curtains_close_threshold and current_brightness < self.curtains_open_threshold:
            return False    # (1)

        if current_brightness > self.curtains_close_threshold and current_brightness >= self.curtains_open_threshold:
            return True     # (3)

        if trend_valid and trend_direction == 1:
            return True     # (2)

        if trend_valid and trend_direction == -1:
            return False    # (4)

        return None


    def update(self):
        actual_reading = ReadAnalogue.read_ldr()
        trend_valid = self.get_trend_valid()
        if not trend_valid:
            self.update_values(actual_reading)
            return

        self.update_trend_equation()
        predicted_reading = self.get_predicted_reading()
        if abs(actual_reading - predicted_reading) > self.prediction_error_threshold:
            # actual reading is likely an error, ignore it and use the predicted value instead
#            Log.write(f"Actual reading ({actual_reading}) was too far from predicted reading ({predicted_reading}) and ignored")
            self.update_values(predicted_reading)
        else:
#            Log.write(f"Actual reading ({actual_reading}) was within range ({self.prediction_error_threshold}) of predicted reading ({predicted_reading})")
            self.update_values(actual_reading)
