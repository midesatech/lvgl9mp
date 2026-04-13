# raw_corners.py - Mide valores raw en las 4 esquinas y calcula calibracion
# Instrucciones: toca TL, TR, BL, BR en ese orden, 3 veces cada una
# El script calcula automaticamente los valores para _normalize

import machine
import lcd_bus
import lvgl as lv
import task_handler
import ili9341
from micropython import const
import time

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

# --- Touch SPI directo (sin driver LVGL, solo raw) ---
_CMD_X = const(0xD0)
_CMD_Y = const(0x90)
_CMD_Z1 = const(0xB0)
_CMD_Z2 = const(0xC0)
_MAX_RAW = const(4090)

touch_spi = machine.SPI.Bus(host=2, mosi=32, miso=39, sck=25)
touch_dev = machine.SPI.Device(spi_bus=touch_spi, freq=1000000, cs=33)

tx = bytearray(3)
rx = bytearray(3)
tx_mv = memoryview(tx)
rx_mv = memoryview(rx)

def read_raw(cmd):
    tx[0] = cmd
    touch_dev.write_readinto(tx_mv[:3], rx_mv[:3])
    return ((rx[1] << 8) | rx[2]) >> 3

def is_touched():
    z1 = read_raw(_CMD_Z1)
    z2 = read_raw(_CMD_Z2)
    z = z1 + (_MAX_RAW + 6 - z2)
    return z > 400, z

def get_stable_raw(samples=8):
    """Toma N muestras y devuelve la mediana"""
    xs, ys = [], []
    for _ in range(samples):
        touched, z = is_touched()
        if touched:
            xs.append(read_raw(_CMD_X))
            ys.append(read_raw(_CMD_Y))
        time.sleep_ms(10)
    if len(xs) < 3:
        return None
    xs.sort(); ys.sort()
    mid = len(xs) // 2
    return xs[mid], ys[mid]

# --- UI ---
scr = lv.obj()
scr.set_style_bg_color(lv.color_hex(0x001122), 0)

title = lv.label(scr)
title.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
title.set_pos(10, 5)
title.set_text("RAW CALIBRATION")

instr = lv.label(scr)
instr.set_style_text_color(lv.color_hex(0xFFFF00), 0)
instr.set_pos(10, 25)
instr.set_text("Toca: TOP-LEFT")

result = lv.label(scr)
result.set_style_text_color(lv.color_hex(0x00FF88), 0)
result.set_pos(10, 55)
result.set_text("Esperando...")

lv.screen_load(scr)

# Marcadores de esquinas
corners_info = [
    (10,  10,  "TL", 0xFF4444),
    (300, 10,  "TR", 0x44FF44),
    (10,  220, "BL", 0x4444FF),
    (300, 220, "BR", 0xFFFF44),
]
corner_names = ["TOP-LEFT", "TOP-RIGHT", "BOT-LEFT", "BOT-RIGHT"]

for cx, cy, label, color in corners_info:
    m = lv.obj(scr)
    m.set_size(16, 16)
    m.set_pos(cx - 8, cy - 8)
    m.set_style_bg_color(lv.color_hex(color), 0)
    m.set_style_radius(0, 0)
    m.set_style_border_width(0, 0)
    lbl = lv.label(scr)
    lbl.set_text(label)
    lbl.set_style_text_color(lv.color_hex(color), 0)
    lbl.set_pos(cx + 10, cy - 5)

task_handler.TaskHandler()

# --- Bucle de medicion ---
collected = []
step = 0
last_touch = False
debounce = 0

print("\n=== CALIBRACION RAW ===")
print("Toca cada esquina cuando se indique")
print("Orden: TL -> TR -> BL -> BR\n")

import _thread

def measure_loop():
    global step, last_touch, debounce, collected

    while step < 4:
        time.sleep_ms(50)
        touched, z = is_touched()

        if touched and not last_touch and time.ticks_ms() - debounce > 800:
            raw = get_stable_raw(10)
            if raw:
                rx_val, ry_val = raw
                name = corner_names[step]
                print("[{}] raw_x={} raw_y={} z={}".format(name, rx_val, ry_val, z))
                collected.append((name, rx_val, ry_val))

                # Actualizar UI
                result.set_text("{}:\nx={} y={}".format(name, rx_val, ry_val))
                if step + 1 < 4:
                    instr.set_text("Toca: " + corner_names[step + 1])
                else:
                    instr.set_text("Listo! Ver consola")

                step += 1
                debounce = time.ticks_ms()

        last_touch = touched

    # Calcular valores de calibracion
    if len(collected) == 4:
        print("\n=== RESULTADOS ===")
        data = {name: (rx, ry) for name, rx, ry in collected}
        tl_x, tl_y = data["TOP-LEFT"]
        tr_x, tr_y = data["TOP-RIGHT"]
        bl_x, bl_y = data["BOT-LEFT"]
        br_x, br_y = data["BOT-RIGHT"]

        print("TL: x={} y={}".format(tl_x, tl_y))
        print("TR: x={} y={}".format(tr_x, tr_y))
        print("BL: x={} y={}".format(bl_x, bl_y))
        print("BR: x={} y={}".format(br_x, br_y))

        # Analizar ejes
        # Si Y varia mas horizontalmente -> ejes intercambiados
        h_var_x = abs(tr_x - tl_x)  # variacion X al mover horizontal
        h_var_y = abs(tr_y - tl_y)  # variacion Y al mover horizontal
        swap = h_var_y > h_var_x

        print("\nVariacion horizontal: delta_x={} delta_y={}".format(h_var_x, h_var_y))
        print("Ejes intercambiados: {}".format(swap))

        if swap:
            # px <- Y fisico, py <- X fisico
            y_min = min(tl_y, tr_y, bl_y, br_y)
            y_max = max(tl_y, tr_y, bl_y, br_y)
            x_min = min(tl_x, tr_x, bl_x, br_x)
            x_max = max(tl_x, tr_x, bl_x, br_x)
            print("\n_normalize correcto:")
            print("px = remap(y, {}, {}, 0, self._orig_width)".format(y_min, y_max))
            print("py = remap(x, {}, {}, 0, self._orig_height)".format(x_min, x_max))
        else:
            x_min = min(tl_x, tr_x, bl_x, br_x)
            x_max = max(tl_x, tr_x, bl_x, br_x)
            y_min = min(tl_y, tr_y, bl_y, br_y)
            y_max = max(tl_y, tr_y, bl_y, br_y)
            print("\n_normalize correcto:")
            print("px = remap(x, {}, {}, 0, self._orig_width)".format(x_min, x_max))
            print("py = remap(y, {}, {}, 0, self._orig_height)".format(y_min, y_max))

        result.set_text("Ver consola\npara valores")

_thread.start_new_thread(measure_loop, ())
