# Punto de entrada - Composicion de dependencias (Dependency Injection)
from app.ports.display_port import init_hardware
from app.ports.led_port import RgbLed
from app.domain.counter_service import CounterService
from app.domain.led_service import LedService
from app.ui.screens import (
    ScreenManager,
    build_button_screen,
    build_slider_screen,
    build_dropdown_screen,
    build_arc_screen,
    build_table_screen,
    build_chart_screen,
    build_led_screen,
)

# 1. Inicializar hardware (puerto de salida)
init_hardware()

# 2. Instanciar servicios de dominio
counter = CounterService()
led = RgbLed()
led_service = LedService(led)

# 3. Construir UI (adaptador de entrada)
manager = ScreenManager()

manager.add(build_button_screen(manager, counter))
manager.add(build_slider_screen(manager))
manager.add(build_dropdown_screen(manager))
manager.add(build_arc_screen(manager))
manager.add(build_table_screen(manager))
manager.add(build_chart_screen(manager))
manager.add(build_led_screen(manager, led_service))

# 4. Arrancar
manager.start()
