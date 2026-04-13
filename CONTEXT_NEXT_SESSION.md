# Contexto para próxima sesión - ESP32-2432S028R (CYD)

## Estado actual (2026-04-13 - fin de sesión)

### Lo que funciona
- Firmware LVGL9 + MicroPython flasheado y verificado (firmware.bin en workspace)
- Display ILI9341 correcto: landscape, USB a la derecha, MADCTL 0x20
- App de widgets visible: botones, slider, checkboxes, LED RGB
- Scroll deshabilitado en todas las pantallas
- Prints en consola al presionar botones de color y botón Clicks

### Problema pendiente: Touch descuadrado (desplazado a la derecha)

#### Síntomas observados al final de sesión
Con los valores `px = remap(y, 100, 3600)` y `py = remap(x, 200, 3700)`:
1. Botón Next: responde con dedo pero NO con lápiz
2. Slider: llega hasta ~9 (mejoró de 7 → 9 durante la sesión)
3. Botón MAGENTA: solo responde desde la letra "E" hacia la derecha
   → indica que el lado izquierdo de la pantalla sigue sin cobertura
   → y_min aún demasiado alto

#### Progresión de valores probados (de peor a mejor)
```
remap(y, 334, 3671) → remap(x, 288, 3830)  # original firmware frozen - malo
remap(y, 371, 3335) → remap(x, 600, 3371)  # versión anterior - malo
remap(y, 564, 3505) → remap(x, 450, 3632)  # basado en mediciones - slider a 7
remap(y, 564, 3505) → remap(x, 200, 3700)  # ajuste vertical - slider a 9
remap(y, 200, 3600) → remap(x, 200, 3700)  # slider a 9, MAGENTA desde E
remap(y, 100, 3600) → remap(x, 200, 3700)  # ÚLTIMO - pendiente de prueba
```

#### Valores actuales en xpt2046.py (filesystem ESP32)
```python
touch_threshold = 200  # bajado de 400
confidence = 3         # bajado de 5
margin = 100           # subido de 50

def _normalize(self, x, y):
    px = pointer_framework.remap(y, 100, 3600, 0, self._orig_width)
    py = pointer_framework.remap(x, 200, 3700, 0, self._orig_height)
    return px, py
```

### Valores raw medidos (confiables, del historial)
Tomados con lápiz resistivo, USB a la derecha, MADCTL 0x20:
```
TL (arriba-izq): x_raw~570,  y_raw~564
TR (arriba-der): x_raw~450,  y_raw~3505
BL (abajo-izq):  x_raw~3432, y_raw~620
BR (abajo-der):  x_raw~3632, y_raw~3473
Centro:          x_raw~2066, y_raw~1947
```

### Análisis del problema raíz
- Y físico = eje horizontal pantalla (izquierda=bajo, derecha=alto)
- X físico = eje vertical pantalla (arriba=bajo, abajo=alto)
- El slider va de izquierda a derecha → controlado por Y físico
- Si slider llega a 9% → Y físico máximo detectado ≈ 100 + 9%*(3600-100) = ~415
  Pero el valor real de TL es y_raw~564 → confirma que y_min=100 es correcto
  El problema es que el lápiz/dedo no genera suficiente presión en el borde izquierdo

### Hipótesis para próxima sesión
1. **El touch resistivo tiene área muerta física en el borde izquierdo** (~10-15%)
   → No hay solución de software, es limitación del hardware
   → Compensar con set_ext_click_area más grande en widgets del borde izquierdo

2. **El lápiz no genera suficiente presión** (threshold=200 puede ayudar)
   → Ya bajado a 200, probar resultado

3. **Los valores raw reales pueden ser diferentes** a los medidos
   → Usar cal_measure.py para medir fresh con el firmware actual

### Plan para próxima sesión

#### Paso 1: Probar valores actuales (y=100-3600, x=200-3700, threshold=200)
Ver si el slider llega más lejos y si Next responde con lápiz

#### Paso 2: Si sigue mal, medir raw con cal_measure.py
```bash
# Subir como main temporal
python -m mpremote connect COM7 cp cal_measure.py :main.py
python -m mpremote connect COM7 reset
# Tocar TL, TR, BL, BR con lápiz y anotar TP_DATA values
# Restaurar main original después
python -m mpremote connect COM7 cp main.py :main.py  # (renombrar primero)
```

#### Paso 3: Calcular valores correctos
Con los raw de las 4 esquinas:
- px = remap(y, y_TL, y_TR, 0, 320)  # y_TL=izquierda, y_TR=derecha
- py = remap(x, x_TL, x_BL, 0, 240)  # x_TL=arriba, x_BL=abajo

#### Paso 4: Recompilar firmware con valores baked in
```bash
# En WSL2
cd ~/lvgl_micropython_build/lvgl_micropython
# Editar api_drivers/common_api_drivers/indev/xpt2046.py
python3 make.py esp32 BOARD=ESP32_GENERIC DISPLAY=ili9341 INDEV=xpt2046 --flash-size=4
cp build/lvgl_micropy_ESP32_GENERIC-4.bin /mnt/c/dev/py/esp3224/firmware.bin
```

### Procedimiento de flash (IMPORTANTE - requiere modo bootloader manual)
1. Mantener BOOT presionado
2. Presionar y soltar RESET
3. Soltar BOOT
4. Ejecutar inmediatamente:
```
python -m esptool --chip esp32 --port COM7 -b 460800 write-flash --flash-mode dio --flash-size 4MB --flash-freq 40m --erase-all 0x0 firmware.bin
```

### Subir archivos después de flash limpio
```
python -m mpremote connect COM7 exec "import os; [os.mkdir(d) for d in ['app','app/ports','app/domain','app/ui']]; print('OK')"

python -m mpremote connect COM7 cp app/__init__.py :app/__init__.py + cp app/ports/display_port.py :app/ports/display_port.py + cp app/ports/led_port.py :app/ports/led_port.py + cp app/domain/counter_service.py :app/domain/counter_service.py + cp app/domain/led_service.py :app/domain/led_service.py + cp app/ui/components.py :app/ui/components.py + cp app/ui/screens.py :app/ui/screens.py + cp main.py :main.py + reset
```

### ADVERTENCIA: No dejar procesos python zombie
Antes de flashear, verificar que no hay procesos mpremote corriendo:
- Desconectar/reconectar USB libera el puerto
- taskkill /F /IM python.exe si es necesario

## Hardware
- Board: ESP32-2432S028R (Cheap Yellow Display 2.8")
- COM: COM7
- USB: a la derecha (orientación estándar)
- LED RGB: GPIO4(R), GPIO16(G), GPIO17(B) — active LOW
- WSL2: Ubuntu-22.04, usuario fury
- Build dir: ~/lvgl_micropython_build/lvgl_micropython

## Archivos importantes en workspace
- `firmware.bin` — último firmware compilado
- `xpt2046.py` — driver touch con calibración actual
- `app/ui/components.py` — scroll deshabilitado (set_scrollbar_mode OFF)
- `app/ui/screens.py` — prints para video en botones
- `cal_measure.py` — script para medir raw del touch (subir como main temporal)
- `FIRMWARE_BUILD_GUIDE.md` — guía completa de compilación y calibración
