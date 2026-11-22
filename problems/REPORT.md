# Five problems: results, complexity, and whether a laptop should manage them (2026-11-21)

Machine: a 13th-generation Intel i9 laptop with 32 GB, Python 3.14, no compiled extensions except the established
cube solver. Every number below is from `python problems/run_all.py` and the timing pass after it (I ran both).
"Established" is the textbook complexity of the method used, and whether ours matches it. Big-O is for the SOLVER;
every gate is linear in the size of the answer it checks, which is why the gate is always the cheap part.

| Problem | Measured | Our solver | Established | Match | On a simple laptop |
|---|---|---|---|---|---|
| Towers of Hanoi | n = 16: 65,535 moves, 13 ms; n = 20: 1,048,575 moves, 283 ms | O(2^n) time and output; 2^n − 1 moves exactly | 2^n − 1 is the proven minimum, so no solver can be below O(2^n) when it has to list the moves | yes, at the floor | yes; the limit is listing the moves, not computing them (n = 30 is a billion moves, which is a storage question, not a speed one) |
| Travelling salesman | n = 12: 18 ms; 14: 96 ms; 16: 474 ms; brute-force agreement at 7 and 9 | Held-Karp fold: O(2^n · n^2) time, O(2^n · n) space | Held-Karp (1962) is O(2^n · n^2), still the best exact bound known for the general problem; the problem is NP-hard, no polynomial method is known | yes | yes to about 18 cities in Python, into the 20s in C; the measured growth, about 5x per two cities, is the 2^n · n^2 curve |
| Dining philosophers | naive protocol: deadlock found, 2,624 states, under 100 ms; ordered protocol: 2,240 states, clean; 250 meals on five real threads in 1 ms | explicit-state model check, O(states × transitions); 3^5 · 2^5 = 7,776 states at most | explicit-state model checking is linear in the reachable state space; deadlock freedom of ordered resources is Dijkstra's resource hierarchy (1965) | yes | yes, trivially; the state space for five philosophers fits in a few megabytes |
| Rubik's cube | 8-move scramble solved optimally in 350 ms; full 25-move scramble: 21-move solution from the two-phase solver in 11 ms, verified by our gate | meet in the middle: O(b^(d/2)) a side, b about 13 effective moves, so about 2 · 13^4 = 57,000 cubes for d = 8 | bidirectional search halves the exponent (standard); optimal solving of any scramble is Korf's IDA* with pattern databases (1997), minutes to hours; near-optimal in milliseconds is Kociemba's two-phase algorithm (1992); God's number is 20 (Rokicki et al., 2010) | yes for the method; ours stops at depth 8 by memory choice, the established optimal solvers go all the way | yes; depth 8 is under a second; a full optimal solve needs the pattern-database approach and patience, which a laptop has |
| Enigma | 361 letters, rotors I to III, two plugboard pairs: rotor order, positions and plugboard recovered in 26 s | stage 1: O(orders · 26^3 · L) = 6 · 17,576 · 250 letter-steps, about 26 million; stage 2: O(pairs · 325 · L) per survivor | Gillogly's index-of-coincidence attack (1995) is exactly this two-stage search; the wartime Bombe ran the crib attack at about 20 minutes per rotor order electromechanically | yes | yes; about a million letter-steps a second in plain Python, so five rotors (60 orders) is about four minutes, and ring settings would multiply by 26^2 more, which is where cribs replace brute force |

## What this says

- Every solver here is the textbook method and runs at the textbook rate. Nothing was made faster than its
  established bound, and nothing claims to be. What the relation way adds is not speed; it is that each answer
  arrives with a deterministic check that never trusted the solver, and that the solver is written as levels, so a
  wrong level cannot leak upward unnoticed.
- The gate is always cheaper than the solver, by an exponent: checking a Hanoi solution is linear in the moves,
  checking a tour is linear in the cities, checking a cube solution is linear in the moves, checking an Enigma key
  is linear in the letters. That asymmetry is why "do not read the code, test it" works at all.
- The one place the gate cannot be cheap is proving optimality of a tour at large n: it falls back to a bound (the
  spanning tree) and to the construction of the fold, and says so in its own verdict.
- A simple laptop would have done all five, slower by the ratio of its cores to this one's, roughly three to five
  times: Enigma in a couple of minutes, everything else in seconds.
