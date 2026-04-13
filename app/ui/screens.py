# Adaptador de entrada: pantallas de la UI
import lvgl as lv
from app.ui.components import nav_bar, white_label, dark_screen
from app.domain.counter_service import CounterService
from app.domain.led_service import LedService


class ScreenManager:
    """Gestiona la navegacion entre pantallas."""

    def __init__(self):
        self._screens = []
        self._current = 0

    def add(self, screen):
        self._screens.append(screen)

    def next(self):
        self._current = (self._current + 1) % len(self._screens)
        lv.screen_load(self._screens[self._current])

    def start(self):
        if self._screens:
            lv.screen_load(self._screens[0])


def build_button_screen(manager: ScreenManager, counter: CounterService) -> lv.obj:
    s = dark_screen()
    y = nav_bar(s, "Button / Label / Check", manager.next)

    white_label(s, "Label widget", 10, y)

    btn = lv.button(s)
    btn.set_size(120, 40)
    btn.set_pos(10, y + 25)
    btn.set_ext_click_area(15)  # compensar area muerta borde derecho
    bl = lv.label(btn)
    bl.set_text("Click me!")
    bl.center()

    def on_click(e):
        counter.increment()
        bl.set_text("Clicks: {}".format(counter.value))
        print("[BTN] Clicks: {}".format(counter.value))

    btn.add_event_cb(on_click, lv.EVENT.CLICKED, None)

    cb1 = lv.checkbox(s)
    cb1.set_text("Option A")
    cb1.set_pos(10, y + 75)
    cb1.set_style_text_color(lv.color_hex(0xFFFFFF), 0)

    cb2 = lv.checkbox(s)
    cb2.set_text("Option B")
    cb2.set_pos(10, y + 115)  # mas separado de A para evitar activacion cruzada
    cb2.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
    cb2.add_state(lv.STATE.CHECKED)

    return s


def build_slider_screen(manager: ScreenManager) -> lv.obj:
    s = dark_screen()
    y = nav_bar(s, "Slider / Switch / Bar", manager.next)

    slider = lv.slider(s)
    slider.set_size(200, 20)
    slider.set_pos(10, y + 5)
    slider.set_value(40, False)
    sl = white_label(s, "Val: 40", 220, y + 5)

    def on_slider(e):
        sl.set_text("Val: {}".format(slider.get_value()))

    slider.add_event_cb(on_slider, lv.EVENT.VALUE_CHANGED, None)

    slider.add_event_cb(on_slider, lv.EVENT.VALUE_CHANGED, None)

    sw = lv.switch(s)
    sw.set_pos(10, y + 45)
    sw_lbl = white_label(s, "OFF", 80, y + 48)

    def on_sw(e):
        sw_lbl.set_text("ON" if sw.has_state(lv.STATE.CHECKED) else "OFF")

    sw.add_event_cb(on_sw, lv.EVENT.VALUE_CHANGED, None)

    bar = lv.bar(s)
    bar.set_size(200, 20)
    bar.set_pos(10, y + 90)
    bar.set_value(65, False)
    white_label(s, "Bar 65%", 220, y + 90)

    return s


def build_dropdown_screen(manager: ScreenManager) -> lv.obj:
    s = dark_screen()
    y = nav_bar(s, "Dropdown / Roller", manager.next)

    dd = lv.dropdown(s)
    dd.set_options("Opcion 1\nOpcion 2\nOpcion 3\nOpcion 4")
    dd.set_size(150, 40)
    dd.set_pos(10, y + 5)
    dd_lbl = white_label(s, "Sel: 0", 170, y + 15)

    def on_dd(e):
        dd_lbl.set_text("Sel: {}".format(dd.get_selected()))

    dd.add_event_cb(on_dd, lv.EVENT.VALUE_CHANGED, None)

    roller = lv.roller(s)
    roller.set_options("Lunes\nMartes\nMiercoles\nJueves\nViernes", lv.roller.MODE.NORMAL)
    roller.set_size(140, 100)
    roller.set_pos(10, y + 55)

    return s


def build_arc_screen(manager: ScreenManager) -> lv.obj:
    s = dark_screen()
    y = nav_bar(s, "Arc / Spinner / LED", manager.next)

    arc = lv.arc(s)
    arc.set_size(100, 100)
    arc.set_pos(10, y)
    arc.set_value(75)
    arc_lbl = lv.label(s)
    arc_lbl.set_text("75%")
    arc_lbl.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
    arc_lbl.align_to(arc, lv.ALIGN.CENTER, 0, 0)

    spinner = lv.spinner(s)
    spinner.set_size(80, 80)
    spinner.set_pos(120, y)

    led1 = lv.led(s)
    led1.set_size(30, 30)
    led1.set_pos(220, y + 10)
    led1.set_color(lv.color_hex(0x00FF00))
    led1.on()

    led2 = lv.led(s)
    led2.set_size(30, 30)
    led2.set_pos(260, y + 10)
    led2.set_color(lv.color_hex(0xFF0000))
    led2.off()

    return s


def build_table_screen(manager: ScreenManager) -> lv.obj:
    s = dark_screen()
    y = nav_bar(s, "Table", manager.next)

    table = lv.table(s)
    table.set_pos(5, y)
    table.set_size(310, 190)
    table.set_column_count(3)
    table.set_row_count(5)
    table.set_column_width(0, 80)
    table.set_column_width(1, 120)
    table.set_column_width(2, 80)

    for i, h in enumerate(["ID", "Nombre", "Valor"]):
        table.set_cell_value(0, i, h)

    for r, row in enumerate([("1","Sensor A","23.5"),("2","Sensor B","18.2"),
                              ("3","Sensor C","31.0"),("4","Sensor D","9.8")]):
        for c, val in enumerate(row):
            table.set_cell_value(r + 1, c, val)

    return s


def build_chart_screen(manager: ScreenManager) -> lv.obj:
    import random
    s = dark_screen()
    y = nav_bar(s, "Chart", manager.next)

    chart = lv.chart(s)
    chart.set_size(300, 180)
    chart.set_pos(10, y)
    chart.set_type(lv.chart.TYPE.LINE)
    chart.set_point_count(10)
    ser1 = chart.add_series(lv.color_hex(0x00FF88), lv.chart.AXIS.PRIMARY_Y)
    ser2 = chart.add_series(lv.color_hex(0xFF5722), lv.chart.AXIS.PRIMARY_Y)

    for _ in range(10):
        chart.set_next_value(ser1, random.randint(20, 80))
        chart.set_next_value(ser2, random.randint(10, 60))

    return s


def build_led_screen(manager: ScreenManager, led_service: LedService) -> lv.obj:
    s = dark_screen()
    y = nav_bar(s, "RGB LED", manager.next)

    status_lbl = white_label(s, "LED: OFF", 10, y + 5)

    COLOR_HEX = {
        "OFF": 0x555555, "ROJO": 0xFF0000, "VERDE": 0x00FF00,
        "AZUL": 0x0000FF, "BLANCO": 0xFFFFFF, "CYAN": 0x00FFFF,
        "MAGENTA": 0xFF00FF, "AMARILLO": 0xFFFF00,
    }

    for i, name in enumerate(led_service.available_colors()):
        btn = lv.button(s)
        btn.set_size(70, 45)
        btn.set_pos(10 + (i % 4) * 76, y + 30 + (i // 4) * 52)
        btn.set_style_bg_color(lv.color_hex(COLOR_HEX.get(name, 0x555555)), 0)
        btn.set_ext_click_area(12)  # compensar area muerta del touch
        bl = lv.label(btn)
        bl.set_text(name)
        bl.set_style_text_color(lv.color_hex(0x000000 if name != "OFF" else 0xFFFFFF), 0)
        bl.center()

        def make_cb(n=name):
            def cb(e):
                led_service.change_color(n)
                status_lbl.set_text("LED: " + led_service.get_current_color())
                print("[LED] Color: {}".format(led_service.get_current_color()))
            return cb

        btn.add_event_cb(make_cb(), lv.EVENT.CLICKED, None)

    return s
