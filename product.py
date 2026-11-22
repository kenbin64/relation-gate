"""The product detector: find z = (x - a)(y - b) + c in three columns, read a, b and c off the shape, keep only the
residual, and say how much of the column the rule reached. PLAN-PRODUCT.md has the bars.

Two readings, kept separate so one can check the other:
  read_shape(x, y, z)   the geometry: look down x and the (y, z) points are a bow tie pinched at y = b, with the
                        band sitting at height c there; look down y and the pinch is at x = a
  fit(x, y, z)          the established method: least squares on 1, x, y, xy, which gives the same numbers
detect(x, y, z)         both, the rule, the residual, and the verdict: a product, or not one
"""
import math
import zlib


# ---------------------------------------------------------------------------------------------- reading the shape
def pinch(u, z, bins=25):
    """The bow tie's pinch: where its two edges cross. Looking down one axis of a product, the points (u, z) lie
    between two straight edges that meet at the pinch. Bin u into equal-count groups, take the top and bottom of z
    in each bin as points on the two edges, fit a line to each edge, and the crossing is the pinch: its position
    is the offset and its height is the constant. Read from the shape, not fitted to the surface."""
    order = sorted(range(len(u)), key=lambda i: u[i])
    size = max(3, len(u) // bins)
    groups = [order[i:i + size] for i in range(0, len(order) - size + 1, size)]
    upper, lower = [], []
    for g in groups:
        zs = [z[i] for i in g]; centre = sum(u[i] for i in g) / len(g)
        upper.append((centre, max(zs))); lower.append((centre, min(zs)))
    # the edges cross at the pinch, so on one side the upper edge is one line and past the pinch it is the other;
    # fit each edge as two half-lines meeting at the crossing, choosing the crossing that fits both edges best
    best = None
    for k in range(2, len(groups) - 2):
        left_u, right_u = upper[:k], upper[k:]; left_l, right_l = lower[:k], lower[k:]
        # left of the pinch the upper edge continues as the lower edge on the right, and the other way round
        edge1, edge2 = line(left_u + right_l), line(left_l + right_u)
        err = sum((m * c + b - v) ** 2 for (m, b), pts in ((edge1, left_u + right_l), (edge2, left_l + right_u)) for c, v in pts)
        if best is None or err < best[0]: best = (err, edge1, edge2)
    _, (m1, b1), (m2, b2) = best
    if abs(m1 - m2) < 1e-12: return sum(u) / len(u), sum(z) / len(z)
    u0 = (b2 - b1) / (m1 - m2)
    return u0, m1 * u0 + b1


def line(points):
    """Least-squares line through points: slope, intercept."""
    n = len(points); sx = sum(p[0] for p in points); sy = sum(p[1] for p in points)
    sxx = sum(p[0] * p[0] for p in points); sxy = sum(p[0] * p[1] for p in points)
    d = n * sxx - sx * sx
    if abs(d) < 1e-12: return 0.0, sy / n
    m = (n * sxy - sx * sy) / d
    return m, (sy - m * sx) / n


def read_shape(x, y, z):
    """a from the view down y (pinch along x), b from the view down x (pinch along y), c from the band's height."""
    b, c_from_x = pinch(y, z)
    a, c_from_y = pinch(x, z)
    return {'a': a, 'b': b, 'c': (c_from_x + c_from_y) / 2}


# ---------------------------------------------------------------------------------------------- the established check
def fit(x, y, z, extra=None):
    """Least squares of z on 1, x, y, xy (and an extra column w when one is given). If z = (x - a)(y - b) + c then
    z = ab + c - b x - a y + xy, so the coefficient of xy is 1 (or a scale), of x is -b, of y is -a, and the
    constant is ab + c. With w, the rule is a product plus k w: a product and another column side by side."""
    cols = [[1.0] * len(x), x, y, [xi * yi for xi, yi in zip(x, y, strict=True)]]
    if extra is not None: cols.append(list(extra))
    n = len(cols)
    ata = [[sum(cols[r][i] * cols[c][i] for i in range(len(x))) for c in range(n)] for r in range(n)]
    atz = [sum(cols[r][i] * z[i] for i in range(len(x))) for r in range(n)]
    coef = solve(ata, atz)
    k0, kx, ky, kxy = coef[:4]
    if abs(kxy) < 1e-12: return {'scale': 0.0, 'a': float('nan'), 'b': float('nan'), 'c': float('nan'), 'k': 0.0}
    a, b = -ky / kxy, -kx / kxy
    return {'scale': kxy, 'a': a, 'b': b, 'c': (k0 - kxy * a * b) / kxy, 'k': coef[4] if extra is not None else 0.0}


def solve(m, v):
    """Gaussian elimination with partial pivoting, for the 4 by 4 normal equations."""
    n = len(v); a = [row[:] + [v[i]] for i, row in enumerate(m)]
    for col in range(n):
        p = max(range(col, n), key=lambda r: abs(a[r][col])); a[col], a[p] = a[p], a[col]
        if abs(a[col][col]) < 1e-15: raise ValueError('the columns are not independent')
        for r in range(n):
            if r != col:
                f = a[r][col] / a[col][col]
                for c in range(col, n + 1): a[r][c] -= f * a[col][c]
    return [a[i][n] / a[i][i] for i in range(n)]


# ---------------------------------------------------------------------------------------------- the verdict
def spread(v):
    m = sum(v) / len(v)
    return math.sqrt(sum((t - m) ** 2 for t in v) / len(v))


def detect(x, y, z, precision=0.01, extra=None):
    """The rule, the residual, and whether this is a product at all. `precision` is the data's own resolution
    (cents by default), used to compare the compressed size of the residual with the column's. `extra` is a
    fourth column the rule may add alongside the product (z = product + k w)."""
    shape = read_shape(x, y, z); f = fit(x, y, z, extra)
    sz = spread(z)
    if f['scale'] == 0.0 or any(math.isnan(f[k]) for k in ('a', 'b', 'c')):
        return {'product': False, 'rule': None, 'shape': shape, 'fit': f, 'agree': {}, 'reached': 0.0, 'spread_z': sz,
                'spread_residual': sz, 'bytes_z': packed(z, precision), 'bytes_residual': None, 'residual': list(z)}
    s, a, b, c, k = f['scale'], f['a'], f['b'], f['c'], f['k']
    w = extra if extra is not None else [0.0] * len(x)
    rule = [s * (xi - a) * (yi - b) + s * c + k * wi for xi, yi, wi in zip(x, y, w, strict=True)]
    residual = [zi - ri for zi, ri in zip(z, rule, strict=True)]
    sr = spread(residual)
    reached = 1 - sr / sz if sz else 0.0
    product = reached >= 0.5
    agree = {k: abs(shape[k] - f[k]) <= 0.05 * max(sz, 1e-9) + 0.02 * max(spread(x if k == 'a' else y) if k != 'c' else sz, 1e-9) for k in ('a', 'b', 'c')}
    text = f'z = {s:.4g} * (x - {a:.4g}) * (y - {b:.4g}) + {s * c:.4g}' + (f' + {k:.4g} * w' if extra is not None else '')
    return {'product': product, 'rule': text if product else None,
            'shape': shape, 'fit': f, 'agree': agree, 'reached': reached, 'spread_z': sz, 'spread_residual': sr,
            'bytes_z': packed(z, precision), 'bytes_residual': packed(residual, precision) if product else None, 'residual': residual}


def packed(values, precision):
    """Compressed size of the values at the given precision: the honest size of storing them."""
    ints = [round(v / precision) for v in values]
    raw = ','.join(str(i) for i in ints).encode()
    return len(zlib.compress(raw, 9))


if __name__ == '__main__':
    import random
    r = random.Random(1)
    x = [r.uniform(-5, 5) for _ in range(400)]; y = [r.uniform(-5, 5) for _ in range(400)]
    a, b, c = 1.5, -2.0, 3.0
    z = [(xi - a) * (yi - b) + c for xi, yi in zip(x, y, strict=True)]
    d = detect(x, y, z)
    print('exact product, true a=1.5 b=-2 c=3')
    print(f"  read off the shape: a={d['shape']['a']:.3f} b={d['shape']['b']:.3f} c={d['shape']['c']:.3f}   fit: a={d['fit']['a']:.3f} b={d['fit']['b']:.3f} c={d['fit']['c']:.3f}")
    print(f"  rule: {d['rule']}   reached {d['reached']:.1%} of the column; residual spread {d['spread_residual']:.2e}; bytes z {d['bytes_z']} residual {d['bytes_residual']}")
    zn = [zi + r.gauss(0, 0.5) for zi in z]
    d = detect(x, y, zn)
    print(f"with noise 0.5: residual spread {d['spread_residual']:.3f} (the noise was 0.5); reached {d['reached']:.1%}; bytes z {d['bytes_z']} residual {d['bytes_residual']}")
    d = detect(x, y, [xi + yi for xi, yi in zip(x, y, strict=True)])
    print(f"z = x + y: product? {d['product']}; reached {d['reached']:.1%}")
