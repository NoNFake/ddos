# import ctypes
# libc = ctypes.cdll.LoadLibrary("libc.so.6")

import random
import sys
r=  random._urandom(1024*1024*1024).hex()
# print(r)
print(sys.getsizeof(r))
