# touch_diag.py - Diagnostico completo del touch
# Muestra: raw X/Y, coordenadas normalizadas, y donde LVGL cree que tocaste
# Subir al ESP32 y correr desde Thonny o: mpremote run touch_diag.py

import machine
import lcd_bus
import lvgl as lv
import task_handler
import ili9341
import xpt2046
import pointer_framework
import time
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

# --- Init touch con debug=True para ver raw coords ---
indev_bus = machine.SPI.Bus(host=2, mosi=32, miso=39, sck=25)
indev_device = machine.SPI.Device(spi_bus=indev_bus, freq=2000000, cs=33)
touch = xpt2046.XPT2046(device=indev_device, debug=True)

# --- UI: pantalla con cruz en el centro y en las esquinas ---
scr = lv.obj()
scr.set_style_bg_color(lv.color_hex(0x000000), 0)

def make_cross(x, y, label_text, color=0xFFFFFF):
    """Dibuja una cruz en (x,y) con etiqueta"""
    h = lv.line(scr)
    h.set_points([{"x": x-10, "y": y}, {"x": x+10, "y": y}], 2)
    h.set_style_line_color(lv.color_hex(color), 0)
    h.set_style_line_width(2, 0)
    v = lv.line(scr)
    v.set_points([{"x": x, "y": y-10}, {"x": x, "y": y+10}], 2)
    v.set_style_line_color(lv.color_hex(color), 0)
    v.set_style_line_width(2, 0)
    lbl = lv.label(scr)
    lbl.set_text(label_text)
    lbl.set_style_text_color(lv.color_hex(color), 0)
    lbl.set_pos(x + 3, y + 3)

# Cruces en las 4 esquinas y centro
make_cross(10,  10,  "TL", 0xFF0000)   # Top-Left     rojo
make_cross(310, 10,  "TR", 0x00FF00)   # Top-Right    verde
make_cross(10,  230, "BL", 0x0000FF)   # Bot-Left     azul
make_cross(310, 230, "BR", 0xFFFF00)   # Bot-Right    amarillo
make_cross(160, 120, "C",  0xFF00FF)   # Centro       magenta

# Etiqueta de estado
status = lv.label(scr)
status.set_text("Toca las cruces")
status.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
status.set_pos(60, 100)

# Punto que sigue el toque
dot = lv.obj(scr)
dot.set_size(8, 8)
dot.set_style_bg_color(lv.color_hex(0xFF8800), 0)
dot.set_style_radius(4, 0)
dot.set_style_border_width(0, 0)
dot.set_pos(-10, -10)  # fuera de pantalla inicialmente

# Callback de toque para mover el punto y mostrar coords
def on_touch(e):
    indev = lv.indev_active()
    if indev is None:
        return
    point = lv.point_t()
    indev.get_point(point)
    x, y = point.x, point.y
    dot.set_pos(x - 4, y - 4)
    status.set_text("LVGL: x={} y={}".format(x, y))
    print("[LVGL] x={} y={}".format(x, y))

scr.add_event_cb(on_touch, lv.EVENT.PRESSED, None)
scr.add_flag(lv.obj.FLAG.CLICKABLE)

lv.screen_load(scr)
task_handler.TaskHandler()
