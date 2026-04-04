from micropython import const
import machine, lcd_bus, lvgl as lv, task_handler, ili9341

_DISPLAY_ROT = const(0xE0)
spi_bus = machine.SPI.Bus(host=1, mosi=13, miso=12, sck=14)
indev_bus = machine.SPI.Bus(host=2, mosi=32, miso=39, sck=25)
indev_device = machine.SPI.Device(spi_bus=indev_bus, freq=2000000, cs=33)
display_bus = lcd_bus.SPIBus(spi_bus=spi_bus, freq=24000000, dc=2, cs=15)
display = ili9341.ILI9341(
    data_bus=display_bus, display_width=320, display_height=240,
    backlight_pin=21, backlight_on_state=ili9341.STATE_PWM,
    color_space=lv.COLOR_FORMAT.RGB565,
    color_byte_order=ili9341.BYTE_ORDER_BGR, rgb565_byte_swap=True,
)
display._ORIENTATION_TABLE = (_DISPLAY_ROT, 0x0, 0x0, 0x0)
display.set_rotation(lv.DISPLAY_ROTATION._0)
display.set_power(True)
display.init(1)
display.set_backlight(100)

import xpt2046
indev = xpt2046.XPT2046(device=indev_device)
task_handler.TaskHandler()

scrn = lv.screen_active()
scrn.set_style_bg_color(lv.color_hex(0x000000), 0)

lbl = lv.label(scrn)
lbl.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
lbl.set_text("w={} h={} id={}".format(
    indev._orig_width, indev._orig_height, indev.id))
lbl.center()
