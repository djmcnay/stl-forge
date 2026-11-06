# Signed volume of a binary STL: sum dot(v0, cross(v1, v2)) / 6 over triangles.
import struct, sys
d = open(sys.argv[1], 'rb').read()
n = struct.unpack_from('<I', d, 80)[0]
vol = 0.0
for i in range(n):
    f = struct.unpack_from('<12f', d, 84 + 50 * i)
    v0, v1, v2 = f[3:6], f[6:9], f[9:12]
    vol += (v0[0] * (v1[1] * v2[2] - v1[2] * v2[1]) + v0[1] * (v1[2] * v2[0] - v1[0] * v2[2]) + v0[2] * (v1[0] * v2[1] - v1[1] * v2[0])) / 6
print(f"triangles: {n}  volume: {vol:.3f} mm^3")
