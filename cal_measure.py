# cal_measure.py - Calibracion simple: toca las 4 esquinas
# Usa el driver XPT2046 con debug=True para ver raw + coords LVGL
# Orden: TL (arriba-izq), TR (arriba-der), BL (abajo-izq), BR (abajo-der)

import machine
import lcd_bus
import lvgl as lv
import task_handler
import ili9341
import xpt2046
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
# debug=True imprime: XPT2046_TP_DATA(x=RAW_X, y=RAW_Y, z=Z)
# y luego:            XPT2046(raw_x=NORM_X, raw_y=NORM_Y, x=LVGL_X, y=LVGL_Y)
touch = xpt2046.XPT2046(device=indev_device, debug=True)

scr = lv.obj()
scr.set_style_bg_color(lv.color_hex(0x001133), 0)

# Instruccion
msg = lv.label(scr)
msg.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
msg.set_pos(20, 90)
msg.set_text("Toca las 4 esquinas\nTL -> TR -> BL -> BR\nVer consola para raw")

# Marcadores visuales en las esquinas
def corner_mark(x, y, color, text):
    o = lv.obj(scr)
    o.set_size(20, 20)
    o.set_pos(x, y)
    o.set_style_bg_color(lv.color_hex(color), 0)
    o.set_style_border_width(0, 0)
    o.set_style_radius(0, 0)
    l = lv.label(scr)
    l.set_text(text)
    l.set_style_text_color(lv.color_hex(color), 0)
    l.set_pos(x + 22, y + 2)

corner_mark(0,   0,   0xFF4444, "TL")
corner_mark(300, 0,   0x44FF44, "TR")
corner_mark(0,   220, 0x4444FF, "BL")
corner_mark(300, 220, 0xFFFF44, "BR")

# Label que muestra la ultima coord LVGL
coord_lbl = lv.label(scr)
coord_lbl.set_style_text_color(lv.color_hex(0x00FF88), 0)
coord_lbl.set_pos(20, 180)
coord_lbl.set_text("LVGL: -")

count = [0]
labels = ["TL", "TR", "BL", "BR", "CENTRO"]

def on_press(e):
    indev = lv.indev_active()
    if indev is None:
        return
    pt = lv.point_t()
    indev.get_point(pt)
    n = count[0] % len(labels)
    print("[LVGL-{}] x={} y={}".format(labels[n], pt.x, pt.y))
    coord_lbl.set_text("LVGL[{}]: x={} y={}".format(labels[n], pt.x, pt.y))
    count[0] += 1

scr.add_event_cb(on_press, lv.EVENT.PRESSED, None)
scr.add_flag(lv.obj.FLAG.CLICKABLE)
lv.screen_load(scr)

print("\n=== CALIBRACION - toca TL, TR, BL, BR, CENTRO ===")
print("XPT2046_TP_DATA = valores RAW del ADC")
print("XPT2046(raw_x,raw_y) = despues de _normalize")
print("LVGL[XX] = coordenada final en pantalla\n")

task_handler.TaskHandler()
