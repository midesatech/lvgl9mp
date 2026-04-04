# Puerto de salida: abstraccion del LED RGB
import machine


class RgbLed:
    """Driver del LED RGB del CYD. Pines activos en LOW."""

    COLORS = {
        "OFF":      (0, 0, 0),
        "ROJO":     (1, 0, 0),
        "VERDE":    (0, 1, 0),
        "AZUL":     (0, 0, 1),
        "BLANCO":   (1, 1, 1),
        "CYAN":     (0, 1, 1),
        "MAGENTA":  (1, 0, 1),
        "AMARILLO": (1, 1, 0),
    }

    def __init__(self, pin_r=4, pin_g=16, pin_b=17):
        self._r = machine.Pin(pin_r, machine.Pin.OUT, value=1)
        self._g = machine.Pin(pin_g, machine.Pin.OUT, value=1)
        self._b = machine.Pin(pin_b, machine.Pin.OUT, value=1)
        self._current = "OFF"

    def set_color(self, name: str):
        if name not in self.COLORS:
            return
        r, g, b = self.COLORS[name]
        self._r.value(0 if r else 1)
        self._g.value(0 if g else 1)
        self._b.value(0 if b else 1)
        self._current = name

    @property
    def current_color(self) -> str:
        return self._current
