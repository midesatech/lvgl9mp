import struct
from esp32 import NVS

# Coordenadas LVGL actuales (sin calibracion correcta):
# TL=(190,89) TR=(192,88) BL=(107,158) BR=(104,161)
# Deben mapearse a:
# TL=(0,0) TR=(319,0) BL=(0,239) BR=(319,239)
#
# La calibracion del framework aplica:
# x_final = alphaX * x_raw + betaX * y_raw + deltaX
# y_final = alphaY * x_raw + betaY * y_raw + deltaY
#
# Donde x_raw e y_raw son las coordenadas LVGL sin calibrar.
# Necesitamos:
# 0   = alphaX * 190 + betaX * 89  + deltaX  (TL x)
# 319 = alphaX * 192 + betaX * 88  + deltaX  (TR x)
# 0   = alphaX * 107 + betaX * 158 + deltaX  (BL x)
#
# De TL y TR: 319 = alphaX*(192-190) + betaX*(88-89) = 2*alphaX - betaX
# De TL y BL: 0 = alphaX*(107-190) + betaX*(158-89) = -83*alphaX + 69*betaX
# => betaX = 83/69 * alphaX = 1.2029 * alphaX
# => 319 = 2*alphaX - 1.2029*alphaX = 0.7971*alphaX
# => alphaX = 319/0.7971 = 400.2
# => betaX = 1.2029 * 400.2 = 481.2
# => deltaX = -alphaX*190 - betaX*89 = -400.2*190 - 481.2*89 = -76038 - 42827 = -118865
#
# Para Y:
# 0   = alphaY * 190 + betaY * 89  + deltaY  (TL y)
# 0   = alphaY * 192 + betaY * 88  + deltaY  (TR y)
# 239 = alphaY * 107 + betaY * 158 + deltaY  (BL y)
#
# De TL y TR: 0 = alphaY*(192-190) + betaY*(88-89) = 2*alphaY - betaY
# => betaY = 2*alphaY
# De TL y BL: 239 = alphaY*(107-190) + betaY*(158-89) = -83*alphaY + 69*betaY
# => 239 = -83*alphaY + 69*2*alphaY = -83*alphaY + 138*alphaY = 55*alphaY
# => alphaY = 239/55 = 4.345
# => betaY = 2 * 4.345 = 8.691
# => deltaY = -alphaY*190 - betaY*89 = -4.345*190 - 8.691*89 = -825.6 - 773.5 = -1599.1

alphaX = 400.2
betaX  = 481.2
deltaX = -118865.0
alphaY = 4.345
betaY  = 8.691
deltaY = -1599.1
mirrorX = 0
mirrorY = 0

blob = bytearray(struct.pack('<ffffffBB',
    alphaX, betaX, deltaX,
    alphaY, betaY, deltaY,
    mirrorX, mirrorY
))

# Namespace correcto es XPT2046_2
nvs = NVS('XPT2046_2')
nvs.set_blob('ts_config', memoryview(blob))
nvs.commit()
print("Calibracion guardada en XPT2046_2 OK")
