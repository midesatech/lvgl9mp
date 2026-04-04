import machine, lcd_bus, lvgl as lv, task_handler, ili9341

# API correcta para firmware commit 15a414b
# machine.SPI.Bus: host, sck son INT obligatorios
spi_bus = machine.SPI.Bus(host=1, sck=14, mosi=13, miso=12)

# lcd_bus.SPIBus: spi_bus, dc, freq obligatorios
display_bus = lcd_bus.SPIBus(spi_bus=spi_bus, dc=2, freq=40000000, cs=15)

display = ili9341.ILI9341(
    data_bus=display_bus,
    display_width=240,
    display_height=320,
    backlight_pin=21,
    color_space=lv.COLOR_FORMAT.RGB565,
    color_byte_order=ili9341.BYTE_ORDER_RGB,
    rgb565_byte_swap=True,
)

display.set_power(True)
display.init(1)
display.set_backlight(100)
display.set_rotation(lv.DISPLAY_ROTATION._90)

th = task_handler.TaskHandler()

scrn = lv.screen_active()
scrn.set_style_bg_color(lv.color_hex(0xFF0000), 0)

# 4 esquinas para verificar orientacion
for x, y, color in [
    (0,   0,   0x00FF00),  # verde  arriba-izq
    (260, 0,   0x0000FF),  # azul   arriba-der
    (0,   180, 0xFFFF00),  # amarillo abajo-izq
    (260, 180, 0xFFFFFF),  # blanco abajo-der
]:
    o = lv.obj(scrn)
    o.set_size(60, 60)
    o.set_pos(x, y)
    o.set_style_bg_color(lv.color_hex(color), 0)
    o.set_style_border_width(0, 0)

label = lv.label(scrn)
label.set_text("ROT90 RGB SWAP")
label.set_style_text_color(lv.color_hex(0x000000), 0)
label.center()
