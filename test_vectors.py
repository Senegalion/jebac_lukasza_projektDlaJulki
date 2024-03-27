import math
import numpy as np

def target_to_left(vector_from, vector_to) -> bool:
    vector_from = np.atleast_1d(vector_from)
    vector_to = np.atleast_1d(vector_to)
    return np.cross(vector_from[:2], vector_to[:2]) > 0

def angle(vector_from, vector_to) -> float:
    vector_from = np.atleast_1d(vector_from)
    vector_to = np.atleast_1d(vector_to)
    dot = np.dot(vector_from[:2], vector_to[:2])
    dst1 = np.linalg.norm(vector_from[:2])
    dst2 = np.linalg.norm(vector_to[:2])
    return math.acos(dot / (dst1 * dst2)) *360/(2*math.pi)

v1 = np.array([0, -1])
v2 = np.array([1, -1])

print(f"angle: {angle(v1, v2)}")
print(f"left : {target_to_left(v1, v2)}")
