
import spidev
import time

import Log

# https://www.raspberrypi-spy.co.uk/2013/10/analogue-sensors-on-the-raspberry-pi-using-an-mcp3008/

# Function to read SPI data from MCP3008 chip
# Channel must be an integer 0-7
def read_ldr():
    # Open SPI bus
    spi = spidev.SpiDev()
    spi.open(0,0)
    spi.max_speed_hz=1000
    channel = 0

    adc = spi.xfer2( [1, (8+channel)<<4, 0] )
    data = ((adc[1]&3) << 8) + adc[2]

    spi.close()
    Log.write(f"LDR reading {data}")
    return data

def read_curtain_motor_power():
    # Open SPI bus
    spi = spidev.SpiDev()
    spi.open(0,0)
    spi.max_speed_hz=1000
    channel = 1

    adc = spi.xfer2( [1, (8+channel)<<4, 0] )
    data = ((adc[1]&3) << 8) + adc[2]

    spi.close()
    # print("motor value:" , data)
    return data
