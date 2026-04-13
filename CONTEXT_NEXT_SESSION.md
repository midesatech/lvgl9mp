# Contexto para próxima sesión - ESP32-2432S028R (CYD)

## Estado actual (2026-04-14 - MEJOR ESTADO)

### Lo que funciona
- Firmware LVGL9 + MicroPython compilado con patches (firmware.bin)
- Display ILI9341: landscape, USB a la derecha, MADCTL 0x20
- App de 7 pantallas completa y navegable
- Scroll deshabilitado en todas las pantallas
- **Botón Next: funciona correctamente**
- **Slider: va de 0 a 100, círculo se mueve con offset de solo 1-2 unidades**
- **Checkboxes: mejorados**
- Bug fix PR#454 aplicado (pointer_framework.py en filesystem)
- Calibración affine guardada en NVS (namespace XPT2046_2)
- Prints en consola al presionar botones

### Patches activos en filesystem ESP32
```
/pointer_framework.py  ← fix PR#454
/xpt2046.py            ← remap lineal (371,3335,600,3371)
/app/...               ← app de widgets
NVS XPT2046_2          ← coeficientes affine guardados
```

### Coeficientes affine guardados en NVS
```
alphaX=1.39742   betaX=0.1696867  deltaX=-83.9696
alphaY=0.1105651 betaY=1.29914    deltaY=-48.44595
mirrorX=False    mirrorY=False
```
Estos coeficientes fueron calculados con _normalize lineal activo.
Se aplican ENCIMA del remap lineal de _normalize.

### Calibración xpt2046.py actual
```python
touch_threshold = 400
confidence = 5
margin = 50

def _normalize(self, x, y):
    px = pointer_framework.remap(y, 371, 3335, 0, self._orig_width)
    py = pointer_framework.remap(x, 600, 3371, 0, self._orig_height)
    return px, py
```

### Síntoma pendiente menor
- Tocar entre dos botones a veces activa el botón de la izquierda
- Offset residual ~5-10px hacia la izquierda
- Se puede corregir ajustando deltaX en los coeficientes NVS:
  ```
  # Aumentar deltaX para correr touch a la derecha
  # Valor actual: -83.9696
  # Probar: -73 o -63 (sumar 10-20 al valor actual)
  python -m mpremote connect COM7 exec "from touch_cal_data import TouchCalData; c=TouchCalData('XPT2046_2'); c.deltaX=-73.0; c._is_dirty=True; c.save(); print('OK')"
  ```

### Para restaurar calibración si se pierde
```
python -m mpremote connect COM7 exec "from touch_cal_data import TouchCalData; c=TouchCalData('XPT2046_2'); c.alphaX=1.39742; c.betaX=0.1696867; c.deltaX=-83.9696; c.alphaY=0.1105651; c.betaY=1.29914; c.deltaY=-48.44595; c.mirrorX=False; c.mirrorY=False; c._is_dirty=True; c.save(); print('OK')"
```

### Procedimiento flash + restaurar todo
1. Flash firmware (BOOT+RESET):
```
python -m esptool --chip esp32 --port COM7 -b 460800 write-flash --flash-mode dio --flash-size 4MB --flash-freq 40m --erase-all 0x0 firmware.bin
```
2. Crear dirs y subir archivos:
```
python -m mpremote connect COM7 exec "import os; [os.mkdir(d) for d in ['app','app/ports','app/domain','app/ui']]"
python -m mpremote connect COM7 cp pointer_framework.py :pointer_framework.py + cp xpt2046.py :xpt2046.py + cp app/__init__.py :app/__init__.py + cp app/ports/display_port.py :app/ports/display_port.py + cp app/ports/led_port.py :app/ports/led_port.py + cp app/domain/counter_service.py :app/domain/counter_service.py + cp app/domain/led_service.py :app/domain/led_service.py + cp app/ui/components.py :app/ui/components.py + cp app/ui/screens.py :app/ui/screens.py + cp main.py :main.py + reset
```
3. Restaurar calibración NVS (ver arriba)

### Hardware
- Board: ESP32-2432S028R (CYD 2.8")
- COM: COM7, USB a la derecha
- LED RGB: GPIO4(R), GPIO16(G), GPIO17(B) — active LOW
- WSL2: Ubuntu-22.04, usuario fury
- Build: ~/lvgl_micropython_build/lvgl_micropython
