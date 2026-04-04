from micropython import const
import machine, lcd_bus, lvgl as lv, task_handler, ili9341
import time

_DISPLAY_ROT = const(0xE0)

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

# Leer XPT2046 raw directamente
cs_pin = machine.Pin(33, machine.Pin.OUT)
cs_pin.value(1)
touch_spi = machine.SPI.Bus(host=2, mosi=32, miso=39, sck=25)
touch_dev_raw = machine.SPI.Device(spi_bus=touch_spi, freq=1000000, cs=33)

def read_raw_coord(cmd):
    buf = bytearray(3)
    buf[0] = cmd
    out = bytearray(3)
    touch_dev_raw.write_readinto(buf, out)
    return ((out[1] << 8) | out[2]) >> 3

task_handler.TaskHandler()

scrn = lv.screen_active()
scrn.set_style_bg_color(lv.color_hex(0x000000), 0)

lbl = lv.label(scrn)
lbl.set_text("Mantene presionado\ncada esquina")
lbl.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
lbl.align(lv.ALIGN.TOP_MID, 0, 10)

raw_lbl = lv.label(scrn)
raw_lbl.set_text("X_raw=?\nY_raw=?")
raw_lbl.set_style_text_color(lv.color_hex(0x00FF00), 0)
raw_lbl.center()

def timer_cb(t):
    x = read_raw_coord(0xD0)  # X
    y = read_raw_coord(0x90)  # Y
    z1 = read_raw_coord(0xB0)
    if z1 > 100:  # tocando
        raw_lbl.set_text("X_raw={}\nY_raw={}\nZ={}".format(x, y, z1))

timer = lv.timer_create(timer_cb, 200, None)
