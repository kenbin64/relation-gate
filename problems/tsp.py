"""The travelling salesman, the relation way.

Specification (the gate): a tour is a list of every city exactly once, back to the start. Its length is the sum
of its edges. It is OPTIMAL when no tour is shorter, and that part cannot be checked by looking at one tour, so
the gate checks it two ways: against every permutation when n is small enough to enumerate (the brute truth),
and against the minimum-spanning-tree bound always (no tour can be shorter than the MST; a tour that is would be
a lie). What the gate cannot prove it says it cannot prove.

Solver (the levels): Held and Karp's fold. Level k holds, for every set of k cities and every last city, the
shortest path through exactly that set ending there. Level k+1 is made from level k only: each point at the
next level is the collapse of a few points at the level below. The final tour is the collapse of the last level.
Exact, in 2^n * n^2 steps instead of n!.
"""
import itertools, math, random, time


def cities(n, seed):
    r = random.Random(seed)
    return [(r.uniform(0, 100), r.uniform(0, 100)) for _ in range(n)]


def dist(a, b): return math.hypot(a[0] - b[0], a[1] - b[1])


def length(pts, tour): return sum(dist(pts[tour[i]], pts[tour[(i + 1) % len(tour)]]) for i in range(len(tour)))


def solve(pts):
    """Held-Karp. Returns the optimal tour starting at city 0."""
    n = len(pts); d = [[dist(a, b) for b in pts] for a in pts]
    table = {(1 << 0, 0): (0.0, None)}                        # level 1: the start city alone
    for k in range(2, n + 1):                                   # each level is built from the one below only
        for subset in itertools.combinations(range(1, n), k - 1):
            mask = 1 | sum(1 << c for c in subset)
            for last in subset:
                prev_mask = mask & ~(1 << last)
                candidates = [0] if k == 2 else [p for p in subset if p != last]
                table[(mask, last)] = min((table[(prev_mask, p)][0] + d[p][last], p) for p in candidates)
    full = (1 << n) - 1
    cost, last = min((table[(full, last)][0] + d[last][0], last) for last in range(1, n))
    tour, mask = [], full                                        # walk the fold back to read the tour
    while last is not None:
        tour.append(last); prev = table[(mask, last)][1]; mask &= ~(1 << last); last = prev
    return tour[::-1], cost


def mst_bound(pts):
    """Prim's tree: the sum of its edges is a floor under every tour."""
    n = len(pts); seen = {0}; total = 0.0
    while len(seen) < n:
        e = min((dist(pts[a], pts[b]), b) for a in seen for b in range(n) if b not in seen)
        total += e[0]; seen.add(e[1])
    return total


def gate(pts, tour, cost):
    n = len(pts)
    if sorted(tour) != list(range(n)): return False, 'not every city exactly once'
    if abs(length(pts, tour) - cost) > 1e-6: return False, 'the stated length is not the length of the tour'
    bound = mst_bound(pts)
    if cost < bound - 1e-9: return False, f'shorter than the spanning-tree bound {bound:.3f}: impossible'
    if n <= 9:
        brute = min(length(pts, [0] + list(p)) for p in itertools.permutations(range(1, n)))
        if abs(brute - cost) > 1e-6: return False, f'brute force finds {brute:.3f}, not {cost:.3f}'
        return True, f'every city once, length {cost:.3f} equals the brute-force minimum over {math.factorial(n - 1):,} tours, above the tree bound {bound:.3f}'
    return True, f'every city once, length {cost:.3f}, above the tree bound {bound:.3f}; optimality rests on the fold (exact by construction), not enumerable at n = {n}'


if __name__ == '__main__':
    for n in (7, 9, 12):
        pts = cities(n, seed=n)
        t0 = time.perf_counter(); tour, cost = solve(pts); ms = (time.perf_counter() - t0) * 1000
        ok, why = gate(pts, tour, cost)
        print(f'n = {n:2d}: {"PASS" if ok else "FAIL"}  tour {tour}  {why}  ({ms:.0f} ms)')
    pts = cities(7, seed=7); tour, cost = solve(pts)
    print('a tampered tour:', gate(pts, tour, cost - 5))
