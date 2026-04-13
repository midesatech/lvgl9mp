# cal_simple.py - Calibracion simple sin threads
# Muestra marcas en esquinas, debug=True imprime raw al tocar
import machine, lcd_bus, lvgl as lv, task_handler, ili9341, xpt2046
from micropython import const

_ROT = const(0x20)

spi = machine.SPI.Bus(host=1, mosi=13, miso=12, sck=14)
bus = lcd_bus.SPIBus(spi_bus=spi, freq=24000000, dc=2, cs=15)
d = ili9341.ILI9341(
    data_bus=bus, display_width=320, display_height=240,
    backlight_pin=21, backlight_on_state=ili9341.STATE_PWM,
    color_space=lv.COLOR_FORMAT.RGB565,
    color_byte_order=ili9341.BYTE_ORDER_BGR,
    rgb565_byte_swap=True)
d._ORIENTATION_TABLE = (_ROT, 0, 0, 0)
d.set_rotation(lv.DISPLAY_ROTATION._0)
d.set_power(True)
d.init(1)
d.set_backlight(100)

t_spi = machine.SPI.Bus(host=2, mosi=32, miso=39, sck=25)
t_dev = machine.SPI.Device(spi_bus=t_spi, freq=2000000, cs=33)
# debug=True -> imprime: XPT2046_TP_DATA(x=RAW_X, y=RAW_Y, z=Z)
touch = xpt2046.XPT2046(device=t_dev, debug=True)

scr = lv.obj()
scr.set_style_bg_color(lv.color_hex(0x001133), 0)
scr.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
scr.set_scroll_dir(lv.DIR.NONE)

def mark(x, y, color, text):
    o = lv.obj(scr)
    o.set_size(30, 30)
    o.set_pos(x, y)
    o.set_style_bg_color(lv.color_hex(color), 0)
    o.set_style_border_width(0, 0)
    o.set_style_radius(0, 0)
    l = lv.label(scr)
    l.set_text(text)
    l.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
    l.set_pos(x + 2, y + 7)

# Marcas en las 4 esquinas y centro
mark(0,   0,   0xFF2222, "TL")
mark(290, 0,   0x22FF22, "TR")
mark(0,   210, 0x2222FF, "BL")
mark(290, 210, 0xFFFF22, "BR")
mark(145, 105, 0xFF22FF, "C")

msg = lv.label(scr)
msg.set_text("Toca TL TR BL BR C\nVer consola para raw")
msg.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
msg.set_pos(50, 50)

lv.screen_load(scr)

print("=== CALIBRACION: toca TL, TR, BL, BR, Centro ===")
print("XPT2046_TP_DATA(x=RAW_X, y=RAW_Y) son los valores del ADC")

task_handler.TaskHandler()
