# Pi-Lights-Curtains
A system for controlling Wi-Fi plugs and remote motors with a Raspberry Pi

This project was started in October 2019 and has been updated and improved over time (most recently in May 2022).
The system itself was an upgrade to an older one using just a PICAXE to automatically open/close curtains based on the time of day.
It uses a light dependant resistor connected to the GPIO of a Raspberry Pi to get data about the brightness outside and decide when to interact with the lights and curtains.

One of the curtain motors is directly connected to the Pi through the GPIO pins, another is connected to a PICAXE on the other side of the room, and a third all-in-one unit
controls a blind. The Pi communicates with the remote units through RF transmitters and receivers and can tell each one to individually open/close. The local and remote
curtain units have circuits for monitoring the current draw of the motors to automatically stop and reverse a little when fully open/closed to release tension.

The Pi (specifically a Raspberry Pi Zero W) uses Wi-Fi to connect to the plugs and turn them on or off, through the python-kasa library (https://github.com/python-kasa/python
kasa). Previous versions of the program had simply used sockets with help from this article (https://blog.georgovassilis.com/2016/05/07/controlling-the-tp-link-hs100-wi-fi
smart-plug/), but in an attempt to remedy some reliability issues (which were later discovered to be caused by unrelated network issues), I moved to the library and had no
reason to move back.

The system can also be controlled directly with an RF remote, which can toggle the curtains and blinds individually and all of the lights together.
