# Guía de Compilación: LVGL9 + MicroPython para ESP32-2432S028R (CYD)

## Resumen

Este documento describe cómo compilar el firmware `lvgl_micropython` en Linux para el board
**ESP32-2432S028R** (Cheap Yellow Display), incluyendo el fix del touch XPT2046 para landscape.

---

## Requisitos del sistema

- Ubuntu 22.04 LTS (o equivalente Debian)
- Python 3.10+
- Git
- ~5 GB de espacio libre (ESP-IDF + toolchain)

---

## 1. Instalar dependencias

```bash
sudo apt-get update
sudo apt-get install -y \
    build-essential cmake ninja-build \
    python3 python3-venv python3-pip \
    libusb-1.0-0-dev git wget flex bison \
    gperf ccache libffi-dev libssl-dev
```

---

## 2. Clonar el repositorio

> **Importante:** No usar `--recursive` ni `git submodule init`. El script `make.py` gestiona
> los submódulos automáticamente.

```bash
git clone https://github.com/lvgl-micropython/lvgl_micropython
cd lvgl_micropython
```

### 2.1 Usar el commit estable para el CYD

El commit `15a414b` fue identificado como estable para el ESP32-2432S028R. Sin embargo,
la rama `main` tiene **71 commits adicionales** (a abril 2026) incluyendo soporte para
MicroPython 1.27.0 y fixes de drivers.

**Opción A — Commit probado (conservador):**
```bash
git checkout 15a414b
```

**Opción B — Rama main actual (recomendado para fork):**
```bash
# Usar main directamente y probar si el CYD funciona
# Si hay boot loop, usar bisect para encontrar el commit problemático:
git bisect start
git bisect bad HEAD
git bisect good 15a414b
# git bisect good/bad según resultado de cada prueba
```

> **Nota:** La rama `touch-calibration` en el repo upstream sugiere que el autor
> está trabajando en mejoras al touch. Vale la pena revisar si ya incluye fixes
> para el CYD antes de aplicar el patch manual del `_normalize`.

---

## 3. Aplicar el fix del touch XPT2046 para el CYD

El XPT2046 del ESP32-2432S028R tiene los ejes X/Y intercambiados y rangos raw distintos
al valor genérico (10-4090). Los valores reales medidos son:

| Esquina | X_raw | Y_raw |
|---------|-------|-------|
| Top-left | 3830 | 3671 |
| Top-right | 3811 | 320 |
| Bot-left | 258 | 3662 |
| Bot-right | 288 | 334 |

Aplicar el patch:

```bash
cat > /tmp/patch_xpt.py << 'EOF'
with open('api_drivers/common_api_drivers/indev/xpt2046.py', 'r') as f:
    content = f.read()

old = '''    def _normalize(self, x, y):
        x = pointer_framework.remap(
            x, _MIN_RAW_COORD, _MAX_RAW_COORD, 0, self._orig_width
        )
        y = pointer_framework.remap(
            y, _MIN_RAW_COORD, _MAX_RAW_COORD, 0, self._orig_height
        )

        return x, y'''

new = '''    def _normalize(self, x, y):
        # ESP32-2432S028R (CYD) MADCTL 0x20 - USB a la derecha
        # Ejes intercambiados e invertidos segun medicion raw:
        # Top-left=(3830,3671) Top-right=(3811,320) Bot-left=(258,3662) Bot-right=(288,334)
        px = pointer_framework.remap(y, 334, 3671, 0, self._orig_width)
        py = pointer_framework.remap(x, 288, 3830, 0, self._orig_height)
        return px, py'''

assert old in content, "Patron no encontrado - verificar version del repo"
content = content.replace(old, new)

with open('api_drivers/common_api_drivers/indev/xpt2046.py', 'w') as f:
    f.write(content)

print('Patch aplicado OK')
EOF

python3 /tmp/patch_xpt.py
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

```bash
# Instalar esptool si no está disponible
pip install esptool

# Flashear (reemplazar /dev/ttyUSB0 con tu puerto)
python -m esptool \
    --chip esp32 \
    --port /dev/ttyUSB0 \
    -b 460800 \
    --before default-reset \
    --after hard-reset \
    write-flash \
    --flash-mode dio \
    --flash-size 4MB \
    --flash-freq 40m \
    --erase-all 0x0 \
    build/lvgl_micropy_ESP32_GENERIC-4.bin
```

---

## 6. Configuración del display en MicroPython

```python
from micropython import const
import machine, lcd_bus, lvgl as lv, task_handler, ili9341

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

# Touch
indev_bus = machine.SPI.Bus(host=2, mosi=32, miso=39, sck=25)
indev_device = machine.SPI.Device(spi_bus=indev_bus, freq=2000000, cs=33)

import xpt2046
indev = xpt2046.XPT2046(device=indev_device)
task_handler.TaskHandler()
```

### Tabla de valores MADCTL según orientación

| Orientación | MADCTL | USB |
|-------------|--------|-----|
| Landscape USB izquierda | `0xE0` | izquierda |
| Landscape USB derecha | `0x20` | derecha (posición estándar) |
| Portrait | `0x40` | arriba |
| Portrait invertido | `0x80` | abajo |

---

## 7. Pinout del ESP32-2432S028R

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
| LED R | 4 (active LOW) |
| LED G | 16 (active LOW) |
| LED B | 17 (active LOW) |

---

## 8. Estrategia de fork para múltiples boards

Para soportar múltiples boards (2.8", 3.5", 4.3") sin hardcodear valores:

1. Hacer fork de `lvgl-micropython/lvgl_micropython` en tu cuenta GitHub
2. Crear rama `feature/multi-board-touch`
3. Modificar `XPT2046.__init__` para aceptar `x_min`, `x_max`, `y_min`, `y_max`, `swap_xy`
4. En cada `main.py` pasar los valores específicos del board

Esto permite un solo firmware genérico y configuración por software.

---

## 9. Touch paramétrico para múltiples boards

En lugar de hardcodear los rangos raw en el firmware, se puede modificar el driver
`xpt2046.py` para aceptar parámetros en el constructor. Esto permite usar un solo
firmware para todos tus boards y configurar el touch desde el `main.py`.

### 9.1 Modificar xpt2046.py

Editar `api_drivers/common_api_drivers/indev/xpt2046.py`:

**Paso 1 — Agregar parámetros al `__init__`:**

```python
def __init__(
    self,
    device,
    touch_cal=None,
    startup_rotation=pointer_framework.lv.DISPLAY_ROTATION._0,
    debug=False,
    # Nuevos parametros para calibracion por board
    x_min=10,       # valor raw minimo del eje X fisico
    x_max=4090,     # valor raw maximo del eje X fisico
    y_min=10,       # valor raw minimo del eje Y fisico
    y_max=4090,     # valor raw maximo del eje Y fisico
    swap_xy=False,  # True si los ejes X/Y estan intercambiados
    invert_x=False, # True si el eje X esta invertido
    invert_y=False, # True si el eje Y esta invertido
):
    self._x_min = x_min
    self._x_max = x_max
    self._y_min = y_min
    self._y_max = y_max
    self._swap_xy = swap_xy
    self._invert_x = invert_x
    self._invert_y = invert_y
    # ... resto del __init__ sin cambios
```

**Paso 2 — Reemplazar `_normalize`:**

```python
def _normalize(self, x, y):
    # Intercambiar ejes si es necesario
    if self._swap_xy:
        x, y = y, x
        x_min, x_max = self._y_min, self._y_max
        y_min, y_max = self._x_min, self._x_max
    else:
        x_min, x_max = self._x_min, self._x_max
        y_min, y_max = self._y_min, self._y_max

    # Mapear a coordenadas de pantalla (con o sin inversion)
    if self._invert_x:
        px = pointer_framework.remap(x, x_max, x_min, 0, self._orig_width)
    else:
        px = pointer_framework.remap(x, x_min, x_max, 0, self._orig_width)

    if self._invert_y:
        py = pointer_framework.remap(y, y_max, y_min, 0, self._orig_height)
    else:
        py = pointer_framework.remap(y, y_min, y_max, 0, self._orig_height)

    return px, py
```

### 9.2 Cómo medir los valores raw de tu board

Antes de configurar un board nuevo, medir los valores raw del touch tocando
las 4 esquinas con este script:

```python
# raw_measure.py - subir al ESP32 y tocar las 4 esquinas
import machine, lcd_bus, lvgl as lv, task_handler, ili9341

# ... inicializar display ...

cs_pin = machine.Pin(33, machine.Pin.OUT)
touch_spi = machine.SPI.Bus(host=2, mosi=32, miso=39, sck=25)
touch_dev_raw = machine.SPI.Device(spi_bus=touch_spi, freq=1000000, cs=33)

def read_raw(cmd):
    buf = bytearray(3)
    buf[0] = cmd
    out = bytearray(3)
    touch_dev_raw.write_readinto(buf, out)
    return ((out[1] << 8) | out[2]) >> 3

# Usar un timer para mostrar valores en pantalla mientras se toca
lbl = lv.label(lv.screen_active())
lbl.center()

def timer_cb(t):
    x = read_raw(0xD0)  # X raw
    y = read_raw(0x90)  # Y raw
    z = read_raw(0xB0)  # presion
    if z > 100:
        lbl.set_text("X={} Y={} Z={}".format(x, y, z))

lv.timer_create(timer_cb, 200, None)
task_handler.TaskHandler()
```

Anotar los valores en cada esquina:

| Esquina | X_raw | Y_raw |
|---------|-------|-------|
| Top-left | ? | ? |
| Top-right | ? | ? |
| Bot-left | ? | ? |
| Bot-right | ? | ? |

### 9.3 Configuración por board en main.py

Con el driver paramétrico, cada board se configura así:

```python
import xpt2046

# ESP32-2432S028R (CYD 2.8") - USB a la derecha - MADCTL 0x20
indev = xpt2046.XPT2046(
    device=indev_device,
    x_min=288,    # Bot-right X_raw
    x_max=3830,   # Top-left X_raw
    y_min=334,    # Bot-right Y_raw
    y_max=3671,   # Top-left Y_raw
    swap_xy=True, # ejes intercambiados en este board
    invert_x=True,
    invert_y=True,
)

# ESP32-3248S035R (CYD 3.5") - valores a medir con raw_measure.py
indev = xpt2046.XPT2046(
    device=indev_device,
    x_min=300,
    x_max=3800,
    y_min=300,
    y_max=3800,
    swap_xy=False,  # ajustar segun medicion
    invert_x=False,
    invert_y=False,
)
```

> **Nota:** El board de 4.3" (ESP32-8048S043) usa touch capacitivo GT911,
> no XPT2046. Requiere un driver diferente.

---

## 9. Agregar módulos C propios

```bash
python3 make.py esp32 \
    BOARD=ESP32_GENERIC \
    DISPLAY=ili9341 \
    INDEV=xpt2046 \
    --flash-size=4 \
    USER_C_MODULE=./mi_modulo/mi_modulo.cmake
```

Estructura mínima de un módulo C:

```
mi_modulo/
├── mi_modulo.c
├── mi_modulo.cmake
└── micropython.cmake
```
