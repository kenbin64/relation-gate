"""Tests for the relation language. Run: python tests/test_relation.py   (no framework, plain asserts, TestThisPuppy style)

Every example in the draft is a test with its expected output, plus the four stability invariants:
  1. forward then backward returns the input exactly;
  2. a refusal never becomes a number downstream;
  3. a fork never collapses without a decide;
  4. every cap halts in at most n steps.
"""
import os
import random
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from relation import Fork, Program, Refuse, Value

PROGRAM = '''
rule and: z = x * y                [Established] "Boolean algebra"
rule pue: pue = total / it         [Established] "Uptime Institute, 2026"

block area(w, h) -> a:
    a = w * h

block square(y) -> z:
    z = y ^ 2

circuit half_adder(a, b) -> s:
    s = a + b - 2*a*b
    c = a * b

climb phi(x) -> y:
    y = 1 + 1/x
    after 7: collapse

gate answer(claim):
    cited   = /\\[[\\w-]+\\]/ in claim
    sourced = source(claim) in ledger
    pass = cited * sourced
    after 3: stop
'''
p = Program(PROGRAM)
passed = 0

def check(name, got, want):
    global passed
    assert repr(got) == want, f'{name}: got {got!r}, wanted {want}'
    passed += 1; print(f'  ok  {name}: {got!r}')

print('reading a block from any side')
check('seed', p.run('a = area?(w = 3, h = 4)'), '12')
check('bloom', p.run('w = area?(a = 12, h = 3)'), '4')
check('pole', p.run('h = area?(a = 12, w = 0)'), 'refuse: pole: a relation in area has no value at these inputs')
check('underdetermined', p.run('w = area?(a = 12)'), 'refuse: underdetermined: give more of h, w')
check('rule as a block', p.run('it = pue?(pue = 1.52, total = 152)'), '100.000000000000')

print('forks are decided, never guessed')
check('fork', p.run('y = square?(z = 9)'), 'fork {-3, 3}')
check('decided', p.run('y = square?(z = 9) decide y >= 0'), '3')
check('decided to nothing', p.run('y = square?(z = 9) decide y > 5'), 'refuse: the decision rule kept nothing')

print('circuits read backward')
check('forward', p.ask('half_adder', a=1, b=1), "{'a': 1, 'b': 1, 'c': 1, 's': 0}")
check('backward', p.ask('half_adder', s=1), "fork {{'a': 0, 'b': 1, 'c': 0, 's': 1}, {'a': 1, 'b': 0, 'c': 0, 's': 1}}")
check('impossible', p.ask('half_adder', s=1, c=1), 'refuse: no 0/1 assignment satisfies half_adder')

print('the ladder and the gate')
ladder, point = p.climb('phi', 1)
assert len(ladder) == 6, 'a cap of seven is six levels and a resolution'
check('collapse', point, '21/13')
g = p.check('answer', 'Data centres used 415 TWh in 2024 [iea]', ledger={'iea'})
check('gate pass', g, "{'pass': 1, 'cited': 1, 'sourced': 1, 'tokens': 10, 'spent': 10}")
for _ in range(3):
    r = p.check('answer', 'AI uses half the world\'s power', ledger={'iea'})
    assert r.v['pass'] == 0
check('gate stops', p.check('answer', 'AI uses half the world\'s power', ledger={'iea'}), 'refuse: stopped after 3 tries, 24 tokens spent')

print('the edges the first mutation run found untested')
check('given, not asked', p.run('a = area?(a = 12, h = 3)'), 'refuse: a was given, not asked')
check('vanishing pole', p.run('w = area?(a = 0, h = 0)'), 'refuse: pole: w vanishes at these inputs (a, h multiplies it away)')
q = Program('climb inv(x) -> y:\n    y = 1 / x\n    after 3: collapse')
ladder, r = q.climb('inv', 0)
check('pole on the ladder', r, 'refuse: pole reached on the ladder')
assert ladder == [], 'nothing is kept past a pole'
q = Program('climb c(x) -> y:\n    y = x + 1\ngate g(t):\n    f = /x/ in t\n    pass = f')
assert q.climbs['c'].cap == 7 and q.gates['g'].cap == 3, 'default caps are seven steps and three tries'
passed += 1; print('  ok  default caps: climb 7, gate 3')
g = p.check('answer', 'Every data centre publishes its water use [made-up]', ledger={'iea'})
check('cited but not in the ledger', g, "{'pass': 0, 'cited': 1, 'sourced': 0, 'tries': 1, 'tokens': 13, 'spent': 13}")
g = p.check('answer', 'no citation at all', ledger={'iea'})
check('neither cited nor sourced', g, "{'pass': 0, 'cited': 0, 'sourced': 0, 'tries': 1, 'tokens': 5, 'spent': 5}")
g = p.check('answer', 'another uncited claim', ledger={'iea'})
assert g.v['tries'] == 1, 'each claim has its own count'
passed += 1; print('  ok  each claim keeps its own count of tries')
check('ledger from the rules', p.ledger(), "[('and', 'z = x * y', '[Established]', 'Boolean algebra'), ('pue', 'pue = total / it', '[Established]', 'Uptime Institute, 2026')]")
changed = True
try:
    Value(1).v = 2
except Exception:
    changed = False
assert not changed, 'a value was changed after it was made'
passed += 1; print('  ok  values cannot be changed once made')
q = Program('block one(w) -> a:\n a = w * 2')
check('one-space indent', q.run('a = one?(w = 5)'), '10')
check('asked for a name the block does not have', p.run('q = area?(a = 12, h = 3)'), 'refuse: q does not appear in area')
check('a decide that keeps two is still a fork', p.run('y = square?(z = 9) decide y != 0'), 'fork {-3, 3}')
for frozen, attr in ((Fork((1, 2)), 'values'), (Refuse('x'), 'reason')):
    changed = True
    try:
        setattr(frozen, attr, None)
    except Exception:
        changed = False
    assert not changed, 'a fork or refusal was changed after it was made'
passed += 1; print('  ok  forks and refusals are as fixed as values')
q = Program('gate once(t):\n    f = /x/ in t\n    pass = f\n    after 1: stop')
assert q.check('once', 'no').v['tries'] == 1, 'the first try is evaluated'
check('a cap of one stops on the second try', q.check('once', 'no'), 'refuse: stopped after 1 tries, 1 tokens spent')
q = Program('gate thrifty(t):\n    f = /x/ in t\n    pass = f\n    within 12 tokens: stop')
assert q.check('thrifty', 'eight ch', key='k').v['spent'] == 2, 'tokens are counted at four characters each'
check('a token budget stops before it is passed', q.check('thrifty', 'this is more than forty characters of text, surely', key='k'), 'refuse: stopped: 15 tokens would pass the budget of 12')
assert q.check('thrifty', 'exactly forty-eight characters are in this line.', key='fresh').v['spent'] == 12, 'a text that lands exactly on the budget is read'
from relation import tokens
assert [tokens(t) for t in ('', 'x', 'abcd', 'abcde', 'abcdefg')] == [0, 1, 1, 2, 2], 'tokens round up at four characters each'
passed += 1; print('  ok  token estimate rounds up: 0, 1, 1, 2, 2')
check('a first text over the budget is refused with its own count', q.check('thrifty', 'this is more than forty characters of text, surely', key='new'), 'refuse: stopped: 13 tokens would pass the budget of 12')
q = Program('block tr(x) -> z:\n    z = x + sin(x)')
check('a relation algebra cannot invert is a refusal, not a guess', q.ask('tr', 'x', z=2), 'refuse: cannot solve tr: could not solve -x - sin(x) + 2')

print('the task facts: json shape, keys, numbers and strings sourced from the input')
q = Program('gate extract(text):\n    shape = json(text)\n    fields = keys(text) = date, amount\n    sourced = numbers(text) in input\n    pass = shape * fields * sourced\n'
            'gate note(text):\n    shape = json(text)\n    fields = keys(text) = title, priority, tags\n    sourced = strings(text) in input\n    pass = shape * fields * sourced')
line = 'Paid on March 3, 2026: annual licence renewal, $240.00, ref LX-88.'
r = q.check('extract', '{"date": "2026-03-03", "amount": 240}', input=line, key='a').v
assert r == {'pass': 1, 'shape': 1, 'fields': 1, 'sourced': 1, 'tokens': 10, 'spent': 10}, r
r = q.check('extract', '{"date": "2026-03-03", "amount": 240}', input='Paid $240.00 on 2026-03-03.', key='a2').v
assert r['pass'] == 1 and r['sourced'] == 1, 'an answer whose numbers are exactly the input\'s numbers is sourced'
r = q.check('note', '{"title": "Fix the gallery signature", "priority": 2, "tags": ["art", "urgent"]}', input='Fix the gallery signature. Priority 2. Tags: art, urgent.', key='n1').v
assert r == {'pass': 1, 'shape': 1, 'fields': 1, 'sourced': 1, 'tokens': 20, 'spent': 20}, r
q2 = Program('gate when(text):\n    when = dates(text) in input\n    pass = when')
assert q2.check('when', '2026-03-03', input='March 3, 2026', key='w').v == {'pass': 1, 'when': 1, 'tokens': 3, 'spent': 3}
assert q.check('extract', '```json\n{"date": "2026-03-03", "amount": 240}\n```', input=line, key='b').v['pass'] == 1, 'a code fence is allowed'
r = q.check('extract', '{"date": "2026-03-03", "amount": 2400}', input=line, key='c').v
assert r['pass'] == 0 and r['sourced'] == 0, 'an amount not in the input fails the source fact'
r = q.check('extract', '{"date": "2026-03-03", "amount": 240, "ref": "LX-88"}', input=line, key='d').v
assert r['pass'] == 0 and r['fields'] == 0, 'an extra key fails the keys fact'
r = q.check('extract', 'The date is 2026-03-03 and the amount is 240.', input=line, key='e').v
assert r['pass'] == 0 and r['shape'] == 0, 'prose is not a JSON object'
note = 'Fix the gallery signature. Priority 2. Tags: art, urgent.'
assert q.check('note', '{"title": "Fix the gallery signature", "priority": 2, "tags": ["art", "urgent"]}', input=note, key='f').v['pass'] == 1
r = q.check('note', '{"title": "Fix the gallery", "priority": 2, "tags": ["art", "urgent", "framing"]}', input=note, key='g').v
assert r['pass'] == 0 and r['sourced'] == 0, 'a tag the note never mentioned fails the strings fact'
r = q.check('note', '{"title": "Fix the Gallery Signature", "priority": 2, "tags": ["art", "urgent"]}', input=note, key='h').v
assert r['pass'] == 0 and r['sourced'] == 0, 'the strings fact is exact, case included'
passed += 1; print('  ok  json, keys, numbers-in-input and strings-in-input facts')
from relation import dates_in, numbers_in
assert numbers_in('Invoice 4471 dated 2026-03-14, total $1,284.50.') == {4471.0, 1284.5}, numbers_in('Invoice 4471 dated 2026-03-14, total $1,284.50.')
assert numbers_in('{"date": "2026-01-07", "amount": 12400.00}') == {12400.0}
passed += 1; print('  ok  numbers are read as values: 1,284.50 is 1284.5; an ISO date is left to the date fact')
for text, want in (('On 7 January 2026 we billed $12,400.00', {'2026-01-07'}), ('Paid on March 3, 2026', {'2026-03-03'}), ('Mar 3, 2026', {'2026-03-03'}),
                   ('03/14/2026', {'2026-03-14'}), ('2026/03/14 and 2025-11-30', {'2026-03-14', '2025-11-30'}), ('no date here, 12 items', set())):
    assert dates_in(text) == want, (text, dates_in(text))
passed += 1; print('  ok  dates are read in six written forms')
q = Program('gate extract(text):\n    when = dates(text) in input\n    sourced = numbers(text) in input\n    pass = when * sourced')
r = q.check('extract', '{"date": "2026-01-07", "amount": 12400.00}', input='On 7 January 2026 we billed $12,400.00 for roof replacement (job 31).', key='a').v
assert r['pass'] == 1, r
r = q.check('extract', '{"date": "2026-01-08", "amount": 12400.00}', input='On 7 January 2026 we billed $12,400.00 for roof replacement (job 31).', key='b').v
assert r['pass'] == 0 and r['when'] == 0, r
passed += 1; print('  ok  a worded date in the input sources an ISO date in the answer; a wrong day is refused')

print('cells: six orientations, turns, seams')
from relation import turned
seen = set()
for axis in 'xyz':
    for hand in '+-':
        seen.add((axis, hand))
        assert turned(axis, hand, axis) == (axis, '-' if hand == '+' else '+'), 'a quarter turn about the cell\'s own axis flips the hand'
        a, h = axis, hand
        for _ in range(4): a, h = turned(a, h, 'x')
        assert (a, h) == (axis, hand), 'four quarter turns is the identity'
        assert turned(axis, hand, 'x')[0] != axis or axis == 'x', 'a turn about another axis changes which axis the saddle bridges'
orbit, frontier = {('z', '+')}, [('z', '+')]              # every orientation reachable from one saddle by quarter turns
while frontier:
    a, h = frontier.pop()
    for about in 'xyz':
        t = turned(a, h, about)
        if t not in orbit: orbit.add(t); frontier.append(t)
assert orbit == seen, orbit
passed += 1; print('  ok  the six orientations are the whole orbit; own-axis turns flip the hand; four turns is the identity')
q = Program('cell c1 = saddle(axis z, hand +)\ncell c2 = turn(c1, about z)\ncell c3 = turn(c2, about z)\ncell c4 = saddle(axis z, hand +)\n'
            'join c1 c3\njoin c1 c2\nbridge c1 c4\nbridge c3 c2')
check('matching hands join', q.seam('c1', 'c3'), 'joined: both z+, the surface is continuous across the face')
check('a quarter turn breaks the join', q.seam('c1', 'c2'), 'refuse: c1 (z+) and c2 (z-) do not match across the face; turn one, or bridge on purpose')
check('a bridge of matching hands is refused', q.seam('c1', 'c4'), 'refuse: bridge c1 c4: the hands already match (z+); a bridge is for a mismatch')
check('a declared bridge', q.seam('c3', 'c2'), 'bridged: c3 is z+, c2 is z-; the crossover is declared')
check('not joined', q.seam('c2', 'c4'), 'refuse: c2 and c4 are not joined')
assert len(q.lattice()) == 4
assert q.cells['c1'].name == 'c1' and q.cells['c2'].name == 'c2' and q.cells['c4'].axis == 'z' and q.cells['c4'].hand == '+'
passed += 1; print('  ok  the lattice reports every seam')
q = Program('cell c1 = saddle(axis x, hand -)\nblock b(x) -> y:\n    y = x + 1\njoin c1 b via x\njoin c1 c1')
assert [(a, b) for a, b, _ in q.lattice()] == [('c1', 'c1')], 'a join that names a block is not a seam between cells'
passed += 1; print('  ok  only joins between two cells are seams')

print('rules by name inside blocks, and blocks joined via a variable')
q = Program('rule pue: pue = total / it   [Established] "Uptime Institute, 2026"\n'
            'block building(it) -> total:\n    use pue\n'
            'block bill(total, hours, price) -> cost:\n    cost = total * hours * price\n'
            'join building bill via total\n'
            'block water(it) -> gallons:\n    gallons = it * hours * per_mwh\n')
check('a rule used by name', q.run('total = building?(it = 100, pue = 1.52)'), '152.000000000000')
check('a value crosses a join', q.ask_lattice('cost', it=100, pue=1.52, hours=8760, price=80), '106521600.000000')
check('no join, no crossing', q.ask_lattice('gallons', it=100, pue=1.52, hours=24, per_mwh=750), '1800000')
check('a derived value does not cross where no join names it', q.ask_lattice('cost', it=100, pue=1.52, hours=8760), 'refuse: no block can reach cost from what is given and what the joins carry')
q = Program('block a(x) -> y:\n    y = 2 * x\nblock b(x) -> y:\n    y = 3 * x\nblock c(y) -> z:\n    z = y + 1\njoin a c via y\njoin b c via y')
check('neighbours that disagree are refused', q.ask_lattice('z', x=5), 'refuse: y disagrees between neighbours: a says 10, b says 15')
q = Program('block a(x) -> y:\n    y = 2 * x\nblock b(x) -> y:\n    y = x + x\nblock c(y) -> z:\n    z = y + 1\njoin a c via y\njoin b c via y')
check('neighbours that agree are trusted', q.ask_lattice('z', x=5), '11')
q = Program('block a(x) -> y:\n    y = 2 * x\nblock b(y) -> z:\n    z = y + 1\njoin a b via y')
check('a missing value is re-derived by the neighbour (self-healing)', q.ask_lattice('x', z=11), '5')
try:
    Program('block k(x) -> y:\n    use nothing').ask('k', 'y', x=1); raise AssertionError('used a rule that does not exist')
except SyntaxError as e:
    passed += 1; print(f'  ok  {e}')

print('rules without a source do not parse')
try:
    Program('rule bad: z = x * y')
    raise AssertionError('parsed a rule with no label and source')
except SyntaxError as e:
    passed += 1; print(f'  ok  refused: {e}')

print('invariants over random relations')
random.seed(7)
for _ in range(200):
    w, h = random.randint(1, 500), random.randint(1, 500)
    a = p.ask('area', w=w, h=h)
    back = p.ask('area', 'w', a=a.v, h=h)
    assert back == Value(w), f'roundtrip failed for {w} x {h}: {back!r}'
passed += 1; print('  ok  200 seeds bloomed back to their inputs exactly')
r = p.ask('area', 'w', a=Refuse('pole'), h=3)
assert isinstance(r, Refuse), 'a refusal became a number'
passed += 1; print(f'  ok  a refusal stays a refusal: {r!r}')
f = p.run('y = square?(z = 16)')
try:
    float(f); raise AssertionError('a fork became a number without a decide')
except TypeError as e:
    passed += 1; print(f'  ok  {e}')
for n in (1, 3, 7):
    q = Program(f'climb c(x) -> y:\n    y = x + 1\n    after {n}: collapse')
    ladder, point = q.climb('c', 0)
    assert len(ladder) == n - 1 and point == Value(n - 1), 'n - 1 rungs, then the resolution'
passed += 1; print('  ok  every cap halts: n - 1 rungs and a resolution')
print(f'\n{passed} checks passed')
