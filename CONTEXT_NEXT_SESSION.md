# Contexto para próxima sesión - ESP32-2432S028R (CYD)

## Estado actual (2026-04-14 - sesión 2)

### Lo que funciona
- Firmware LVGL9 + MicroPython compilado con ambos patches (firmware.bin)
- Display ILI9341: landscape, USB a la derecha, MADCTL 0x20
- App de widgets completa y navegable
- Scroll deshabilitado en todas las pantallas
- **Botón Next: funciona correctamente**
- **Slider: llega hasta 93 con dedo, 51 con lápiz**
- Prints en consola al presionar botones de color y Clicks
- Bug fix PR #454 aplicado (pointer_framework.py en filesystem)

### Patches activos en filesystem ESP32
```
/pointer_framework.py  ← fix PR#454 (x_orig para calculo correcto)
/xpt2046.py            ← calibracion touch CYD
/app/...               ← app de widgets
```

### Calibración touch actual (xpt2046.py)
```python
touch_threshold = 400
confidence = 5
margin = 50

def _normalize(self, x, y):
    px = pointer_framework.remap(y, 371, 3335, 0, self._orig_width)
    py = pointer_framework.remap(x, 600, 3371, 0, self._orig_height)
    return px, py
```

### Síntomas pendientes (limitaciones hardware)
- Slider salta a 51 al tocar el círculo en 40 → offset ~11 unidades
- Checkboxes responden ligeramente fuera del cuadro → área muerta física
- Lápiz requiere más presión que dedo → normal en touch resistivo

### Próximo paso opcional: calibración affine interactiva
El firmware soporta calibración por 3 puntos que se guarda en NVS:
```python
# Agregar en main.py después de init_hardware():
display, indev = init_hardware()
if not indev.is_calibrated:
    indev.calibrate()
    indev._cal.save()
```
Esto daría precisión comparable a Arduino/C.

### Procedimiento flash + subir archivos
Ver FIRMWARE_BUILD_GUIDE.md sección 5 y 11.

**IMPORTANTE**: Después de cada flash, subir también:
- `pointer_framework.py` (fix PR#454)
- `xpt2046.py` (calibración touch)

### Hardware
- Board: ESP32-2432S028R (CYD 2.8")
- COM: COM7, USB a la derecha
- LED RGB: GPIO4(R), GPIO16(G), GPIO17(B) — active LOW
- WSL2: Ubuntu-22.04, usuario fury
- Build: ~/lvgl_micropython_build/lvgl_micropython
