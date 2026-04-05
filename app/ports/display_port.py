# Puerto de salida: abstraccion del hardware de display y touch
import machine
import lcd_bus
import lvgl as lv
import task_handler
import ili9341
import xpt2046
from micropython import const

_DISPLAY_ROT = const(0x20)  # landscape USB a la derecha


def init_display():
    """Inicializa display ILI9341 en landscape para ESP32-2432S028R."""
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
    return display


def init_touch():
    """Inicializa touch XPT2046 para ESP32-2432S028R."""
    indev_bus = machine.SPI.Bus(host=2, mosi=32, miso=39, sck=25)
    indev_device = machine.SPI.Device(spi_bus=indev_bus, freq=2000000, cs=33)
    return xpt2046.XPT2046(device=indev_device)


def init_hardware():
    """Inicializa todo el hardware y retorna (display, indev)."""
    display = init_display()
    indev = init_touch()
    task_handler.TaskHandler()
    return display, indev
