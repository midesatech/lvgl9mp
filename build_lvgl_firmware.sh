#!/bin/bash
# =============================================================
# Script de compilacion: lvgl_micropython para ESP32-2432S028
# LVGL 9 + MicroPython + drivers ILI9341 + XPT2046 compilados en C
# Ejecutar desde WSL2 Ubuntu
# =============================================================

set -e  # salir si cualquier comando falla

echo "============================================"
echo " LVGL MicroPython - ESP32-2432S028 (CYD)"
echo "============================================"

# --- 1. Instalar dependencias del sistema ---
echo ""
echo "[1/4] Instalando dependencias del sistema..."
sudo apt-get update -qq
sudo apt-get install -y \
    build-essential \
    cmake \
    ninja-build \
    python3 \
    python3-venv \
    python3-pip \
    libusb-1.0-0-dev \
    git \
    wget \
    flex \
    bison \
    gperf \
    ccache \
    libffi-dev \
    libssl-dev \
    dfu-util \
    libusb-1.0-0

echo "[1/4] Dependencias instaladas OK"

# --- 2. Clonar lvgl_micropython ---
echo ""
echo "[2/4] Clonando lvgl_micropython..."

# Directorio de trabajo en home del usuario WSL
WORKDIR="$HOME/lvgl_micropython_build"
mkdir -p "$WORKDIR"
cd "$WORKDIR"

if [ -d "lvgl_micropython" ]; then
    echo "  -> Directorio ya existe, eliminando para clonar limpio..."
    rm -rf lvgl_micropython
fi

# IMPORTANTE: NO usar --recursive ni submodule init (lo indica el README)
git clone https://github.com/lvgl-micropython/lvgl_micropython
cd lvgl_micropython

echo "[2/4] Repo clonado OK"

# --- 3. Compilar firmware ---
echo ""
echo "[3/4] Compilando firmware para ESP32-2432S028..."
echo "  Board  : ESP32_GENERIC"
echo "  Display: ILI9341 (compilado en C)"
echo "  Touch  : XPT2046 (compilado en C)"
echo "  Flash  : 4MB"
echo ""
echo "  Esto puede tardar 10-20 minutos la primera vez..."
echo ""

python3 make.py esp32 \
    BOARD=ESP32_GENERIC \
    DISPLAY=ili9341 \
    INDEV=xpt2046 \
    --flash-size=4

echo ""
echo "[3/4] Compilacion completada OK"

# --- 4. Mostrar resultado y comando de flash ---
echo ""
echo "[4/4] Firmware generado:"
ls -lh build/*.bin 2>/dev/null || ls -lh build/

echo ""
echo "============================================"
echo " COMO FLASHEAR EL FIRMWARE"
echo "============================================"
echo ""
echo "Opcion A - Desde WSL (necesitas WSL USB Manager):"
echo "  Conecta el ESP32, adjuntalo a WSL con WSL USB Manager"
echo "  Luego ejecuta el comando que aparece al final del build"
echo ""
echo "Opcion B - Desde Windows directamente (MAS FACIL):"
echo "  1. Copia el .bin a Windows:"
echo "     cp build/lvgl_micropy_ESP32_GENERIC-4.bin /mnt/c/Users/\$USER/Desktop/"
echo ""
echo "  2. Instala esptool en Windows si no lo tenes:"
echo "     pip install esptool"
echo ""
echo "  3. Flashea desde PowerShell/CMD (ajusta el puerto COM):"
echo "     python -m esptool --chip esp32 --port COM10 -b 460800 --before default-reset --after hard-reset write-flash --flash-mode dio --flash-size 4MB --flash-freq 40m --erase-all 0x0 lvgl_micropy_ESP32_GENERIC-4.bin"
echo ""
echo "============================================"
echo " CODIGO DE PRUEBA PARA EL CYD"
echo "============================================"
echo ""
echo "Guarda esto como main.py y subilo con Thonny:"
cat << 'PYCODE'

# main.py - Test basico LVGL9 para ESP32-2432S028 (CYD)
# Pines del CYD: CLK=14, MOSI=13, MISO=12, CS=15, DC=2, BL=21
# Touch SPI: CLK=25, MOSI=32, MISO=39, CS=33

import lcd_bus
from micropython import const
import machine

# --- Configuracion display ---
_WIDTH  = const(320)
_HEIGHT = const(240)
_BL     = const(21)
_DC     = const(2)
_RST    = const(12)

_MOSI   = const(13)
_MISO   = const(12)
_SCK    = const(14)
_LCD_CS = const(15)
_LCD_FREQ = const(40000000)

# Touch usa SPI separado en el CYD
_T_MOSI = const(32)
_T_MISO = const(39)
_T_SCK  = const(25)
_T_CS   = const(33)
_T_FREQ = const(2500000)

# --- Bus SPI display ---
spi_bus = machine.SPI.Bus(host=1, mosi=_MOSI, miso=_MISO, sck=_SCK)

display_bus = lcd_bus.SPIBus(
    spi_bus=spi_bus,
    freq=_LCD_FREQ,
    dc=_DC,
    cs=_LCD_CS,
)

import ili9341
import lvgl as lv

display = ili9341.ILI9341(
    data_bus=display_bus,
    display_width=_WIDTH,
    display_height=_HEIGHT,
    backlight_pin=_BL,
    color_space=lv.COLOR_FORMAT.RGB565,
    color_byte_order=ili9341.BYTE_ORDER_BGR,
    rgb565_byte_swap=True,
)

# --- Touch ---
touch_spi = machine.SPI.Bus(host=2, mosi=_T_MOSI, miso=_T_MISO, sck=_T_SCK)
touch_dev = machine.SPI.Device(spi_bus=touch_spi, freq=_T_FREQ, cs=_T_CS)

import xpt2046
import task_handler

display.set_power(True)
display.init()
display.set_backlight(100)

indev = xpt2046.XPT2046(touch_dev)

if not indev.is_calibrated:
    indev.calibrate()

th = task_handler.TaskHandler()

# --- UI de prueba ---
scrn = lv.screen_active()
scrn.set_style_bg_color(lv.color_hex(0x1a1a2e), 0)

label = lv.label(scrn)
label.set_text("LVGL9 + CYD OK!")
label.set_style_text_color(lv.color_hex(0x00ff88), 0)
label.center()

btn = lv.button(scrn)
btn.set_size(160, 50)
btn.align(lv.ALIGN.CENTER, 0, 60)
btn_label = lv.label(btn)
btn_label.set_text("Toca aqui")
btn_label.center()

PYCODE

echo ""
echo "Build completado exitosamente."
