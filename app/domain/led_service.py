# Caso de uso / servicio de dominio: logica del LED
from app.ports.led_port import RgbLed


class LedService:
    """Caso de uso: controlar el LED RGB."""

    def __init__(self, led: RgbLed):
        self._led = led

    def change_color(self, color_name: str):
        self._led.set_color(color_name)
        print("[LedService] Color cambiado a: {}".format(color_name))

    def get_current_color(self) -> str:
        return self._led.current_color

    def available_colors(self) -> list:
        return list(RgbLed.COLORS.keys())
