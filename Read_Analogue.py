import spidev
import time
import FileManager

# honestly, not sure how this works.
# found online, tried looking up more but couldn't find much information
# but heres where i stole it from anyway
# https://www.raspberrypi-spy.co.uk/2013/10/analogue-sensors-on-the-raspberry-pi-using-an-mcp3008/
# example requires import os for controlling system volume, but we dont need it

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
    FileManager.writeLog(f"{time.ctime()}: LDR reading {data}")
    return data

def read_curtain_motor():
    # Open SPI bus
    spi = spidev.SpiDev()
    spi.open(0,0)
    spi.max_speed_hz=1000
    channel = 1
    
    adc = spi.xfer2( [1, (8+channel)<<4, 0] )
    data = ((adc[1]&3) << 8) + adc[2]
    
    spi.close()
#    print("motor value:" , data)
    return data
