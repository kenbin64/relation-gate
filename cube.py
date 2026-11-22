"""The multi-facing cube: the saddle z = xy in a cube, its 24 orientations, the six faces it shows, the hole, and
what rotation does to the hole. Everything here is read from the object by asking it; nothing is stored.

Three uses:
  orientations()             the 24 rotations of a cube, each as what it does to the saddle (axis, hand), and the
                             six faces the saddle can show
  views(tilt)                look at the saddle through each face: how much of the face is occupied, and where the
                             hole (the pinch of the bow tie) sits; tilt the saddle and the hole moves to tan(tilt)
  encode / decode / verify   a chain of cells where the seams carry the message: a matched seam is 0, a declared
                             bridge (the hand flips) is 1. The rule regenerates every cell from the bridges alone,
                             so only the bridges are stored: the residual face is the data. A seam that is neither
                             matched nor declared is an error at a known position.
"""
import itertools
import math

AXES = 'xyz'


# ---------------------------------------------------------------------------------------------- the 24 rotations
def rotations():
    """Every rotation of a cube, as a signed permutation matrix with determinant +1."""
    out = []
    for perm in itertools.permutations(range(3)):
        for signs in itertools.product((1, -1), repeat=3):
            m = [[0] * 3 for _ in range(3)]
            for r, c in enumerate(perm): m[r][c] = signs[r]
            if det(m) == 1: out.append(tuple(tuple(row) for row in m))
    return out


def det(m):
    return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
            + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))


def apply(m, p):
    return tuple(sum(m[r][c] * p[c] for c in range(3)) for r in range(3))


def compose(a, b):
    """The rotation b then a."""
    return tuple(tuple(sum(a[r][k] * b[k][c] for k in range(3)) for c in range(3)) for r in range(3))


def face_of(m):
    """Which saddle the rotation m turns z = xy into: (axis, hand), read off the rotated points."""
    points = [apply(m, (a, b, a * b)) for a in (-1, 0, 1, 2) for b in (-1, 0, 1, 2)]
    for h in range(3):
        u, v = [n for n in range(3) if n != h]
        for s in (1, -1):
            if all(p[h] == s * p[u] * p[v] for p in points): return AXES[h], '+' if s > 0 else '-'
    raise ValueError('a rotated saddle is always a saddle')


def orientations():
    """The 24 rotations grouped by the face they show: six faces, four rotations each."""
    faces = {}
    for m in rotations(): faces.setdefault(face_of(m), []).append(m)
    return faces


QUARTER = {'x': ((1, 0, 0), (0, 0, -1), (0, 1, 0)), 'y': ((0, 0, 1), (0, 1, 0), (-1, 0, 0)), 'z': ((0, -1, 0), (1, 0, 0), (0, 0, 1))}


# ---------------------------------------------------------------------------------------------- the views and the hole
def views(tilt_deg=0.0, about='y', samples=81):
    """Look at the saddle through each face of the cube after tilting it `tilt_deg` about `about`.
    For each face: the share of the face that is occupied, and where the hole sits (the height at which the
    occupied band is narrowest), or None when the face is full and there is no hole."""
    t = math.radians(tilt_deg); c, s = math.cos(t), math.sin(t)
    rot = {'x': lambda x, y, z: (x, y * c - z * s, y * s + z * c), 'y': lambda x, y, z: (x * c + z * s, y, -x * s + z * c),
           'z': lambda x, y, z: (x * c - y * s, x * s + y * c, z)}[about]
    g = [-1 + 2 * i / (samples - 1) for i in range(samples)]
    pts = [rot(x, y, x * y) for x in g for y in g]
    out = {}
    for drop, name in ((2, 'down z'), (0, 'down x'), (1, 'down y')):
        keep = [n for n in range(3) if n != drop]
        cell = lambda v: max(0, min(int((v + 1) / 2 * samples), samples - 1))
        grid = {}
        for p in pts:
            key = cell(p[keep[0]])
            grid.setdefault(key, set()).add(cell(p[keep[1]]))
        occupied = sum(len(v) for v in grid.values()) / (samples * samples)
        widths = {k: len(v) for k, v in grid.items()}
        narrowest = min(widths, key=widths.get)
        hole = None if occupied > 0.95 else -1 + 2 * narrowest / (samples - 1)
        out[name] = {'occupied': round(occupied, 3), 'hole': None if hole is None else round(hole, 2)}
    return out


def hole_position(tilt_deg):
    """Where the hole sits on the side face after a tilt, by the rule: tan(tilt), inside the cube while under 45."""
    return math.tan(math.radians(tilt_deg)) if tilt_deg < 45 else None


# ---------------------------------------------------------------------------------------------- the chain: seams as data
def turned(axis, hand, about):
    """(axis, hand) after a quarter turn about `about`."""
    m = QUARTER[about]
    base = next(r for r in rotations() if face_of(r) == (axis, hand))
    return face_of(compose(m, base))


def encode(bits, start=('z', '+')):
    """Bits to a chain of cells. 0: the next cell matches (a joined seam). 1: the next cell is turned about its own
    axis, which flips the hand (a bridge). Returns the cells and the residual: the positions of the bridges."""
    cells = [start]; bridges = []
    for i, bit in enumerate(bits):
        axis, hand = cells[-1]
        cells.append(turned(axis, hand, axis) if bit else (axis, hand))
        if bit: bridges.append(i)
    return cells, bridges


def bloom(length, bridges, start=('z', '+')):
    """The rule regenerates the whole chain from the bridges alone: only the residual was stored."""
    cells = [start]
    for i in range(length):
        axis, hand = cells[-1]
        cells.append(turned(axis, hand, axis) if i in set(bridges) else (axis, hand))
    return cells


def decode(cells):
    """The bits are the seams: matched is 0, flipped hand is 1."""
    return [0 if cells[i] == cells[i + 1] else 1 for i in range(len(cells) - 1)]


def verify(cells, bridges):
    """Every seam must be either matched or a declared bridge. Anything else is an error at a known seam."""
    declared = set(bridges)
    for i in range(len(cells) - 1):
        a, b = cells[i], cells[i + 1]
        if a == b and i in declared: return False, f'seam {i}: declared a bridge but the hands match'
        if a != b and i not in declared: return False, f'seam {i}: the hands differ ({a[0]}{a[1]} to {b[0]}{b[1]}) and no bridge was declared'
        if a != b and (a[0] != b[0]): return False, f'seam {i}: the axis changed ({a[0]} to {b[0]}); a bridge only flips the hand'
    return True, f'{len(cells) - 1} seams: {len(declared)} bridges, the rest matched'


# ---------------------------------------------------------------------------------------------- the whole
def rotate_all(cells, m):
    """Turn the whole chain by one rotation of the cube: every cell shows a different face, the object is the same."""
    out = []
    for axis, hand in cells:
        base = next(r for r in rotations() if face_of(r) == (axis, hand))
        out.append(face_of(compose(m, base)))
    return out


def whole(cells):
    """What the chain IS, independent of how it is held: the seams. Rotate the whole cube and every face changes,
    but which seams match and which flip does not. The whole is the message; the faces are the view."""
    return tuple(decode(cells))


def collapse(cells):
    """Six faces and then the whole die: a block of cells becomes one cell at the next level, by the face most of
    them show. A tie is a fork, a die landed on its edge, and a fork is decided by a person, not here."""
    counts = {}
    for c in cells: counts[c] = counts.get(c, 0) + 1
    top = max(counts.values()); faces = sorted(f for f, n in counts.items() if n == top)
    if len(faces) == 1: return faces[0]
    return ('fork', faces)


if __name__ == '__main__':
    faces = orientations()
    print(f'{sum(len(v) for v in faces.values())} rotations, {len(faces)} faces: ' + ', '.join(f'{a}{h} x{len(v)}' for (a, h), v in sorted(faces.items())))
    for tilt in (0, 15, 30, 45):
        v = views(tilt)
        print(f'tilt {tilt:2d}: ' + '  '.join(f'{k} occupied {d["occupied"]:.0%}' + (f', hole at {d["hole"]:+.2f}' if d['hole'] is not None else ', full') for k, d in v.items())
              + f'   (rule: hole at {hole_position(tilt):+.2f})' if hole_position(tilt) is not None else f'   (rule: the hole has left the cube)')
    bits = [1, 0, 1, 1, 0, 0, 1, 0]
    cells, bridges = encode(bits)
    print(f'bits {bits} -> stored residual (bridge positions) {bridges}; the chain regrown from them: ' + ' '.join(a + h for a, h in bloom(len(bits), bridges)))
    print('decoded', decode(bloom(len(bits), bridges)), '| verify', verify(cells, bridges))
    bad = list(cells); bad[4] = ('y', '+')
    print('a corrupted cell:', verify(bad, bridges))
    held = rotate_all(cells, QUARTER['x'])
    print('the whole cube turned about x: faces ' + ' '.join(a + h for a, h in held) + f'; the whole (the seams) {whole(held)} unchanged: {whole(held) == whole(cells)}')
    print('a block of cells collapsed to one at the next level:', collapse(cells), '| a tie:', collapse([('z', '+'), ('z', '-')]))
