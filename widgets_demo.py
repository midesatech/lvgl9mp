from micropython import const
import machine, lcd_bus, lvgl as lv, task_handler, ili9341

_DISPLAY_ROT = const(0xE0)

spi_bus = machine.SPI.Bus(host=1, mosi=13, miso=12, sck=14)
indev_bus = machine.SPI.Bus(host=2, mosi=32, miso=39, sck=25)
indev_device = machine.SPI.Device(spi_bus=indev_bus, freq=2000000, cs=33)
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

import xpt2046
indev = xpt2046.XPT2046(device=indev_device)
task_handler.TaskHandler()

# ---- Pantallas de demo ----
screens = []
current = [0]

def next_screen(e):
    current[0] = (current[0] + 1) % len(screens)
    lv.screen_load(screens[current[0]])

def make_nav(scr, title):
    """Barra superior con titulo y boton siguiente"""
    bar = lv.obj(scr)
    bar.set_size(320, 30)
    bar.set_pos(0, 0)
    bar.set_style_bg_color(lv.color_hex(0x2196F3), 0)
    bar.set_style_border_width(0, 0)
    bar.set_style_radius(0, 0)

    t = lv.label(bar)
    t.set_text(title)
    t.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
    t.align(lv.ALIGN.LEFT_MID, 5, 0)

    btn = lv.button(bar)
    btn.set_size(60, 22)
    btn.align(lv.ALIGN.RIGHT_MID, -3, 0)
    btn.add_event_cb(next_screen, lv.EVENT.CLICKED, None)
    bl = lv.label(btn)
    bl.set_text("Next >")
    bl.center()
    return 35  # y offset para contenido

# ---- Pantalla 1: Button, Label, Checkbox ----
s1 = lv.obj()
s1.set_style_bg_color(lv.color_hex(0x1a1a2e), 0)
y = make_nav(s1, "Button / Label / Check")

lbl = lv.label(s1)
lbl.set_text("Label widget")
lbl.set_style_text_color(lv.color_hex(0x00ff88), 0)
lbl.set_pos(10, y)

btn = lv.button(s1)
btn.set_size(120, 40)
btn.set_pos(10, y + 25)
bl = lv.label(btn)
bl.set_text("Click me!")
bl.center()
count = [0]
def on_btn(e):
    count[0] += 1
    bl.set_text("Clicks: {}".format(count[0]))
btn.add_event_cb(on_btn, lv.EVENT.CLICKED, None)

cb1 = lv.checkbox(s1)
cb1.set_text("Option A")
cb1.set_pos(10, y + 75)
cb1.set_style_text_color(lv.color_hex(0xFFFFFF), 0)

cb2 = lv.checkbox(s1)
cb2.set_text("Option B")
cb2.set_pos(10, y + 105)
cb2.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
cb2.add_state(lv.STATE.CHECKED)

screens.append(s1)

# ---- Pantalla 2: Slider, Switch, Bar ----
s2 = lv.obj()
s2.set_style_bg_color(lv.color_hex(0x1a1a2e), 0)
y = make_nav(s2, "Slider / Switch / Bar")

slider = lv.slider(s2)
slider.set_size(200, 20)
slider.set_pos(10, y + 5)
slider.set_value(40, False)
sl = lv.label(s2)
sl.set_text("Val: 40")
sl.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
sl.set_pos(220, y + 5)
def on_slider(e):
    sl.set_text("Val: {}".format(slider.get_value()))
slider.add_event_cb(on_slider, lv.EVENT.VALUE_CHANGED, None)

sw = lv.switch(s2)
sw.set_pos(10, y + 45)
sw_lbl = lv.label(s2)
sw_lbl.set_text("OFF")
sw_lbl.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
sw_lbl.set_pos(80, y + 48)
def on_sw(e):
    sw_lbl.set_text("ON" if sw.has_state(lv.STATE.CHECKED) else "OFF")
sw.add_event_cb(on_sw, lv.EVENT.VALUE_CHANGED, None)

bar = lv.bar(s2)
bar.set_size(200, 20)
bar.set_pos(10, y + 90)
bar.set_value(65, False)
bl2 = lv.label(s2)
bl2.set_text("Bar 65%")
bl2.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
bl2.set_pos(220, y + 90)

screens.append(s2)

# ---- Pantalla 3: Dropdown, Roller ----
s3 = lv.obj()
s3.set_style_bg_color(lv.color_hex(0x1a1a2e), 0)
y = make_nav(s3, "Dropdown / Roller")

dd = lv.dropdown(s3)
dd.set_options("Opcion 1\nOpcion 2\nOpcion 3\nOpcion 4")
dd.set_size(150, 40)
dd.set_pos(10, y + 5)
dd_lbl = lv.label(s3)
dd_lbl.set_text("Sel: 0")
dd_lbl.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
dd_lbl.set_pos(170, y + 15)
def on_dd(e):
    dd_lbl.set_text("Sel: {}".format(dd.get_selected()))
dd.add_event_cb(on_dd, lv.EVENT.VALUE_CHANGED, None)

roller = lv.roller(s3)
roller.set_options("Lunes\nMartes\nMiercoles\nJueves\nViernes", lv.roller.MODE.NORMAL)
roller.set_size(140, 100)
roller.set_pos(10, y + 55)

screens.append(s3)

# ---- Pantalla 4: Arc, Spinner, LED ----
s4 = lv.obj()
s4.set_style_bg_color(lv.color_hex(0x1a1a2e), 0)
y = make_nav(s4, "Arc / Spinner / LED")

arc = lv.arc(s4)
arc.set_size(100, 100)
arc.set_pos(10, y)
arc.set_value(75)
arc_lbl = lv.label(s4)
arc_lbl.set_text("75%")
arc_lbl.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
arc_lbl.align_to(arc, lv.ALIGN.CENTER, 0, 0)

spinner = lv.spinner(s4)
spinner.set_size(80, 80)
spinner.set_pos(120, y)

led1 = lv.led(s4)
led1.set_size(30, 30)
led1.set_pos(220, y + 10)
led1.set_color(lv.color_hex(0x00FF00))
led1.on()

led2 = lv.led(s4)
led2.set_size(30, 30)
led2.set_pos(260, y + 10)
led2.set_color(lv.color_hex(0xFF0000))
led2.off()

screens.append(s4)

# ---- Pantalla 5: Table ----
s5 = lv.obj()
s5.set_style_bg_color(lv.color_hex(0x1a1a2e), 0)
y = make_nav(s5, "Table")

table = lv.table(s5)
table.set_pos(5, y)
table.set_size(310, 190)
table.set_column_count(3)
table.set_row_count(5)
table.set_column_width(0, 80)
table.set_column_width(1, 120)
table.set_column_width(2, 80)
headers = ["ID", "Nombre", "Valor"]
for i, h in enumerate(headers):
    table.set_cell_value(0, i, h)
data = [("1","Sensor A","23.5"),("2","Sensor B","18.2"),("3","Sensor C","31.0"),("4","Sensor D","9.8")]
for r, row in enumerate(data):
    for c, val in enumerate(row):
        table.set_cell_value(r+1, c, val)

screens.append(s5)

# ---- Pantalla 6: Chart ----
s6 = lv.obj()
s6.set_style_bg_color(lv.color_hex(0x1a1a2e), 0)
y = make_nav(s6, "Chart")

chart = lv.chart(s6)
chart.set_size(300, 180)
chart.set_pos(10, y)
chart.set_type(lv.chart.TYPE.LINE)
chart.set_point_count(10)
ser1 = chart.add_series(lv.color_hex(0x00FF88), lv.chart.AXIS.PRIMARY_Y)
ser2 = chart.add_series(lv.color_hex(0xFF5722), lv.chart.AXIS.PRIMARY_Y)
import random
for i in range(10):
    chart.set_next_value(ser1, random.randint(20, 80))
    chart.set_next_value(ser2, random.randint(10, 60))

screens.append(s6)

# ---- Pantalla 7: RGB LED ----
# CYD: R=GPIO4, G=GPIO16, B=GPIO17, activo en LOW
PIN_R = machine.Pin(4,  machine.Pin.OUT, value=1)
PIN_G = machine.Pin(16, machine.Pin.OUT, value=1)
PIN_B = machine.Pin(17, machine.Pin.OUT, value=1)

s7 = lv.obj()
s7.set_style_bg_color(lv.color_hex(0x1a1a2e), 0)
y = make_nav(s7, "RGB LED")

status_lbl = lv.label(s7)
status_lbl.set_text("LED: OFF")
status_lbl.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
status_lbl.set_pos(10, y + 5)

def set_led(r, g, b, name):
    PIN_R.value(0 if r else 1)
    PIN_G.value(0 if g else 1)
    PIN_B.value(0 if b else 1)
    status_lbl.set_text("LED: " + name)

colors = [
    ("OFF",    0xFF555555, 0, 0, 0),
    ("ROJO",   0xFFFF0000, 1, 0, 0),
    ("VERDE",  0xFF00FF00, 0, 1, 0),
    ("AZUL",   0xFF0000FF, 0, 0, 1),
    ("BLANCO", 0xFFFFFFFF, 1, 1, 1),
    ("CYAN",   0xFF00FFFF, 0, 1, 1),
    ("MAGENTA",0xFFFF00FF, 1, 0, 1),
    ("AMARILLO",0xFFFFFF00,1, 1, 0),
]

cols = 4
for i, (name, color, r, g, b) in enumerate(colors):
    btn = lv.button(s7)
    btn.set_size(70, 45)
    btn.set_pos(10 + (i % cols) * 76, y + 30 + (i // cols) * 52)
    btn.set_style_bg_color(lv.color_hex(color & 0xFFFFFF), 0)
    bl = lv.label(btn)
    bl.set_text(name)
    bl.set_style_text_color(lv.color_hex(0x000000 if color != 0xFF555555 else 0xFFFFFF), 0)
    bl.center()
    def make_cb(r=r, g=g, b=b, name=name):
        def cb(e): set_led(r, g, b, name)
        return cb
    btn.add_event_cb(make_cb(), lv.EVENT.CLICKED, None)

screens.append(s7)

# Cargar primera pantalla
lv.screen_load(screens[0])
