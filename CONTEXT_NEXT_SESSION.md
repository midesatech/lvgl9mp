# Contexto para próxima sesión - ESP32-2432S028R (CYD)

## Estado actual (2026-04-14)

### Lo que funciona
- Firmware LVGL9 + MicroPython compilado y flasheado (firmware.bin en workspace)
- Display ILI9341: landscape, USB a la derecha, MADCTL 0x20
- App de widgets visible y navegable
- Scroll deshabilitado en todas las pantallas
- Botón Next: funciona con dedo, con lápiz requiere más presión
- Slider: llega hasta ~62 con lápiz
- Prints en consola al presionar botones

### Calibración actual (mejor estado conocido)
```python
# xpt2046.py en filesystem ESP32
touch_threshold = 400
confidence = 5
margin = 50

def _normalize(self, x, y):
    px = pointer_framework.remap(y, 371, 3335, 0, self._orig_width)
    py = pointer_framework.remap(x, 600, 3371, 0, self._orig_height)
    return px, py
```

### Problema raíz identificado (IMPORTANTE)
El touch resistivo XPT2046 del CYD **no es lineal**. Un remap lineal simple
no puede corregirlo perfectamente. En Arduino/C funciona porque la librería
`XPT2046_Touchscreen` usa transformación affine (3 puntos) internamente.

El `pointer_framework` de lvgl_micropython ya soporta calibración affine via
`touch_cal` (TouchCalData con alphaX, betaX, deltaX, alphaY, betaY, deltaY).
Esta es la solución correcta pero requiere implementar el proceso de calibración.

### Solución definitiva: calibración affine por 3 puntos

El `pointer_framework.PointerDriver` tiene el método `calibrate()` que llama
a `touch_calibrate.calibrate()`. Si se implementa correctamente, calcula los
6 coeficientes de la transformación affine y los guarda en flash.

#### Cómo implementarlo:
1. Llamar `indev.calibrate()` desde MicroPython
2. El usuario toca 3 puntos en pantalla
3. Los coeficientes se guardan automáticamente
4. El touch queda calibrado permanentemente

#### Alternativa manual:
Medir 3 puntos raw y calcular los coeficientes affine:
```
| px |   | alphaX  betaX  | | x_raw |   | deltaX |
| py | = | alphaY  betaY  | | y_raw | + | deltaY |
```

### Datos medidos en sesión (útiles para calibración affine)
Con `y_min=800, y_max=3900` (valores que daban slider 0-100):
- Extremo izquierdo barra slider (x_real=10):  LVGL x:17, y:70
- Extremo derecho barra slider (x_real=210):   LVGL x:206, y:83
- Círculo slider en 40 (x_real=90):            LVGL x:173, y:67
- Botón Next (x_real≈280, y_real≈15):          LVGL x:195, y:30

### Síntomas pendientes (limitaciones hardware)
- Option B se activa tocando ligeramente fuera del cuadro → área muerta vertical
- Botón Clicks no responde en el 15% del borde derecho → área muerta horizontal
- El círculo del slider no sigue exactamente el dedo → no-linealidad del touch

### Archivos importantes
- `firmware.bin` — firmware compilado con valores frozen
- `xpt2046.py` — driver touch (filesystem tiene prioridad sobre frozen)
- `app/ui/components.py` — scroll deshabilitado
- `app/ui/screens.py` — prints para video, checkboxes separados
- `FIRMWARE_BUILD_GUIDE.md` — guía completa

### Hardware
- Board: ESP32-2432S028R (CYD 2.8")
- COM: COM7, USB a la derecha
- LED RGB: GPIO4(R), GPIO16(G), GPIO17(B) — active LOW
- WSL2: Ubuntu-22.04, usuario fury
- Build: ~/lvgl_micropython_build/lvgl_micropython

### Procedimiento flash (requiere modo bootloader)
1. Mantener BOOT + presionar/soltar RESET + soltar BOOT
2. `python -m esptool --chip esp32 --port COM7 -b 460800 write-flash --flash-mode dio --flash-size 4MB --flash-freq 40m --erase-all 0x0 firmware.bin`
3. Crear dirs: `python -m mpremote connect COM7 exec "import os; [os.mkdir(d) for d in ['app','app/ports','app/domain','app/ui']]"`
4. Subir archivos: `python -m mpremote connect COM7 cp app/__init__.py :app/__init__.py + cp app/ports/display_port.py :app/ports/display_port.py + cp app/ports/led_port.py :app/ports/led_port.py + cp app/domain/counter_service.py :app/domain/counter_service.py + cp app/domain/led_service.py :app/domain/led_service.py + cp app/ui/components.py :app/ui/components.py + cp app/ui/screens.py :app/ui/screens.py + cp main.py :main.py + cp xpt2046.py :xpt2046.py + reset`
