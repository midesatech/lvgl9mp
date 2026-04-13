# Adaptador de entrada: componentes UI reutilizables
import lvgl as lv


def nav_bar(screen, title: str, on_next) -> int:
    """Barra de navegacion superior. Retorna el y-offset para el contenido."""
    bar = lv.obj(screen)
    bar.set_size(320, 30)
    bar.set_pos(0, 0)
    bar.set_style_bg_color(lv.color_hex(0x2196F3), 0)
    bar.set_style_border_width(0, 0)
    bar.set_style_radius(0, 0)
    bar.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
    bar.set_scroll_dir(lv.DIR.NONE)

    t = lv.label(bar)
    t.set_text(title)
    t.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
    t.align(lv.ALIGN.LEFT_MID, 5, 0)

    btn = lv.button(bar)
    btn.set_size(60, 22)
    btn.align(lv.ALIGN.RIGHT_MID, -3, 0)
    btn.set_ext_click_area(10)
    btn.add_event_cb(lambda e: on_next(), lv.EVENT.CLICKED, None)
    btn_lbl = lv.label(btn)
    btn_lbl.set_text("Next >")
    btn_lbl.center()

    return 35


def white_label(parent, text: str, x: int, y: int) -> lv.label:
    lbl = lv.label(parent)
    lbl.set_text(text)
    lbl.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
    lbl.set_pos(x, y)
    return lbl


def dark_screen() -> lv.obj:
    s = lv.obj()
    s.set_style_bg_color(lv.color_hex(0x1a1a2e), 0)
    s.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
    s.set_scroll_dir(lv.DIR.NONE)
    return s
