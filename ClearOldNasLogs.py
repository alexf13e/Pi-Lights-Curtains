import os
import shutil
import time
import datetime

logdir = "/media/NAS/logs"
loglist = os.listdir(logdir)
weekago = datetime.date.today() - datetime.timedelta(days=7)

for log in loglist:
    logdatestring = os.path.splitext(log)[0]
    elements = logdatestring.split("-")
    logdate = datetime.date(int(elements[0]), int(elements[1]), int(elements[2]))
    if logdate < weekago:
        try:
            os.remove(f"{logdir}/{log}")
        except Exception as e:
            print(e) #need something to except with
