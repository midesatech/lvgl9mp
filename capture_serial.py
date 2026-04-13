import serial
import time

s = serial.Serial('COM7', 115200, timeout=0.1)
print("Leyendo serial - toca las esquinas del CYD...")
print("Ctrl+C para parar")

start = time.time()
try:
    while time.time() - start < 60:  # 60 segundos
        data = s.read(256)
        if data:
            text = data.decode('utf-8', errors='replace')
            # Solo mostrar lineas con valores validos (no X=0 Y=4095)
            for line in text.split('\n'):
                if 'TOUCH' in line and 'X_raw=0' not in line:
                    print(line.strip(), flush=True)
except KeyboardInterrupt:
    pass

s.close()
print("\nFin")
