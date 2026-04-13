# Guía de Compilación: LVGL9 + MicroPython para ESP32-2432S028R (CYD)

> **IMPORTANTE**: Esta guía es específica para el board **ESP32-2432S028R**
> (Cheap Yellow Display 2.8"). Otros boards CYD (3.5", 4.3") requieren
> configuración diferente.

## Resumen

Guía completa para compilar el firmware `lvgl_micropython` en **Linux o macOS**,
incluyendo dos patches críticos para el touch XPT2046:

1. **Fix XPT2046 `_normalize`** — calibración de ejes para el CYD
2. **Fix PR #454 `pointer_framework`** — bug en transformación affine del touch

Sin estos patches el touch no funciona correctamente en MicroPython, aunque
en Arduino/C sí funciona porque las librerías C manejan la calibración internamente.

---

## Repositorio base

El firmware se compila desde:
```
https://github.com/lvgl-micropython/lvgl_micropython
```

Este es el repositorio **original** que usamos. El commit estable probado
para el ESP32-2432S028R es `15a414b`.

> **Nota**: El repo `de-dh/ESP32-Cheap-Yellow-Display-Micropython-LVGL` tiene
> un firmware precompilado alternativo que también incluye el fix PR#454.
> Sin embargo, compilar desde el repo original da más control sobre los patches.

---

## 1. Requisitos del sistema

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
# Instalar Homebrew si no está disponible: https://brew.sh
brew install cmake ninja python3 git wget
pip3 install esptool mpremote
```

> En macOS el puerto serie será `/dev/cu.usbserial-XXXX` en lugar de `/dev/ttyUSB0`.
> Usar `ls /dev/cu.*` para encontrar el puerto correcto.

---

## 2. Clonar el repositorio

> **Importante:** No usar `--recursive` ni `git submodule init`.
> El script `make.py` gestiona los submódulos automáticamente.

```bash
git clone https://github.com/lvgl-micropython/lvgl_micropython
cd lvgl_micropython
git checkout 15a414b
```

---

## 3. Patch 1: Fix XPT2046 `_normalize` para el CYD

El XPT2046 del ESP32-2432S028R tiene los ejes X/Y intercambiados respecto
al display. El driver genérico no lo sabe — hay que parchear `_normalize`.

```bash
cat > /tmp/patch_xpt.py << 'EOF'
import re

path = 'api_drivers/common_api_drivers/indev/xpt2046.py'
with open(path, 'r') as f:
    content = f.read()

old = r'    def _normalize\(self, x, y\):.*?return px, py'
new = '''    def _normalize(self, x, y):
        # ESP32-2432S028R (CYD 2.8") MADCTL 0x20 - USB a la derecha
        # Ejes intercambiados: X fisico = vertical, Y fisico = horizontal
        # Valores medidos con lapiz resistivo:
        # TL=(x~570,y~564) TR=(x~450,y~3505) BL=(x~3432,y~620) BR=(x~3632,y~3473)
        px = pointer_framework.remap(y, 371, 3335, 0, self._orig_width)
        py = pointer_framework.remap(x, 600, 3371, 0, self._orig_height)
        return px, py'''

result = re.sub(old, new, content, flags=re.DOTALL)
assert result != content, "Patron no encontrado - verificar version del repo"
with open(path, 'w') as f:
    f.write(result)
print('Patch XPT2046 OK')
EOF
python3 /tmp/patch_xpt.py
```

---

## 4. Patch 2: Fix PR #454 `pointer_framework`

Bug crítico en el cálculo de la transformación affine del touch. Sin este fix,
la calibración interactiva no funciona correctamente.

**El bug** (líneas ~83-84 del archivo original):
```python
# BUG: x ya modificado se usa para calcular y
x = int(round(x * cal.alphaX + y * cal.betaX + cal.deltaX))
y = int(round(x * cal.alphaY + y * cal.betaY + cal.deltaY))  # x incorrecto!
```

**Aplicar el fix:**
```bash
cat > /tmp/patch_pf.py << 'EOF'
path = 'api_drivers/py_api_drivers/frozen/indev/pointer_framework.py'
with open(path, 'r') as f:
    content = f.read()

old = ('            x = int(round(x * cal.alphaX + y * cal.betaX + cal.deltaX))\n'
       '            y = int(round(x * cal.alphaY + y * cal.betaY + cal.deltaY))')

new = ('            # Fix PR#454: usar x e y originales para ambos calculos\n'
       '            x_orig = x\n'
       '            y_orig = y\n'
       '            x = int(round(x_orig * cal.alphaX + y_orig * cal.betaX + cal.deltaX))\n'
       '            y = int(round(x_orig * cal.alphaY + y_orig * cal.betaY + cal.deltaY))')

assert old in content, "Patron no encontrado - verificar version del repo"
content = content.replace(old, new)
with open(path, 'w') as f:
    f.write(content)
print('Patch pointer_framework PR#454 OK')
EOF
python3 /tmp/patch_pf.py
```

---

## 5. Compilar el firmware

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

## 6. Flashear el firmware

### Instalar esptool
```bash
pip3 install esptool
```

### Modo bootloader manual (requerido)
El ESP32 debe estar en modo bootloader para flashear:
1. Mantener presionado el botón **BOOT** (GPIO0)
2. Presionar y soltar **RESET** (EN)
3. Soltar **BOOT**
4. Ejecutar el comando de flash inmediatamente

### Flashear
```bash
# Linux
python3 -m esptool --chip esp32 --port /dev/ttyUSB0 \
    -b 460800 --before default-reset --after hard-reset \
    write-flash --flash-mode dio --flash-size 4MB \
    --flash-freq 40m --erase-all 0x0 \
    build/lvgl_micropy_ESP32_GENERIC-4.bin

# macOS (reemplazar XXXX con tu puerto)
python3 -m esptool --chip esp32 --port /dev/cu.usbserial-XXXX \
    -b 460800 --before default-reset --after hard-reset \
    write-flash --flash-mode dio --flash-size 4MB \
    --flash-freq 40m --erase-all 0x0 \
    build/lvgl_micropy_ESP32_GENERIC-4.bin
```

> `--erase-all` borra el filesystem. Necesitarás subir los archivos de la app después.

---

## 7. Subir archivos de la app

```bash
# Instalar mpremote
pip3 install mpremote

# Reemplazar PORT con tu puerto (/dev/ttyUSB0 o /dev/cu.usbserial-XXXX)
PORT=/dev/ttyUSB0

# Crear estructura de directorios
python3 -m mpremote connect $PORT exec \
    "import os; [os.mkdir(d) for d in ['app','app/ports','app/domain','app/ui']]"

# Subir todos los archivos
python3 -m mpremote connect $PORT \
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

## 8. Calibración del touch XPT2046

### Por qué es necesario

El touch resistivo XPT2046 del CYD no es lineal. El remap lineal del Patch 1
da una aproximación, pero la calibración affine por 3 puntos da precisión
comparable a Arduino/C.

### Calibración interactiva (recomendada)

```bash
# 1. Subir script de calibración
python3 -m mpremote connect $PORT cp calibrate_touch.py :main.py
python3 -m mpremote connect $PORT reset

# 2. Seguir instrucciones en pantalla:
#    - Aparece un círculo rojo en 3 posiciones
#    - Presionar y mantener el lápiz sobre cada círculo
#    - El sistema captura 8 muestras por punto
#    - La calibración se guarda automáticamente en NVS

# 3. Restaurar app original
python3 -m mpremote connect $PORT cp main.py :main.py
python3 -m mpremote connect $PORT reset
```

### Coeficientes de calibración del ESP32-2432S028R (referencia)

Estos coeficientes fueron medidos en un board específico. Pueden variar
entre unidades pero sirven como punto de partida:

```
alphaX=1.39742   betaX=0.1696867  deltaX=-63.0
alphaY=0.1105651 betaY=1.29914    deltaY=-48.44595
mirrorX=False    mirrorY=False
Namespace NVS: XPT2046_2
```

### Restaurar calibración manualmente

Si se pierde la calibración (por flash con --erase-all), restaurar con:

```bash
python3 -m mpremote connect $PORT exec "
from touch_cal_data import TouchCalData
c = TouchCalData('XPT2046_2')
c.alphaX = 1.39742
c.betaX = 0.1696867
c.deltaX = -63.0
c.alphaY = 0.1105651
c.betaY = 1.29914
c.deltaY = -48.44595
c.mirrorX = False
c.mirrorY = False
c._is_dirty = True
c.save()
print('Calibracion restaurada OK')
"
```

> **Nota**: El namespace NVS (`XPT2046_2`) depende del ID del indev.
> Verificar con: `python3 -m mpremote connect $PORT exec "import xpt2046, machine; ..."`
> Si el ID es diferente, ajustar el namespace.

---

## 9. Configuración del display

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

## 10. Pinout del ESP32-2432S028R

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

## 11. Notas técnicas sobre los patches

### Por qué estos patches no están en el repo original

- **Patch XPT2046**: Los valores de calibración son específicos de cada board.
  El repo original usa valores genéricos (0-4090) que no funcionan con el CYD.

- **Patch PR#454**: Es un bug reportado y corregido en el PR #454 del repo
  `lvgl-micropython/lvgl_micropython`. Al momento de compilar con commit
  `15a414b`, este fix no estaba mergeado. Verificar si ya está incluido en
  versiones más recientes antes de aplicarlo manualmente:
  ```bash
  grep -n "x_orig" api_drivers/py_api_drivers/frozen/indev/pointer_framework.py
  # Si retorna resultados, el fix ya está incluido
  ```

### Aplicar patches a versiones más recientes del repo

Si usas un commit más reciente que `15a414b`:

1. Verificar si PR#454 ya está mergeado (ver comando arriba)
2. Los valores de `_normalize` del Patch 1 son específicos del CYD 2.8"
   y deben aplicarse siempre independientemente de la versión

### Persistencia de los patches

Los archivos en el filesystem del ESP32 tienen **prioridad** sobre los
módulos frozen del firmware:

| Archivo | Ubicación recomendada |
|---------|----------------------|
| `xpt2046.py` | Baked in firmware (Patch 1 aplicado antes de compilar) |
| `pointer_framework.py` | Baked in firmware (Patch 2 aplicado antes de compilar) |

Si se compila con ambos patches, no es necesario subir estos archivos
al filesystem después de cada flash.

---

## 12. Notas sobre el touch resistivo

- **Área muerta en bordes**: ~5-10% en cada borde no responde al touch
- **No linealidad**: el remap lineal es una aproximación; la calibración
  affine da mejor resultado
- **Diferencia lápiz/dedo**: el lápiz resistivo requiere más presión
- **Comparación con Arduino**: en Arduino/C la librería `XPT2046_Touchscreen`
  con `setRotation()` maneja la calibración internamente. En MicroPython
  hay que hacerlo manualmente con los patches descritos en esta guía.

### Compensar área muerta con ext_click_area

```python
btn.set_ext_click_area(10)  # 10px extra en todos los lados
```

---

## 13. Recursos y referencias

- [lvgl_micropython](https://github.com/lvgl-micropython/lvgl_micropython) — Repo original usado
- [PR #454 bug fix](https://github.com/lvgl-micropython/lvgl_micropython/pull/454) — Fix pointer_framework
- [ESP32-CYD MicroPython LVGL](https://github.com/de-dh/ESP32-Cheap-Yellow-Display-Micropython-LVGL) — Firmware alternativo precompilado
- [ESP32-Cheap-Yellow-Display](https://github.com/witnessmenow/ESP32-Cheap-Yellow-Display) — Repo oficial CYD con ejemplos Arduino
- [LVGL 9 Docs](https://docs.lvgl.io/master/) — Documentación oficial LVGL
- [LVGL 8.3 Docs con ejemplos MicroPython](https://docs.lvgl.io/8.3/) — Mayoría de ejemplos MicroPython están aquí
