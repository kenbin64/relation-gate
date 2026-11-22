"""The dining philosophers, the relation way.

Specification (the gate): five philosophers, five forks, each fork between two neighbours. A protocol is correct
when (1) no fork is ever held by two philosophers at once, (2) no reachable state is a deadlock (somebody can
always move), and (3) nobody starves (every philosopher eats, in every fair run). These are relations over
STATES, so the gate is a model check: enumerate every reachable state of the protocol and test the relations
on all of them. Nothing is sampled; the whole state space is the level, and the verdict is its collapse.

Solver: the ordered-forks protocol (Dijkstra's resource hierarchy): every philosopher picks up the lower-numbered
of their two forks first. The naive protocol (left fork first) is run through the same gate to show that the gate
catches its deadlock. Then the ordered protocol runs on real threads to show it finishing.
"""
import threading, time
from collections import deque

N = 5


def naive(me): return (me, (me + 1) % N)                       # left fork first, then right


def ordered(me): return tuple(sorted((me, (me + 1) % N)))      # lower-numbered fork first


def moves(state, protocol):
    """Every state one step away. A state is (holding[i] = 0, 1 or 2 forks, eaten[i] = times eaten)."""
    holding, eaten = state
    for me in range(N):
        first, second = protocol(me)
        taken = {f for j in range(N) for f in protocol(j)[:holding[j]]}
        h = list(holding); e = list(eaten)
        if holding[me] == 0 and first not in taken: h[me] = 1; yield (tuple(h), tuple(e))
        elif holding[me] == 1 and second not in taken: h[me] = 2; yield (tuple(h), tuple(e))
        elif holding[me] == 2: h[me] = 0; e[me] = min(eaten[me] + 1, 1); yield (tuple(h), tuple(e))


def gate(protocol):
    """Model check: explore every reachable state; test the three relations on every one."""
    start = ((0,) * N, (0,) * N)
    seen = {start}; queue = deque([start]); deadlocks = []
    while queue:
        s = queue.popleft()
        holding = s[0]
        held = [f for j in range(N) for f in protocol(j)[:holding[j]]]
        if len(held) != len(set(held)): return False, f'a fork held twice in state {s}', len(seen)
        nxt = list(moves(s, protocol))
        if not nxt: deadlocks.append(s)
        for t in nxt:
            if t not in seen: seen.add(t); queue.append(t)
    if deadlocks: return False, f'deadlock reachable: {deadlocks[0][0]} (each holds one fork, nobody can move); {len(seen)} states explored', len(seen)
    fed = any(all(s[1]) for s in seen)
    if not fed: return False, 'no reachable state in which everyone has eaten', len(seen)
    return True, f'{len(seen)} reachable states: no double-held fork, no deadlock, a state where all five have eaten is reachable', len(seen)


def run_threads(rounds=50):
    """The ordered protocol on real threads: proof by finishing, with a count of meals."""
    forks = [threading.Lock() for _ in range(N)]; meals = [0] * N
    def dine(me):
        a, b = ordered(me)
        for _ in range(rounds):
            with forks[a]:
                with forks[b]:
                    meals[me] += 1
    threads = [threading.Thread(target=dine, args=(i,)) for i in range(N)]
    t0 = time.perf_counter()
    for t in threads: t.start()
    for t in threads: t.join(timeout=30)
    alive = [t.is_alive() for t in threads]
    return meals, any(alive), (time.perf_counter() - t0) * 1000


if __name__ == '__main__':
    for name, protocol in (('naive, left fork first', naive), ('ordered, lower-numbered fork first', ordered)):
        ok, why, states = gate(protocol)
        print(f'{name:36s} {"PASS" if ok else "FAIL"}  {why}')
    meals, stuck, ms = run_threads()
    print(f'ordered protocol on five real threads: {"stuck" if stuck else "finished"}, meals {meals} in {ms:.0f} ms')
