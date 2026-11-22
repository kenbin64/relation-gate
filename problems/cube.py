"""Rubik's cube, the relation way.

Specification (the gate): a cube is 8 corner cubies and 12 edge cubies, each in a position with an orientation.
A solution is a move sequence; it is valid when applying it to the scrambled cube gives the solved cube. That
check is exact and cheap, so ANY solver's output can be verified without trusting the solver: ours, or an
established one. The model is Kociemba's cubie model (the standard one); its own identities are checked first
(four turns of a face is the identity; R U R' U' has order 6), and a wrong wiring fails those before anything
else runs. The first version of this file wired the facelets by hand and that check caught it.

Solver (the levels): meet in the middle. Level k is the set of every cube k moves from the scramble; the solved
side builds the same levels from the other end. Each level is made from the one below only, and the first cube
the two sides share collapses the search to one answer, the SHORTEST one. Four levels a side reaches scrambles
of eight moves. For a full random scramble the established two-phase solver (kociemba) is called and OUR gate
checks its answer: the solver may be anyone's, the gate is not.
"""
import random, time
from collections import deque

# Cubie model (Kociemba). Corners URF, UFL, ULB, UBR, DFR, DLF, DBL, DRB; edges UR, UF, UL, UB, DR, DF, DL, DB, FR, FL, BL, BR.
# A move is (cp, co, ep, eo): cp[i] is the corner now at position i, co[i] its twist; the same for edges with flips.
BASIC = {
    'U': ([3, 0, 1, 2, 4, 5, 6, 7], [0] * 8, [3, 0, 1, 2, 4, 5, 6, 7, 8, 9, 10, 11], [0] * 12),
    'R': ([4, 1, 2, 0, 7, 5, 6, 3], [2, 0, 0, 1, 1, 0, 0, 2], [8, 1, 2, 3, 11, 5, 6, 7, 4, 9, 10, 0], [0] * 12),
    'F': ([1, 5, 2, 3, 0, 4, 6, 7], [1, 2, 0, 0, 2, 1, 0, 0], [0, 9, 2, 3, 4, 8, 6, 7, 1, 5, 10, 11], [0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0]),
    'D': ([0, 1, 2, 3, 5, 6, 7, 4], [0] * 8, [0, 1, 2, 3, 5, 6, 7, 4, 8, 9, 10, 11], [0] * 12),
    'L': ([0, 2, 6, 3, 4, 1, 5, 7], [0, 1, 2, 0, 0, 2, 1, 0], [0, 1, 10, 3, 4, 5, 9, 7, 8, 2, 6, 11], [0] * 12),
    'B': ([0, 1, 3, 7, 4, 5, 2, 6], [0, 0, 1, 2, 0, 0, 2, 1], [0, 1, 2, 11, 4, 5, 6, 10, 8, 9, 3, 7], [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1]),
}
SOLVED = (tuple(range(8)), (0,) * 8, tuple(range(12)), (0,) * 12)


def compose(state, move):
    cp, co, ep, eo = state; mcp, mco, mep, meo = move
    return (tuple(cp[mcp[i]] for i in range(8)), tuple((co[mcp[i]] + mco[i]) % 3 for i in range(8)),
            tuple(ep[mep[i]] for i in range(12)), tuple((eo[mep[i]] + meo[i]) % 2 for i in range(12)))


MOVES = {}
for f, m in BASIC.items():
    MOVES[f] = m
    MOVES[f + '2'] = compose(m, m)
    MOVES[f + "'"] = compose(compose(m, m), m)


def apply(state, sequence):
    for m in sequence.split(): state = compose(state, MOVES[m])
    return state


# Facelets, for the gate's second opinion and for the established solver: U 0-8, R 9-17, F 18-26, D 27-35, L 36-44, B 45-53.
U, R, F, D, L, B = (i * 9 for i in range(6))
CORNER_FACELET = [[U + 8, R + 0, F + 2], [U + 6, F + 0, L + 2], [U + 0, L + 0, B + 2], [U + 2, B + 0, R + 2],
                  [D + 2, F + 8, R + 6], [D + 0, L + 8, F + 6], [D + 6, B + 8, L + 6], [D + 8, R + 8, B + 6]]
EDGE_FACELET = [[U + 5, R + 1], [U + 7, F + 1], [U + 3, L + 1], [U + 1, B + 1], [D + 5, R + 7], [D + 1, F + 7],
                [D + 3, L + 7], [D + 7, B + 7], [F + 5, R + 3], [F + 3, L + 5], [B + 5, L + 3], [B + 3, R + 5]]
CORNER_COLOR = ['URF', 'UFL', 'ULB', 'UBR', 'DFR', 'DLF', 'DBL', 'DRB']
EDGE_COLOR = ['UR', 'UF', 'UL', 'UB', 'DR', 'DF', 'DL', 'DB', 'FR', 'FL', 'BL', 'BR']


def facelets(state):
    cp, co, ep, eo = state; out = [None] * 54
    for face in range(6): out[face * 9 + 4] = 'URFDLB'[face]
    for i in range(8):
        for k in range(3): out[CORNER_FACELET[i][(k + co[i]) % 3]] = CORNER_COLOR[cp[i]][k]
    for i in range(12):
        for k in range(2): out[EDGE_FACELET[i][(k + eo[i]) % 2]] = EDGE_COLOR[ep[i]][k]
    return ''.join(out)


def gate(scramble_state, solution):
    """Does the solution solve this cube? Exact: apply it and compare, in both the cubie and the facelet form."""
    try:
        end = apply(scramble_state, solution)
    except KeyError as e:
        return False, f'unknown move {e}'
    if end != SOLVED or facelets(end) != facelets(SOLVED): return False, f'{len(solution.split())} moves do not reach the solved cube'
    return True, f'{len(solution.split())} moves reach the solved cube'


def inverse(sequence):
    inv = {'': "'", "'": '', '2': '2'}
    return ' '.join(m[0] + inv[m[1:]] for m in reversed(sequence.split()))


def solve_meet(state, depth=4):
    """Meet in the middle, level by level from both ends; the first shared cube gives the shortest solution."""
    if state == SOLVED: return ''
    front = {state: ''}; back = {SOLVED: ''}; fq = deque([state]); bq = deque([SOLVED])
    for _ in range(depth):
        for side, queue, other in ((front, fq, back), (back, bq, front)):
            for _ in range(len(queue)):
                s = queue.popleft(); path = side[s]
                last = path.split()[-1][0] if path else None
                for m, mv in MOVES.items():
                    if m[0] == last: continue                      # the same face twice is never shortest
                    t = compose(s, mv)
                    if t in side: continue
                    side[t] = path + ' ' + m if path else m; queue.append(t)
                    if t in other:
                        return (front[t] + ' ' + inverse(back[t])).strip()
    return None


def scramble(n, seed):
    r = random.Random(seed); seq = []; last = None
    while len(seq) < n:
        m = r.choice(list(MOVES))
        if m[0] == last: continue
        seq.append(m); last = m[0]
    return ' '.join(seq)


def sanity():
    for f in BASIC:
        assert apply(SOLVED, f'{f} {f} {f} {f}') == SOLVED, f'{f} four times is not the identity'
        assert apply(SOLVED, f"{f} {f}'") == SOLVED
    assert apply(SOLVED, ' '.join(["R U R' U'"] * 6)) == SOLVED, "R U R' U' six times is not the identity"
    assert apply(SOLVED, ' '.join(['R2 U2'] * 6)) == SOLVED, '(R2 U2)^6 is not the identity'
    assert facelets(SOLVED) == ''.join(c * 9 for c in 'URFDLB')
    s = facelets(apply(SOLVED, scramble(30, 1)))
    assert all(s.count(c) == 9 for c in 'URFDLB')


if __name__ == '__main__':
    sanity(); print("cube model: four turns is the identity, R U R' U' has order 6, (R2 U2)^6 is the identity, nine facelets a colour")
    for n in (3, 5, 7, 8):
        sc = scramble(n, seed=n); state = apply(SOLVED, sc)
        t0 = time.perf_counter(); sol = solve_meet(state, depth=4); ms = (time.perf_counter() - t0) * 1000
        ok, why = gate(state, sol) if sol else (False, 'not found within four levels a side')
        print(f'scramble of {n}: {sc:28s} -> {sol!s:28s} {"PASS" if ok else "FAIL"} {why} ({ms:.0f} ms)')
    try:
        import kociemba
        sc = scramble(25, seed=42); state = apply(SOLVED, sc)
        t0 = time.perf_counter(); sol = kociemba.solve(facelets(state)); ms = (time.perf_counter() - t0) * 1000
        ok, why = gate(state, sol)
        print(f'scramble of 25 (full): established two-phase solver -> {len(sol.split())} moves; our gate: {"PASS" if ok else "FAIL"} {why} ({ms:.0f} ms)')
        print('a tampered solution:', gate(state, sol + ' U'))
    except ImportError:
        print('kociemba not installed: full scrambles not solved here (the gate still verifies any solution given)')
