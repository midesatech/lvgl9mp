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

task_handler.TaskHandler()

# Leer XPT2046 directamente via SPI
touch_spi = machine.SPI.Bus(host=2, mosi=32, miso=39, sck=25)
cs = machine.Pin(33, machine.Pin.OUT)
cs.value(1)

def read_xpt2046():
    cs.value(0)
    # Comando 0xD0 = leer X, 0x90 = leer Y
    buf = bytearray(3)
    # Leer X
    machine.SPI.Bus
    cs.value(1)
    return None

# Usar SPI directo
import machine
spi = machine.SPI(2, baudrate=2000000, polarity=0, phase=0,
                  sck=machine.Pin(25), mosi=machine.Pin(32), miso=machine.Pin(39))
cs_pin = machine.Pin(33, machine.Pin.OUT)
cs_pin.value(1)

def read_raw(cmd):
    cs_pin.value(0)
    time.sleep_us(10)
    spi.write(bytes([cmd]))
    buf = bytearray(2)
    spi.readinto(buf)
    cs_pin.value(1)
    return ((buf[0] << 8) | buf[1]) >> 3

scrn = lv.screen_active()
scrn.set_style_bg_color(lv.color_hex(0x000000), 0)

lbl = lv.label(scrn)
lbl.set_text("Mantene presionado\ny mira los valores")
lbl.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
lbl.align(lv.ALIGN.TOP_MID, 0, 10)

raw_lbl = lv.label(scrn)
raw_lbl.set_text("X_raw=? Y_raw=?")
raw_lbl.set_style_text_color(lv.color_hex(0x00FF00), 0)
raw_lbl.center()

import _thread

def read_loop():
    while True:
        x_raw = read_raw(0xD0)  # X
        y_raw = read_raw(0x90)  # Y
        if x_raw > 100 and y_raw > 100:  # tocando
            raw_lbl.set_text("X_raw={} Y_raw={}".format(x_raw, y_raw))
        time.sleep_ms(100)

_thread.start_new_thread(read_loop, ())
