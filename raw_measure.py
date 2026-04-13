# raw_measure.py
# Herramienta para medir los valores raw del touch XPT2046
# Subir al ESP32, tocar las 4 esquinas y el centro, anotar los valores
# Usar estos valores para configurar el driver en main.py

from micropython import const
import machine, lcd_bus, lvgl as lv, task_handler, ili9341

_DISPLAY_ROT = const(0x20)  # USB a la derecha

spi_bus = machine.SPI.Bus(host=1, mosi=13, miso=12, sck=14)
display_bus = lcd_bus.SPIBus(spi_bus=spi_bus, freq=24000000, dc=2, cs=15)

display = ili9341.ILI9341(
    data_bus=display_bus,
    display_width=320, display_height=240,
    backlight_pin=21, backlight_on_state=ili9341.STATE_PWM,
    color_space=lv.COLOR_FORMAT.RGB565,
    color_byte_order=ili9341.BYTE_ORDER_BGR,
    rgb565_byte_swap=True,
)
display._ORIENTATION_TABLE = (_DISPLAY_ROT, 0x0, 0x0, 0x0)
display.set_rotation(lv.DISPLAY_ROTATION._0)
display.set_power(True)
display.init(1)
display.set_backlight(100)

# Leer XPT2046 raw directamente via SPI
touch_spi = machine.SPI.Bus(host=2, mosi=32, miso=39, sck=25)
touch_dev_raw = machine.SPI.Device(spi_bus=touch_spi, freq=1000000, cs=33)

def read_raw(cmd):
    buf = bytearray(3)
    buf[0] = cmd
    out = bytearray(3)
    touch_dev_raw.write_readinto(buf, out)
    return ((out[1] << 8) | out[2]) >> 3

task_handler.TaskHandler()

scrn = lv.screen_active()
scrn.set_style_bg_color(lv.color_hex(0x000000), 0)

title = lv.label(scrn)
title.set_text("Toca las 4 esquinas\ny el centro")
title.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
title.align(lv.ALIGN.TOP_MID, 0, 10)

raw_lbl = lv.label(scrn)
raw_lbl.set_text("X_raw=?\nY_raw=?\nZ=?")
raw_lbl.set_style_text_color(lv.color_hex(0x00FF88), 0)
raw_lbl.center()

hint = lv.label(scrn)
hint.set_text("Ver consola para log")
hint.set_style_text_color(lv.color_hex(0xAAAAAA), 0)
hint.align(lv.ALIGN.BOTTOM_MID, 0, -10)

last_z = [0]

def timer_cb(t):
    x = read_raw(0xD0)  # X raw
    y = read_raw(0x90)  # Y raw
    z = read_raw(0xB0)  # presion

    if z > 100:
        raw_lbl.set_text("X_raw={}\nY_raw={}\nZ={}".format(x, y, z))
        # Solo imprimir cuando hay nuevo toque (evitar spam)
        if last_z[0] < 100:
            print("TOUCH -> X_raw={} Y_raw={} Z={}".format(x, y, z))
    else:
        if last_z[0] > 100:
            print("--- soltado ---")

    last_z[0] = z

lv.timer_create(timer_cb, 150, None)

# Instrucciones en consola
print("=" * 40)
print("raw_measure.py - CYD Touch Calibration")
print("=" * 40)
print("Toca cada esquina y anota los valores:")
print("  Top-left:  X_raw=? Y_raw=?")
print("  Top-right: X_raw=? Y_raw=?")
print("  Bot-left:  X_raw=? Y_raw=?")
print("  Bot-right: X_raw=? Y_raw=?")
print("  Centro:    X_raw=? Y_raw=?")
print("=" * 40)
