import serial
import time

s = serial.Serial('COM5', 115200, timeout=0.1)
print('Listo - presiona RESET en el ESP32 ahora...')

start = time.time()
output = ''
while time.time() - start < 15:
    data = s.read(512)
    if data:
        text = data.decode('utf-8', errors='replace')
        output += text
        print(text, end='', flush=True)
    # Parar cuando aparezca el prompt o un error claro
    if '>>>' in output or 'Traceback' in output:
        time.sleep(2)  # capturar un poco mas
        data = s.read(512)
        if data:
            print(data.decode('utf-8', errors='replace'), end='')
        break

s.close()
print('\n--- FIN CAPTURA ---')
