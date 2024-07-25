
import shutil
import os

logdir = "/home/pi/curtains/logs"
loglist = os.listdir(logdir)
loglist.sort()

# named with date and sorted, so the newest will be last
# move all but the last (newest) one to the NAS
for i in range(len(loglist)-1):
    try:
        shutil.move(f"{logdir}/{loglist[i]}", f"/media/NAS/logs/{loglist[i]}")
    except Exception as e:
        with open(f"{logdir}/{loglist[i]}", "a") as f:
            f.write(f"Failed to copy to NAS with error:\n{e}\n")

