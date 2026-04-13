# Guía de Compilación: LVGL9 + MicroPython para ESP32-2432S028R (CYD)

## Resumen

Guía completa para compilar el firmware `lvgl_micropython` en **Linux o macOS** para el board
**ESP32-2432S028R** (Cheap Yellow Display), incluyendo el fix del touch XPT2046 y el bug fix
del PR #454 del `pointer_framework`.

---

## Requisitos del sistema

### Linux (Ubuntu 22.04 / Debian)
```bash
sudo apt-get update
sudo apt-get install -y \
    build-essential cmake ninja-build \
    python3 python3-venv python3-pip \
    libusb-1.0-0-dev git wget flex bison \
    gperf ccache libffi-dev libssl-dev
```

### macOS
```bash
brew install cmake ninja python3 git wget
pip3 install esptool
```

> En macOS el puerto serie será `/dev/cu.usbserial-XXXX` en lugar de `/dev/ttyUSB0`.

---

## 1. Clonar el repositorio

> **Importante:** No usar `--recursive` ni `git submodule init`. El script `make.py` gestiona
> los submódulos automáticamente.

```bash
git clone https://github.com/lvgl-micropython/lvgl_micropython
cd lvgl_micropython
git checkout 15a414b
```

> El commit `15a414b` es el último estable probado con el ESP32-2432S028R.
> La rama `main` también funciona pero puede tener cambios no probados.

---

## 2. Aplicar el fix del touch XPT2046

El XPT2046 del CYD tiene los ejes X/Y intercambiados respecto al display.
Hay que parchear `_normalize` en el driver:

```bash
cat > /tmp/patch_xpt.py << 'EOF'
import re

path = 'api_drivers/common_api_drivers/indev/xpt2046.py'
with open(path, 'r') as f:
    content = f.read()

old = r'    def _normalize\(self, x, y\):.*?return px, py'
new = '''    def _normalize(self, x, y):
        # ESP32-2432S028R (CYD) MADCTL 0x20 - USB a la derecha
        # Valores medidos con lapiz resistivo:
        # TL=(x~570,y~564) TR=(x~450,y~3505) BL=(x~3432,y~620) BR=(x~3632,y~3473)
        px = pointer_framework.remap(y, 371, 3335, 0, self._orig_width)
        py = pointer_framework.remap(x, 600, 3371, 0, self._orig_height)
        return px, py'''

result = re.sub(old, new, content, flags=re.DOTALL)
assert result != content, "Patron no encontrado"
with open(path, 'w') as f:
    f.write(result)
print('XPT2046 patch OK')
EOF
python3 /tmp/patch_xpt.py
```

---

## 3. Aplicar el bug fix PR #454 del pointer_framework

Este es el fix más importante. Corrige un bug en el cálculo de la transformación
affine del touch que causaba coordenadas incorrectas:

```bash
cat > /tmp/patch_pf.py << 'EOF'
path = 'api_drivers/py_api_drivers/frozen/indev/pointer_framework.py'
with open(path, 'r') as f:
    content = f.read()

# Bug: x ya modificado se usaba para calcular y
old = '''            x = int(round(x * cal.alphaX + y * cal.betaX + cal.deltaX))
            y = int(round(x * cal.alphaY + y * cal.betaY + cal.deltaY))'''

# Fix: guardar x e y originales antes de modificarlos
new = '''            # Fix PR#454: usar x e y originales para ambos calculos
            x_orig = x
            y_orig = y
            x = int(round(x_orig * cal.alphaX + y_orig * cal.betaX + cal.deltaX))
            y = int(round(x_orig * cal.alphaY + y_orig * cal.betaY + cal.deltaY))'''

assert old in content, "Patron no encontrado - verificar version del repo"
content = content.replace(old, new)
with open(path, 'w') as f:
    f.write(content)
print('pointer_framework PR#454 fix OK')
EOF
python3 /tmp/patch_pf.py
```

---

## 4. Compilar el firmware

```bash
python3 make.py esp32 \
    BOARD=ESP32_GENERIC \
    DISPLAY=ili9341 \
    INDEV=xpt2046 \
    --flash-size=4
```

La primera compilación descarga el ESP-IDF (~1 GB) y tarda 15-25 minutos.
Las compilaciones posteriores reutilizan el cache y tardan ~3-5 minutos.

El firmware generado queda en:
```
build/lvgl_micropy_ESP32_GENERIC-4.bin
```

---

## 5. Flashear el firmware

### Instalar esptool
```bash
pip3 install esptool
```

### Modo bootloader manual (requerido)
El ESP32 debe estar en modo bootloader para flashear:
1. Mantener presionado el botón **BOOT** (GPIO0)
2. Presionar y soltar **RESET** (EN)
3. Soltar **BOOT**

### Flashear
```bash
# Linux
python3 -m esptool --chip esp32 --port /dev/ttyUSB0 \
    -b 460800 --before default-reset --after hard-reset \
    write-flash --flash-mode dio --flash-size 4MB \
    --flash-freq 40m --erase-all 0x0 \
    build/lvgl_micropy_ESP32_GENERIC-4.bin

# macOS
python3 -m esptool --chip esp32 --port /dev/cu.usbserial-XXXX \
    -b 460800 --before default-reset --after hard-reset \
    write-flash --flash-mode dio --flash-size 4MB \
    --flash-freq 40m --erase-all 0x0 \
    build/lvgl_micropy_ESP32_GENERIC-4.bin
```

> `--erase-all` borra el filesystem. Necesitarás subir los archivos de la app después.

---

## 6. Subir archivos de la app

Instalar mpremote:
```bash
pip3 install mpremote
```

Crear directorios y subir archivos:
```bash
# Crear estructura de directorios
python3 -m mpremote connect /dev/ttyUSB0 exec \
    "import os; [os.mkdir(d) for d in ['app','app/ports','app/domain','app/ui']]"

# Subir todos los archivos
python3 -m mpremote connect /dev/ttyUSB0 \
    cp app/__init__.py :app/__init__.py \
    + cp app/ports/display_port.py :app/ports/display_port.py \
    + cp app/ports/led_port.py :app/ports/led_port.py \
    + cp app/domain/counter_service.py :app/domain/counter_service.py \
    + cp app/domain/led_service.py :app/domain/led_service.py \
    + cp app/ui/components.py :app/ui/components.py \
    + cp app/ui/screens.py :app/ui/screens.py \
    + cp main.py :main.py \
    + reset
```

---

## 7. Configuración del display

```python
from micropython import const
import machine, lcd_bus, lvgl as lv, task_handler, ili9341, xpt2046

_DISPLAY_ROT = const(0x20)  # landscape USB a la derecha

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

indev_bus = machine.SPI.Bus(host=2, mosi=32, miso=39, sck=25)
indev_device = machine.SPI.Device(spi_bus=indev_bus, freq=2000000, cs=33)
indev = xpt2046.XPT2046(device=indev_device)
task_handler.TaskHandler()
```

### Tabla MADCTL según orientación

| Orientación | MADCTL | USB |
|-------------|--------|-----|
| Landscape USB derecha | `0x20` | derecha ← estándar CYD |
| Landscape USB izquierda | `0xE0` | izquierda |
| Portrait | `0x40` | arriba |
| Portrait invertido | `0x80` | abajo |

---

## 8. Pinout del ESP32-2432S028R

| Función | GPIO |
|---------|------|
| Display MOSI | 13 |
| Display MISO | 12 |
| Display SCK | 14 |
| Display CS | 15 |
| Display DC | 2 |
| Display BL | 21 |
| Touch MOSI | 32 |
| Touch MISO | 39 |
| Touch SCK | 25 |
| Touch CS | 33 |
| Touch IRQ | 36 |
| LED R | 4 (active LOW) |
| LED G | 16 (active LOW) |
| LED B | 17 (active LOW) |
| LDR | 34 |
| SD MOSI | 23 |
| SD MISO | 19 |
| SD SCK | 18 |
| SD CS | 5 |

---

## 9. Calibración del touch XPT2046

### Valores de calibración (ESP32-2432S028R, USB derecha)

```python
# En xpt2046.py - _normalize para MADCTL 0x20
# Valores medidos con lápiz resistivo del kit
px = pointer_framework.remap(y, 371, 3335, 0, self._orig_width)
py = pointer_framework.remap(x, 600, 3371, 0, self._orig_height)
```

### Valores raw medidos en las esquinas

| Esquina | X_raw | Y_raw |
|---------|-------|-------|
| Top-left | ~570 | ~564 |
| Top-right | ~450 | ~3505 |
| Bot-left | ~3432 | ~620 |
| Bot-right | ~3632 | ~3473 |
| Centro | ~2066 | ~1947 |

> **Nota:** Y físico = eje horizontal de pantalla. X físico = eje vertical.
> Los ejes están intercambiados respecto al display.

### Cómo medir los valores raw de tu board

```python
# raw_measure.py - subir al ESP32 y tocar las 4 esquinas
# Ver archivo raw_measure.py en el repositorio
```

### Calibración affine interactiva (opcional)

El firmware soporta calibración affine por 3 puntos que se guarda en NVS:

```python
# En main.py, después de init_hardware():
display, indev = init_hardware()
if not indev.is_calibrated:
    indev.calibrate()   # muestra UI de calibración en pantalla
    indev._cal.save()   # guarda en NVS del ESP32
```

La calibración se guarda permanentemente y no se pierde al reiniciar.

---

## 10. Bug fix PR #454 — pointer_framework

### El problema

El `pointer_framework.py` del firmware base tiene un bug en el cálculo
de la transformación affine del touch:

```python
# BUG: x ya modificado se usa para calcular y
x = int(round(x * cal.alphaX + y * cal.betaX + cal.deltaX))
y = int(round(x * cal.alphaY + y * cal.betaY + cal.deltaY))  # x incorrecto!
```

### El fix

```python
# FIX: usar x e y originales para ambos cálculos
x_orig = x
y_orig = y
x = int(round(x_orig * cal.alphaX + y_orig * cal.betaX + cal.deltaX))
y = int(round(x_orig * cal.alphaY + y_orig * cal.betaY + cal.deltaY))
```

### Aplicar sin recompilar

Subir `pointer_framework.py` al filesystem del ESP32 (tiene prioridad sobre el frozen):

```bash
python3 -m mpremote connect /dev/ttyUSB0 cp pointer_framework.py :pointer_framework.py
python3 -m mpremote connect /dev/ttyUSB0 reset
```

El archivo `pointer_framework.py` con el fix está en el repositorio.

---

## 11. Persistencia de los patches

Los archivos en el filesystem del ESP32 tienen **prioridad** sobre los módulos
frozen del firmware. Esto significa:

| Archivo | Ubicación | Prioridad |
|---------|-----------|-----------|
| `xpt2046.py` | filesystem `/` | Alta — sobreescribe frozen |
| `pointer_framework.py` | filesystem `/` | Alta — sobreescribe frozen |
| Módulos frozen | firmware | Baja — solo si no hay en filesystem |

**Flujo recomendado después de cada flash:**

```bash
# 1. Crear directorios
python3 -m mpremote connect PORT exec \
    "import os; [os.mkdir(d) for d in ['app','app/ports','app/domain','app/ui']]"

# 2. Subir app + patches críticos
python3 -m mpremote connect PORT \
    cp pointer_framework.py :pointer_framework.py \
    + cp xpt2046.py :xpt2046.py \
    + cp app/__init__.py :app/__init__.py \
    + cp app/ports/display_port.py :app/ports/display_port.py \
    + cp app/ports/led_port.py :app/ports/led_port.py \
    + cp app/domain/counter_service.py :app/domain/counter_service.py \
    + cp app/domain/led_service.py :app/domain/led_service.py \
    + cp app/ui/components.py :app/ui/components.py \
    + cp app/ui/screens.py :app/ui/screens.py \
    + cp main.py :main.py \
    + reset
```

---

## 12. Notas sobre el touch resistivo

El XPT2046 resistivo del CYD tiene limitaciones físicas:

- **Área muerta en bordes**: ~5-10% en cada borde no responde al touch
- **No linealidad**: el touch no es perfectamente lineal — un remap lineal
  es una aproximación. La calibración affine (sección 9) da mejor resultado
- **Diferencia lápiz/dedo**: el lápiz resistivo requiere más presión que el dedo
- **Comparación con Arduino**: en Arduino/C la librería `XPT2046_Touchscreen`
  usa `setRotation()` que aplica transformación interna. En MicroPython hay
  que hacer la transformación manualmente en `_normalize`

### Compensar área muerta con ext_click_area

```python
btn.set_ext_click_area(15)  # 15px extra en todos los lados
```

---

## 13. Recursos y referencias

- [lvgl_micropython](https://github.com/lvgl-micropython/lvgl_micropython) — Bindings oficiales
- [ESP32-CYD MicroPython LVGL](https://github.com/de-dh/ESP32-Cheap-Yellow-Display-Micropython-LVGL) — Repo con firmware precompilado y calibración
- [PR #454 bug fix](https://github.com/lvgl-micropython/lvgl_micropython/issues/454) — Fix del pointer_framework
- [ESP32-Cheap-Yellow-Display](https://github.com/witnessmenow/ESP32-Cheap-Yellow-Display) — Repo oficial CYD con ejemplos Arduino
- [LVGL 9 Docs](https://docs.lvgl.io/master/) — Documentación oficial LVGL
