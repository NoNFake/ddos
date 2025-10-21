from concurrent.futures import ThreadPoolExecutor
import sys
def tastk(n):
    # return n + 2
    print(
        n +2
    )



g = []
with ThreadPoolExecutor(max_workers=10) as executor:
    for i in range(10):
        # t = executor.submit(tastk, i)
        t = executor.submit(tastk, i)
        g.append(t)

f = sys.getsizeof(g)
print("size:    ", f)


