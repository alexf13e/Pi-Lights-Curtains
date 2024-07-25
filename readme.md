
## Pi-Lights-Curtains

Program for running a system to control lights and curtains automatically or via RF remote.

The system runs on a Raspberry Pi Zero W, along with two PICAXE chips which are controlled by the Pi. The PICAXE chips run BASIC code which waits for a specific RF signal from the Pi, and performs the action (open/close) specified by the signal. The chips do so by enabling power to a motor, using a relay to control the direction.

The Pi periodically checks a value from an LDR to see how bright it is outside, and determines whether the lights should be on or off, and the curtains open or closed. If the desired state is not the current one, it performs the respective action (e.g. if it is dark and the lights are off, turn them on, but do nothing if they are already on).

The LDR can be overridden with an RF remote with a button to toggle the state of the lights and each curtain. The LDR is ignored for a period of time after an action is taken to prevent fluctuations in light level from causing a back-and-forth between states, and so the manual action isn't immediately reverted.

The Pi uses cron to automatically run the program at reboot, as well as manage moving log files to a NAS drive, and removing those older than 7 days. These have been useful for finding issues which would otherwise be difficult to track, as the program is running 24/7, as well as adjusting light and dark thresholds. A new log file is created each day, and the previous day's file uploaded just after midnight. Log files are not written to directly on the NAS as this was preventing it from being able to ever sleep due to logging the light level at each reading, and knowing the light level when an issue arises is too important to remove.

The state of the lights and curtains is saved to a file (variables.json) so that if the program restarts, it can remember the state from the previous time it ran. Additional safeguards are also in place to prevent issues with the curtains trying to move to the state they are already in. Specifically the current pull of the motor is monitored and power is cut off if this is too high, and a timeout is also implemented. In normal operation a disc with holes cut out spins with the motor. An LED shines through the holes, and the number of pulses is counted to determine the distance the curtain has travelled with power being cut when it passes a specified value (these measures are used for the lounge and dining curtains, the blind has a different controller which detects when it is fully open/closed).