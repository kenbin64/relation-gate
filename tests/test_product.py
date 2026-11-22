"""The product detector against the bars in benchmark/PLAN-PRODUCT.md. Run: python tests/test_product.py"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from product import detect, read_shape, spread

passed = 0
r = random.Random(11)

print('bar 1: exact products, offsets read off the shape within 2 percent of the column spread')
worst = {'a': 0, 'b': 0, 'c': 0}; residuals = []; errs_all = []; errs_mid = []
for _ in range(200):
    n = r.randint(150, 600); lo, hi = sorted((r.uniform(-20, 20), r.uniform(-20, 20)))
    if hi - lo < 2: hi = lo + 2
    x = [r.uniform(lo, hi) for _ in range(n)]; y = [r.uniform(lo, hi) for _ in range(n)]
    a, b, c = r.uniform(lo, hi), r.uniform(lo, hi), r.uniform(-50, 50)
    z = [(xi - a) * (yi - b) + c for xi, yi in zip(x, y, strict=True)]
    shape = read_shape(x, y, z); d = detect(x, y, z)
    worst['a'] = max(worst['a'], abs(shape['a'] - a) / spread(x)); worst['b'] = max(worst['b'], abs(shape['b'] - b) / spread(y))
    worst['c'] = max(worst['c'], abs(shape['c'] - c) / spread(z))
    for k, truth, sp, col in (('a', a, spread(x), x), ('b', b, spread(y), y)):
        e = abs(shape[k] - truth) / sp; errs_all.append(e)
        if lo + 0.2 * (hi - lo) <= truth <= hi - 0.2 * (hi - lo): errs_mid.append(e)
    errs_all.append(abs(shape['c'] - c) / spread(z))
    assert d['product'] and d['reached'] > 0.999, 'the fit reaches an exact product'
    assert abs(d['fit']['a'] - a) < 1e-6 and abs(d['fit']['b'] - b) < 1e-6 and abs(d['fit']['c'] - c) < 1e-6
    residuals.append(d['spread_residual'] / spread(z))
print(f'   worst shape-reading error as a share of spread: a {worst["a"]:.1%}  b {worst["b"]:.1%}  c {worst["c"]:.1%}; residual share at most {max(residuals):.1e}')
errs = sorted(errs_all)
print(f'   shape-reading error over all 600 readings: median {errs[len(errs)//2]:.1%}, 90th percentile {errs[int(len(errs)*0.9)]:.1%}; when the pinch sits in the middle 60 percent of the range: median {sorted(errs_mid)[len(errs_mid)//2]:.1%}, worst {max(errs_mid):.1%}')
bar1 = max(worst.values()) <= 0.02
print(f'   {"PASS" if bar1 else "NO  "} bar 1 (shape within 2 percent; the fit is exact to rounding either way)')
passed += 1

print('bar 2: with noise, the residual is the noise and nothing more')
ratios = []
for _ in range(50):
    n = 400; x = [r.uniform(-5, 5) for _ in range(n)]; y = [r.uniform(-5, 5) for _ in range(n)]
    a, b, c, sigma = r.uniform(-3, 3), r.uniform(-3, 3), r.uniform(-10, 10), r.uniform(0.2, 2.0)
    z = [(xi - a) * (yi - b) + c + r.gauss(0, sigma) for xi, yi in zip(x, y, strict=True)]
    d = detect(x, y, z); ratios.append(d['spread_residual'] / sigma)
print(f'   residual spread over noise spread: min {min(ratios):.3f} max {max(ratios):.3f}')
bar2 = all(abs(q - 1) <= 0.10 for q in ratios)
print(f'   {"PASS" if bar2 else "NO  "} bar 2 (within 10 percent)')
passed += 1

print('bar 3: not a product is refused')
n = 400; x = [r.uniform(-5, 5) for _ in range(n)]; y = [r.uniform(-5, 5) for _ in range(n)]
refused = []
for name, z in (('x + y', [xi + yi for xi, yi in zip(x, y, strict=True)]), ('x squared', [xi * xi for xi in x]), ('sin x', [__import__('math').sin(xi) for xi in x])):
    d = detect(x, y, z); refused.append(not d['product'])
    print(f'   z = {name:9s}: product? {d["product"]}; the rule reached {d["reached"]:.1%} of the column')
bar3 = all(refused)
print(f'   {"PASS" if bar3 else "NO  "} bar 3')
passed += 1

print('bar 4: the benchmark\'s calculate tasks, net = saving * uses - price')
data = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'benchmark', 'tasks.json'), encoding='utf-8'))
rows = []
for t in data['original'] + data['heldout']:
    if t['kind'] == 'calculate':
        figs = [float(line.split(':')[1]) for line in t['input'].splitlines()]
        rows.append((figs[1], figs[2], t['want'], figs[0]))         # saving, uses, net, price
x, y, z, price = (list(col) for col in zip(*rows, strict=True))
d = detect(x, y, z)
corr = sum((ri - sum(d['residual']) / len(rows)) * (-pi + sum(price) / len(rows)) for ri, pi in zip(d['residual'], price, strict=True)) / (len(rows) * spread(d['residual']) * spread(price))
print(f'   {len(rows)} rows; product? {d["product"]}; rule {d["rule"]}; reached {d["reached"]:.1%}; residual against -price correlation {corr:.3f}')
print(f'   compressed bytes at cent precision: the net column {d["bytes_z"]}, the residual {d["bytes_residual"]}')
bar4 = d['product'] and corr > 0.95
print(f'   {"PASS" if bar4 else "NO  "} bar 4 (a product found, the residual is the price column)')
d4 = detect(x, y, z, extra=price)
print(f'   with price given as a fourth column (post hoc, labelled): rule {d4["rule"]}; reached {d4["reached"]:.2%}; residual spread {d4["spread_residual"]:.2e}; bytes net {d4["bytes_z"]} residual {d4["bytes_residual"]}')
passed += 1
print(f'\n{passed} bars run: ' + ', '.join(f'{n} {"PASS" if ok else "NO"}' for n, ok in (('1', bar1), ('2', bar2), ('3', bar3), ('4', bar4))))
