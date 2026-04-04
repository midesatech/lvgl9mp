import os

# Listar todos los archivos
print("Archivos en /:", os.listdir('/'))

# Borrar cualquier archivo de calibracion
for f in os.listdir('/'):
    if 'cal' in f.lower() or 'xpt' in f.lower() or 'touch' in f.lower():
        os.remove('/' + f)
        print("Borrado:", f)

print("Listo")
