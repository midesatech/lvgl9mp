# Contexto para próxima sesión - ESP32-2432S028R (CYD)

## Estado actual (2026-04-13)

### Lo que funciona
- Firmware LVGL9 + MicroPython compilado y flasheado correctamente
- Display ILI9341 se ve bien, orientación landscape USB a la derecha (MADCTL 0x20)
- App de widgets se muestra: botones, slider, checkboxes, LED RGB, etc.
- Scroll deshabilitado en pantallas (`set_scrollbar_mode OFF` + `set_scroll_dir NONE`)
- Prints en consola al presionar botones de color y botón Clicks

### Problema pendiente: Touch descuadrado
El touch XPT2046 sigue sin funcionar correctamente:
- El slider solo llega hasta ~6-7 con dedo o lápiz (debería llegar a 100)
- Los botones responden pero en posición desplazada

### Valores de calibración actuales en xpt2046.py (filesystem)
```python
def _normalize(self, x, y):
    # Y fisico = eje horizontal (izq~564, der~3505)
    # X fisico = eje vertical   (arriba~450, abajo~3632)
    px = pointer_framework.remap(y, 564, 3505, 0, self._orig_width)
    py = pointer_framework.remap(x, 450, 3632, 0, self._orig_height)
    return px, py
```

### Valores raw medidos (del historial - confiables)
Tomados con lápiz resistivo, USB a la derecha, MADCTL 0x20:
```
TL (arriba-izq): x_raw~570,  y_raw~564
TR (arriba-der): x_raw~450,  y_raw~3505
BL (abajo-izq):  x_raw~3432, y_raw~620
BR (abajo-der):  x_raw~3632, y_raw~3473
Centro:          x_raw~2066, y_raw~1947
```

### Análisis del problema
1. Los ejes están intercambiados: X físico = movimiento vertical, Y físico = movimiento horizontal
2. El mapeo actual parece correcto en dirección pero el slider solo llega a ~7%
3. Posible causa: el rango Y (564-3505) cubre bien horizontal, pero el rango X (450-3632)
   puede estar mal para vertical — el slider se mueve horizontalmente, así que usa Y físico
4. El slider va de izquierda a derecha → usa Y físico → rango 564 a 3505 → debería funcionar
5. PERO si el slider solo llega a 7, significa que Y físico máximo que se detecta es ~780
   (7% de 3505-564 = ~205 unidades sobre 564 = ~769) → el touch no detecta más allá

### Hipótesis principal
El `touch_threshold = 400` puede estar filtrando toques válidos en la zona izquierda/derecha.
O bien el `confidence = 5` con `margin = 50` descarta muestras inconsistentes del borde.

### Lo que hay que probar en la próxima sesión

#### Opción A: Bajar touch_threshold y ajustar confidence
En xpt2046.py cambiar:
```python
touch_threshold = 200  # era 400
confidence = 3         # era 5
margin = 100           # era 50
```

#### Opción B: Medir raw reales con cal_measure.py
El script `cal_measure.py` está en el workspace. Subirlo como main.py temporal,
tocar las 4 esquinas físicas del display y anotar los valores TP_DATA que aparecen.
Esos son los valores raw REALES del ADC antes de normalizar.

#### Opción C: Recompilar firmware con valores correctos baked in
Una vez encontrados los valores correctos, compilar en WSL2:
```bash
cd ~/lvgl_micropython_build/lvgl_micropython
# Editar api_drivers/common_api_drivers/indev/xpt2046.py con valores correctos
python3 make.py esp32 BOARD=ESP32_GENERIC DISPLAY=ili9341 INDEV=xpt2046 --flash-size=4
```
El firmware compilado queda en build/lvgl_micropy_ESP32_GENERIC-4.bin
Copiarlo a Windows: cp build/lvgl_micropy_ESP32_GENERIC-4.bin /mnt/c/dev/py/esp3224/firmware.bin

### Flashear firmware (procedimiento correcto)
1. Mantener BOOT presionado
2. Presionar y soltar RESET
3. Soltar BOOT
4. Ejecutar: `python -m esptool --chip esp32 --port COM7 -b 460800 write-flash --flash-mode dio --flash-size 4MB --flash-freq 40m --erase-all 0x0 firmware.bin`

### Subir archivos después de flash
```
python -m mpremote connect COM7 exec "import os; [os.mkdir(d) for d in ['app','app/ports','app/domain','app/ui']]; print('OK')"

python -m mpremote connect COM7 cp app/__init__.py :app/__init__.py + cp app/ports/display_port.py :app/ports/display_port.py + cp app/ports/led_port.py :app/ports/led_port.py + cp app/domain/counter_service.py :app/domain/counter_service.py + cp app/domain/led_service.py :app/domain/led_service.py + cp app/ui/components.py :app/ui/components.py + cp app/ui/screens.py :app/ui/screens.py + cp main.py :main.py + reset
```

### IMPORTANTE: No subir xpt2046.py al filesystem
El firmware frozen tiene el xpt2046.py correcto. Si se sube uno al filesystem
puede quedar corrupto (problema que tuvimos hoy). Mejor compilar con los valores
correctos baked in.

## Hardware
- Board: ESP32-2432S028R (Cheap Yellow Display 2.8")
- COM: COM7
- USB: a la derecha (orientación estándar)
- LED RGB: GPIO4(R), GPIO16(G), GPIO17(B) — active LOW
- WSL2: Ubuntu-22.04, usuario fury
- Build dir: ~/lvgl_micropython_build/lvgl_micropython

## Archivos importantes
- `firmware.bin` — último firmware compilado (en workspace Windows)
- `xpt2046.py` — driver touch con calibración actual
- `app/ui/components.py` — scroll deshabilitado
- `app/ui/screens.py` — prints para video
- `cal_measure.py` — script para medir raw del touch
- `FIRMWARE_BUILD_GUIDE.md` — guía completa de compilación
