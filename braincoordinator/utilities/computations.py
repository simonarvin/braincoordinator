import numpy as np

def distance3d(p1, p2) -> float:
    return np.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2 + (p1[2]-p2[2])**2)

def distance2d(p1, p2) -> float:
    return np.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

def str_to_float(str:str) -> float:
    if str[0] == "-":
        return float(str[:2] + '.' + str[2:])
    else:
        return float(str[:1] + '.' + str[1:])

def to_decimal(*args):
    if len(args) != 1:
        return [format(arg, '.2f') for arg in args]
    else:
        return format(args[0], '.2f')
