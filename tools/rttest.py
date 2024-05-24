import tensorrt
print(tensorrt.__version__)
assert tensorrt.Builder(tensorrt.Logger())