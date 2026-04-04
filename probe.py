import machine

# SPI.Bus: primer arg es id (int), pins son Pin objects
p_sck  = machine.Pin(14)
p_mosi = machine.Pin(13)
p_miso = machine.Pin(12)

b = machine.SPI.Bus(1, sck=p_sck, mosi=p_mosi, miso=p_miso)
print("SPI.Bus ok:", type(b))

import lcd_bus
d = lcd_bus.SPIBus(spi_bus=b, freq=40000000, dc=2, cs=15)
print("SPIBus ok:", type(d))
