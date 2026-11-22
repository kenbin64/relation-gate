"""Towers of Hanoi, the relation way.

Specification (the gate): a solution is a list of moves (from, to). It is valid when every move takes the top
disc of one peg and puts it on a peg whose top disc is larger (or empty), and the last state has every disc on
the target peg. The relation `moves = 2^n - 1` is the known minimum; the gate checks it, and read backward it
tells you n from a move count.

Solver (the levels): moving n discs is one point at level n. It blooms into three parts: move n-1 discs aside
(the whole of level n-1, one point), move one disc, move n-1 discs back. Recursion between levels, nothing else.
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from relation import Program

RULES = Program('rule hanoi: moves = 2^n - 1   [Established] "Towers of Hanoi minimum move count"')


def solve(n, source='A', target='C', spare='B'):
    """The whole of level n, as a list of moves. Level n-1 is a point inside it."""
    if n == 0: return []
    return solve(n - 1, source, spare, target) + [(source, target)] + solve(n - 1, spare, target, source)


def gate(n, moves):
    """Replays the moves against the rules. Returns (ok, reason)."""
    pegs = {'A': list(range(n, 0, -1)), 'B': [], 'C': []}     # top of a peg is the end of its list
    for i, (src, dst) in enumerate(moves):
        if not pegs[src]: return False, f'move {i}: peg {src} is empty'
        disc = pegs[src][-1]
        if pegs[dst] and pegs[dst][-1] < disc: return False, f'move {i}: disc {disc} onto smaller disc {pegs[dst][-1]}'
        pegs[dst].append(pegs[src].pop())
    if pegs['C'] != list(range(n, 0, -1)): return False, 'not all discs ended on peg C'
    want = int(RULES.ask('hanoi', 'moves', n=n).v)
    if len(moves) != want: return False, f'{len(moves)} moves; the relation says {want} is the minimum'
    return True, f'{len(moves)} moves, every one legal, all discs on C, count equals 2^{n} - 1'


if __name__ == '__main__':
    for n in (3, 10, 16):
        t0 = time.perf_counter(); moves = solve(n); ok, why = gate(n, moves)
        print(f'n = {n:2d}: {"PASS" if ok else "FAIL"}  {why}  ({(time.perf_counter() - t0) * 1000:.0f} ms)')
    print('the relation read backward: 1,048,575 moves means n =', RULES.ask('hanoi', 'n', moves=1048575))
    bad = solve(3); bad[3] = ('A', 'B')
    print('a tampered solution:', gate(3, bad))
