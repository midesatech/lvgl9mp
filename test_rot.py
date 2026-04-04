from micropython import const
import machine, lcd_bus, lvgl as lv

_WIDTH=const(320); _HEIGHT=const(240); _BL=const(21); _DC=const(2)
_MOSI=const(13); _SCK=const(14); _LCD_CS=const(15); _LCD_FREQ=const(40000000)

spi_bus = machine.SPI.Bus(host=1, sck=_SCK, mosi=_MOSI, miso=-1)
display_bus = lcd_bus.SPIBus(spi_bus=spi_bus, freq=_LCD_FREQ, dc=_DC, cs=_LCD_CS)

import ili9341, task_handler

# Probar con BYTE_ORDER_RGB (no BGR) y sin byte_swap
display = ili9341.ILI9341(
    data_bus=display_bus,
    display_width=_WIDTH,
    display_height=_HEIGHT,
    backlight_pin=_BL,
    color_space=lv.COLOR_FORMAT.RGB565,
    color_byte_order=ili9341.BYTE_ORDER_RGB,
    rgb565_byte_swap=False,
)

display.set_power(True)
display.init(1)
display.set_backlight(100)

th = task_handler.TaskHandler()

scrn = lv.screen_active()
scrn.set_style_bg_color(lv.color_hex(0xFF0000), 0)  # Rojo puro

lv.label(scrn).set_text("ROJO=OK")
lv.label(scrn).center()
