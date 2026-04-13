# calibrate_touch.py v5
# Borra cal incorrecta, recalibra con _normalize devolviendo raw
import machine, lcd_bus, lvgl as lv, task_handler, ili9341, xpt2046
from micropython import const

_DISPLAY_ROT = const(0x20)

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

indev_bus = machine.SPI.Bus(host=2, mosi=32, miso=39, sck=25)
indev_device = machine.SPI.Device(spi_bus=indev_bus, freq=2000000, cs=33)
indev = xpt2046.XPT2046(device=indev_device)

task_handler.TaskHandler()

print("ID:", indev.id)
print("is_calibrated:", indev.is_calibrated)

# Borrar calibracion incorrecta manualmente (erase_key no erase)
if indev.is_calibrated:
    try:
        indev._cal._config.erase_key('ts_config')
        indev._cal._config.commit()
        print("Calibracion anterior borrada OK")
    except Exception as e:
        print("Error borrando:", e)
    # Resetear en memoria
    indev._cal._alphaX = None
    indev._cal._betaX = None
    indev._cal._deltaX = None
    indev._cal._alphaY = None
    indev._cal._betaY = None
    indev._cal._deltaY = None
    indev._cal._mirrorX = None
    indev._cal._mirrorY = None

print("is_calibrated ahora:", indev.is_calibrated)

# Ahora calibrar - _normalize devuelve raw porque is_calibrated=False
result = indev.calibrate()
print("Resultado:", result)

if result:
    indev._cal._is_dirty = True
    indev._cal.save()
    print("alphaX:", indev._cal.alphaX)
    print("betaX:", indev._cal.betaX)
    print("deltaX:", indev._cal.deltaX)
    print("alphaY:", indev._cal.alphaY)
    print("betaY:", indev._cal.betaY)
    print("deltaY:", indev._cal.deltaY)
    print("GUARDADO OK - namespace XPT2046_{}".format(indev.id))
else:
    print("FALLO")
