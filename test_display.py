from micropython import const
import machine
import lcd_bus
import lvgl as lv

_WIDTH    = const(320)
_HEIGHT   = const(240)
_BL       = const(21)
_DC       = const(2)
_MOSI     = const(13)
_MISO     = const(12)
_SCK      = const(14)
_LCD_CS   = const(15)
_LCD_FREQ = const(40000000)

spi_bus = machine.SPI.Bus(host=1, mosi=_MOSI, miso=_MISO, sck=_SCK)
display_bus = lcd_bus.SPIBus(spi_bus=spi_bus, freq=_LCD_FREQ, dc=_DC, cs=_LCD_CS)

import ili9341

# Probar BGR primero, si colores raros cambiar a BYTE_ORDER_RGB
display = ili9341.ILI9341(
    data_bus=display_bus,
    display_width=_WIDTH,
    display_height=_HEIGHT,
    backlight_pin=_BL,
    color_space=lv.COLOR_FORMAT.RGB565,
    color_byte_order=ili9341.BYTE_ORDER_BGR,
    rgb565_byte_swap=True,
)

import task_handler

display.set_power(True)
display.init(2)
display.set_backlight(100)

th = task_handler.TaskHandler()

scrn = lv.screen_active()
scrn.set_style_bg_color(lv.color_hex(0x000080), 0)  # fondo azul

# Texto grande centrado
label = lv.label(scrn)
label.set_text("LVGL9 OK\nCYD 2432S028")
label.set_style_text_color(lv.color_hex(0xFFFFFF), 0)

label.center()

# Barra roja arriba
bar = lv.obj(scrn)
bar.set_size(_WIDTH, 20)
bar.set_pos(0, 0)
bar.set_style_bg_color(lv.color_hex(0xFF0000), 0)
bar.set_style_border_width(0, 0)

# Barra verde abajo
bar2 = lv.obj(scrn)
bar2.set_size(_WIDTH, 20)
bar2.set_pos(0, _HEIGHT - 20)
bar2.set_style_bg_color(lv.color_hex(0x00FF00), 0)
bar2.set_style_border_width(0, 0)
