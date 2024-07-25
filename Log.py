from datetime import date
import time

# write a log entry to the local log file. this will be uploaded to NAS every day, and a new file is created each day
# need to use full file paths for running with cron
def write_without_time(text: str):
    current_date = date.today()
    with open(f"/home/pi/curtains/logs/{current_date}.txt", "a") as f:
        f.write(f"{text}\n")


def write(text: str):
    current_date = date.today()
    current_time = time.ctime()
    with open(f"/home/pi/curtains/logs/{current_date}.txt", "a") as f:
        f.write(f"{current_time}: {text}\n")
#    print(f"{current_time}: {text}")
