# The relation language (prototype)

A small language where every line is a relation, never an assignment. `a = w * h` binds three names, and the
block holding it can be asked for any one of them: forward is the seed, backward is the bloom. Logic is
arithmetic over 0 and 1 (`*` is AND, `x + y - x*y` is OR, `1 - x` is NOT). The edges are values, not errors:
dividing by zero gives `refuse`, inverting a square gives `fork`, and a fork only becomes a value through an
explicit `decide`. Every loop is capped (`after n`), and every `rule` must carry a label and a source or it
does not parse.

It is the checker's language and the specification's language, not a language for a model to write in. The
pieces are old and solid (algebra read for any unknown, logic as arithmetic circuits, regex as a finite
automaton, a debugger's step-over with a count); the composition is the proposal, and the benchmark below is
the first number on it.

## For AI-assisted programming: the directive, the API, the readable view

- **DIRECTIVE.md** is the text to hand an AI assistant (paste into CLAUDE.md or a system prompt): seven rules for
  writing in relations with sources, what to produce for a task, and what the checker will do with it.
- **api.py** exposes the language to any tool: `check` (the gate), `bloom` and `fold` (terse form to readable
  lines and back, exact), `ask` (read a relation for any unknown), `ledger` (the rules with labels and sources),
  as Python functions and as a local HTTP service (`python api.py`, port 8767; GET /directive returns the directive).
- **render.py** is the readable view. The model writes the dense form, `{"date": ["2026-03-03", "March 3, 2026"]}`;
  the renderer shows `date = 2026-03-03 from "March 3, 2026"` and folds it back without losing a character
  (tested on 2,000 awkward cases: quotes, backslashes, control characters, non-ASCII, padding).

## Run it

    python tests/test_relation.py      19 checks: every example in the draft plus the four stability invariants
    python demo.py                     four computations asked the way a person would ask them

Needs Python 3 and sympy (`pip install sympy`). Solving is done by sympy; regex by `re`; circuits over 0/1 by
enumeration (fine to a dozen or so free inputs).

## The four statements

    rule name: lhs = rhs [Label] "source"      one relation with its label and source (both required)
    block name(params) -> out:                 a level: relations that collapse to one point; ask with name?(...)
    circuit name(params) -> out:               a block over facts (0/1); reads backward by enumeration
    climb name(x) -> y:                        one step, repeated at most n times, then collapsed
        y = <expression in x>
        after n: collapse
    gate name(text):                           a truth table over facts pulled from text, with a cap
        fact = /regex/ in text
        fact = source(text) in ledger
        pass = <0/1 arithmetic over the facts>
        after n: stop

Queries as text: `w = area?(a = 12, h = 3)` or `y = square?(z = 9) decide y >= 0`.

## The unit of account is the token

The AI's own unit is the program's unit. Every gate result carries `tokens` (the text it read, estimated at
four characters per token, stated as an estimate) and `spent` (the running total on the same key). A gate can
be capped by tries (`after 3: stop`) or by budget (`within 60 tokens: stop`). The measure of the whole stack
is a relation like any other, `tpc = tokens / correct`, and it reads backward: a budget gives the number of
correct answers it buys.

## Test the tests (what TestThisPuppy does for Java, done here for Python)

    python tests/mutate.py             plants one bug at a time in relation.py and runs the tests against each

TestThisPuppy has no Python engine yet and mutmut does not run natively on Windows, so `tests/mutate.py` is a
small deterministic mutation runner (operator swaps, comparison swaps, constant changes, dropped returns,
and/or swaps). Result on 2026-11-21, identical on repeated runs: 137 bugs planted, 126 caught (91 percent).
The eleven survivors were audited by hand: ten are equivalent mutants (a `maxsplit` or `strict=` that cannot
change behaviour, a sort key offset, a default that is never reached, a `return None` that was already None)
and one is a branch algebra cannot be made to reach (a solved value that is itself infinite). The first run
scored 76 percent; the gaps it showed became 18 new tests and two real bug fixes (`decide y != 0` evaluated
to a plain True instead of a comparison; fork values came back in hash order, so the same question could
print its two answers in either order).

One lesson for anyone writing a mutation runner: the first versions of this one reported 94 to 96 percent,
and which equivalent mutants "died" changed between runs. The cause was Python's bytecode cache: a mutant
written within the same second as the last one, with the same file size, ran the previous mutant's compiled
code. The runner now passes `-B` and `PYTHONDONTWRITEBYTECODE`, and pins `PYTHONHASHSEED`, and the result is
the same every time. The inflated scores were the tool's bug, not the tests' strength.

Code check: `python -m ruff check relation.py demo.py tests/*.py --select F,B,E7,E9,PL --ignore E701,E702,PLR0911,PLW0603,PLR2004 --line-length 120`
is clean; the remaining style findings are one-statement-per-line. Security scan (bandit): two false
positives, the dictionary key named `pass` read as a password.

## Stability invariants (tested)

1. Forward then backward returns the input exactly (200 random seeds).
2. A refusal never becomes a number downstream.
3. A fork never collapses without a decide.
4. Every cap halts in at most n steps.

## Measured on a benchmark

`gate-server.py <program.gate>` serves a gate program over stdin and stdout so a runner in another language can
call it hundreds of times. Four more fact kinds exist for checking a model's answer against the task it was
given: `json(text)`, `keys(text) = a, b`, `numbers(text) in input`, `strings(text) in input`.

The benchmark is in `benchmark/`: the tasks, the held-out generator, the prompt forms, the graders (fixed
rules, never a model), the gate program, the runner, the report and the raw results, so every number below can
be re-run with `node benchmark/run.js llama3.2:3b` and read with `python benchmark/report.py`. Write-up with the
bars that were fixed before the run: `benchmark/RESULTS-RELATION.md`. With llama3.2:3b on the held-out tasks: the agent pipeline where a model checks a model let through 68.3 percent
wrong answers at 2,749 tokens per correct answer; the same worker with the gate program `tasks.gate` as the
checker let through 4.2 percent wrong at 607 tokens per correct answer, abstaining on 46.7 percent. Bars were
written before the run. The ten wrong answers the gate let through were sentiment misjudgments, arithmetic in
the right shape, and a capitalised title: judgment and computation, which a shape-and-source gate does not see.

## Five classic problems, the same way (`problems/`)

`python problems/run_all.py` runs them all. Each file has the same three parts: a specification written as the
relations a valid answer must satisfy, a deterministic gate that checks any proposed answer against them, and
a solver that works in levels (iterate inside a level, collapse to one point between levels). Nothing is
printed as solved until its gate has passed it, and every file also feeds its gate a tampered answer to show
the gate refusing.

| Problem | Gate | Solver | Result (I ran it, 2026-11-21) |
|---|---|---|---|
| Towers of Hanoi | every move legal, all discs on the target, count = 2^n − 1 (a relation, also read backward) | recursion between levels | n = 16, 65,535 moves, 29 ms |
| Travelling salesman | every city once, stated length true, above the spanning-tree bound, equal to brute force when n ≤ 9 | Held-Karp fold: level k+1 from level k only | 12 cities exact in 16 ms; brute-force agreement at 7 and 9 |
| Dining philosophers | model check of every reachable state: no fork held twice, no deadlock, everyone fed | ordered forks (Dijkstra) | naive protocol: deadlock found at 2,624 states; ordered: clean over 2,240, and 250 meals on real threads |
| Rubik's cube | apply the moves to the cubie model and to the facelets, compare with solved | meet in the middle, level by level, shortest answer; full scrambles by the established two-phase solver, checked by our gate | 8-move scramble solved optimally in 356 ms; 25-move scramble: 21-move solution verified |
| Enigma | decrypt with the recovered key equals the plaintext | index of coincidence over rotor order and positions, then the plugboard pair by pair (Gillogly's method) | 361 letters, rotors I to III, two plugboard pairs: key and plugboard recovered in 25 s |

Honest scope, in the files: the cube's own meet-in-the-middle reaches eight-move scrambles; Enigma is the
statistical attack with rotors I to III, ring settings at A and a short plugboard; the salesman is exact to
about 15 cities by the fold, not beyond. The first cube model, wired by hand, was caught by its own identity
checks (R U R' U' must have order 6) and replaced with the standard cubie model.

## Not built yet

Cells (`saddle`, `turn`, `join`, `bridge`), rules referenced by name inside blocks, and the benchmark run that
would decide whether a `gate` written here beats a prompt-only gate on tokens per correct answer.
