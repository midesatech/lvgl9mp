import serial
import time

s = serial.Serial('COM5', 115200, timeout=2)
time.sleep(0.3)

# Ctrl+C x2 para interrumpir cualquier ejecucion
s.write(b'\x03\x03')
time.sleep(0.8)
s.read_all()  # limpiar buffer

# Sobrescribir main.py con contenido vacio via REPL
s.write(b"open('main.py','w').write('# empty')\r\n")
time.sleep(1.5)

out = s.read_all()
print('Response:', repr(out))

# Verificar que quedo bien
s.write(b"print(open('main.py').read())\r\n")
time.sleep(1)
out = s.read_all()
print('main.py content:', repr(out))

s.close()
print('Done')
