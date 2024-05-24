import tensorflow as tf
print("tensorflow version", tf.__version__)

x = [[3.]]
y = [[4.]]
print("Result: {}".format(tf.matmul(x, y)))