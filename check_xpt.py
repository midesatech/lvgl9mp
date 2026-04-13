import xpt2046
src = open(xpt2046.__file__).read()
idx = src.find('_normalize')
print(src[idx:idx+200])
