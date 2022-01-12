import numpy


class EaeSens:
    L1 = 0
    L2 = 0
    L3 = 0
    EXT = 0
    OUT = 0
    line_no = 0
    sens_no = 0

    def __init__(self, L1, L2, L3, EXT, OUT, line_no, sens_no):
        self.L1 = L1
        self.L2 = L2
        self.L3 = L3
        self.EXT = EXT
        self.OUT = OUT
        self.line_no = line_no
        self.sens_no = sens_no


# obj1 = EaeSens(3, 3, 3)

array = numpy.ndarray((32,), dtype=EaeSens)

i = 0
for i in range(16):
    array[i] = EaeSens(0.0, 0.0, 0.0, 0, 0, 110, i)

a = 16
for a in range(32):
    array[a] = EaeSens(0.0, 0.0, 0.0, 0, 0, 400, a)

print((array[20].line_no, array[20].sens_no))
