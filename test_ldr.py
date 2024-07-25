import spidev

def read_ldr():
    # Open SPI bus
    spi = spidev.SpiDev()
    spi.open(0,0)
    spi.max_speed_hz=1000
    channel = 0
    
    adc = spi.xfer2( [1, (8+channel)<<4, 0] )
    data = ((adc[1]&3) << 8) + adc[2]
    
    spi.close()
    return data

while True:
    input()
    ser = read_ldr()
    V = ser / 1024 * 3.3
    R = 10000 * 3.3 / V - 10000
    print(f"serial value = {ser}, V = {V}, R = {R}");
