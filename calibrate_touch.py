# calibrate_touch.py - Calibracion affine interactiva del touch
# Subir al ESP32 como main.py temporal, tocar los 3 puntos en pantalla
# La calibracion se guarda en NVS y persiste entre reinicios

import machine, lcd_bus, lvgl as lv, task_handler, ili9341, xpt2046
import pointer_framework
from micropython import const

_DISPLAY_ROT = const(0x20)

# --- Init display ---
spi_bus = machine.SPI.Bus(host=1, mosi=13, miso=12, sck=14)
display_bus = lcd_bus.SPIBus(spi_bus=spi_bus, freq=24000000, dc=2, cs=15)
display = ili9341.ILI9341(
    data_bus=display_bus,
    display_width=320, display_height=240,
    backlight_pin=21,
    backlight_on_state=ili9341.STATE_PWM,
    color_space=lv.COLOR_FORMAT.RGB565,
    color_byte_order=ili9341.BYTE_ORDER_BGR,
    rgb565_byte_swap=True,
)
display._ORIENTATION_TABLE = (_DISPLAY_ROT, 0x0, 0x0, 0x0)
display.set_rotation(lv.DISPLAY_ROTATION._0)
display.set_power(True)
display.init(1)
display.set_backlight(100)

# --- Init touch ---
indev_bus = machine.SPI.Bus(host=2, mosi=32, miso=39, sck=25)
indev_device = machine.SPI.Device(spi_bus=indev_bus, freq=2000000, cs=33)
indev = xpt2046.XPT2046(device=indev_device)

task_handler.TaskHandler()

# --- Calibrar ---
print("Iniciando calibracion affine...")
print("Toca los 3 puntos que aparecen en pantalla")

if indev.is_calibrated:
    print("Ya habia calibracion guardada - recalibrando...")

indev.calibrate()
indev._cal.save()

print("Calibracion guardada en NVS!")
print("alphaX={} betaX={} deltaX={}".format(
    indev._cal.alphaX, indev._cal.betaX, indev._cal.deltaX))
print("alphaY={} betaY={} deltaY={}".format(
    indev._cal.alphaY, indev._cal.betaY, indev._cal.deltaY))
print("mirrorX={} mirrorY={}".format(
    indev._cal.mirrorX, indev._cal.mirrorY))
print("\nListo! Reconecta el ESP32 para cargar la app normal.")
