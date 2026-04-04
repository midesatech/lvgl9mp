import serial
import time

s = serial.Serial('COM5', 115200, timeout=0.1)
print("Leyendo serial - toca las esquinas del CYD...")
print("Ctrl+C para parar")

start = time.time()
try:
    while time.time() - start < 30:
        data = s.read(256)
        if data:
            text = data.decode('utf-8', errors='replace')
            print(text, end='', flush=True)
except KeyboardInterrupt:
    pass

s.close()
print("\nFin")
