"""Four computations in the relation language, each asked the way a person would ask it. Run: python demo.py

1. A data-centre sizing block, written once as five relations, asked from four different sides.
2. A two-bit adder, a circuit of AND/OR/NOT as arithmetic, read forward and then in reverse.
3. The Fibonacci ladder: one step, seven times, and the gate collapses it to a point.
4. The gate: claims checked against a ledger by regex and a truth table, with a cap.
"""
import time
from relation import Program

PROGRAM = r'''
# 1. a data centre is a building that turns electricity into computation and heat
#    it = computing load in MW; total = power into the building; gallons_per_mwh = the cooling design
block datacentre(it, pue, hours, price, gallons_per_mwh) -> cost:
    total  = it * pue
    energy = total * hours
    cost   = energy * price
    water  = it * hours * gallons_per_mwh

rule pue: pue = total / it   [Established] "Uptime Institute Global Data Center Survey 2026"
rule evaporative_water: gallons_per_mwh = 750   [Established] "EPRI brief: 2.7 million gallons a day at 150 MW"
rule liquid_water: gallons_per_mwh = 53   [Established] "EPRI brief: 190,000 gallons a day at 150 MW"

# 2. a two-bit adder: a1 a0 + b1 b0 = c s1 s0, every gate an arithmetic relation over 0 and 1
circuit adder(a0, a1, b0, b1) -> s0:
    s0 = a0 + b0 - 2*a0*b0
    c0 = a0 * b0
    t  = a1 + b1 - 2*a1*b1
    s1 = t + c0 - 2*t*c0
    c  = a1*b1 + t*c0 - a1*b1*t*c0

# 3. the Fibonacci ladder: each step closes 61.8 percent of the gap to phi and never arrives on its own
climb phi(x) -> y:
    y = 1 + 1/x
    after 7: collapse

# 4. the gate: a claim passes when it is cited AND every citation is in the ledger
gate claim(text):
    cited   = /\[[\w-]+\]/ in text
    sourced = source(text) in ledger
    pass    = cited * sourced
    after 3: stop
    within 60 tokens: stop

# 5. the AI's own unit is the program's unit: the point that crosses a gate is priced in tokens
rule tokens_per_correct: tpc = tokens / correct   [Measured] "reliability benchmark, gated design on a small local model: 107 tokens per correct answer"
'''

p = Program(PROGRAM)
PHI = (1 + 5 ** 0.5) / 2


def ask(line, **extra):
    t0 = time.perf_counter()
    r = p.run(line) if isinstance(line, str) else line()
    print(f'   {line if isinstance(line, str) else extra["label"]:62s} -> {r!r}   ({(time.perf_counter() - t0) * 1000:.1f} ms)')
    return r


print('1. one block, five relations, asked from four sides')
print('   (100 MW of computing, industry PUE 1.52, a year of hours, 8 cents a kWh = 80 dollars a MWh)')
ask('cost = datacentre?(it = 100, pue = 1.52, hours = 8760, price = 80, gallons_per_mwh = 750)')
ask('it = datacentre?(cost = 106521600, pue = 1.52, hours = 8760, price = 80, gallons_per_mwh = 750)')
ask('pue = datacentre?(cost = 80000000, it = 100, hours = 8760, price = 80, gallons_per_mwh = 750)')
ask('it = datacentre?(water = 1000000, hours = 24, gallons_per_mwh = 750, pue = 1.52, price = 80)')
ask('it = datacentre?(water = 1000000, hours = 24, gallons_per_mwh = 53, pue = 1.52, price = 80)')
ask('pue = datacentre?(it = 0, cost = 1, hours = 8760, price = 80, gallons_per_mwh = 750)')

print('\n2. a circuit read forward, then in reverse')
ask(lambda: p.ask('adder', a0=1, a1=1, b0=1, b1=0), label='adder(3 + 1): forward')
ask(lambda: p.ask('adder', s0=1, s1=1, c=0), label='which inputs give 3 with no carry out?')
ask(lambda: p.ask('adder', s0=0, s1=0, c=1), label='which inputs give 4?')
ask(lambda: p.ask('adder', a0=1, b0=1, s0=1), label='1 + 1 with a low bit of 1?')

print('\n3. the ladder: seven steps, then the gate collapses it')
ladder, point = p.climb('phi', 1)
for k, x in enumerate(ladder, 1):
    gap = abs(float(x) - PHI) / abs(1 - PHI)
    print(f'   step {k}: {str(x):6s} = {float(x):.6f}   gap left {gap * 100:6.2f} percent of the start   (0.382^{k} = {0.382 ** k * 100:5.2f})')
print(f'   collapse -> {point!r}  (phi is {PHI:.6f}; the eighth press would be the next level, not an eighth step)')

print('\n4. the gate over claims, with the ledger from the episode')
ledger = {'iea-energy-ai', 'uptime-2026', 'epri-water', 'lbnl-2024'}
claims = ['Data centres used about 415 TWh in 2024 [iea-energy-ai]',
          'The industry average PUE was 1.52 in 2026 [uptime-2026]',
          'AI already uses half of the world\'s electricity',
          'Chip liquid cooling cuts water about 14 times [epri-water]',
          'Every data centre publishes its water use [made-up-source]']
for c in claims:
    r = p.check('claim', c, ledger)
    print(f'   {"PASS" if r.v["pass"] else "no  "}  {c}')
for _ in range(3): p.check('claim', claims[2], ledger)
print(f'   the third retry of the uncited claim -> {p.check("claim", claims[2], ledger)!r}')

print('\n5. the unit of account is the token, and the rule reads backward')
ask('tpc = tokens_per_correct?(tokens = 3210, correct = 30)')
ask('correct = tokens_per_correct?(tokens = 10000, tpc = 107)')
ask('tokens = tokens_per_correct?(correct = 1000, tpc = 107)')

print('\n6. cells and seams: six orientations, a quarter turn, a join that refuses, a bridge that is declared')
cells = Program('cell c1 = saddle(axis z, hand +)\ncell c2 = turn(c1, about z)\ncell c3 = turn(c2, about z)\ncell c4 = turn(c1, about x)\n'
                'join c1 c3\njoin c1 c2\nbridge c1 c2\njoin c1 c4')
for name, c in cells.cells.items(): print(f'   {name}: axis {c.axis}, hand {c.hand}')
for a, b, verdict in cells.lattice(): print(f'   {a} {b}: {verdict!r}')

print('\n7. blocks joined via a variable: a value crosses a declared seam, neighbours must agree, a missing value is re-derived')
lattice = Program(PROGRAM + '\nblock carbon(total, hours, intensity) -> tonnes:\n    tonnes = total * hours * intensity / 1000\njoin datacentre carbon via total\n')
ask(lambda: lattice.ask_lattice('tonnes', it=100, pue=1.52, hours=8760, price=80, gallons_per_mwh=750, intensity=0.4), label='tonnes of CO2 through the seam (total crosses from datacentre to carbon)')
ask(lambda: lattice.ask_lattice('it', tonnes=532.608, hours=8760, intensity=0.4, pue=1.52, price=80, gallons_per_mwh=750), label='the computing load, re-derived backward through the seam')
ask(lambda: lattice.ask_lattice('tonnes', it=100, hours=8760, price=80, gallons_per_mwh=750, intensity=0.4), label='without pue nothing reaches the seam: refuse')

print('\nledger generated from the rules in the program:')
for name, rel, label, source in p.ledger():
    print(f'   {name:18s} {rel:28s} {label:14s} {source}')
