"""The relation language, prototype interpreter (2026-11-21).

Every line of a program is a relation, never an assignment: `a = w * h` binds three names, and a block holding
it can be asked for ANY one of them. Reading forward is the seed; reading backward is the bloom.

Four kinds of statement, all mostly mathematics:
    rule name: lhs = rhs [Label] "source"       one relation with its label and source (both required)
    block name(params) -> out:                  a level: several relations that collapse to one point
        <relation lines, indented>
    circuit name(params) -> out:                a block over facts (every variable is 0 or 1; * is AND)
        <relation lines, indented>
    climb name(x) -> y:                         one step of a ladder, repeated at most n times, then collapsed
        y = <expression in x>
        after n: collapse
    gate name(text):                            a truth table over facts pulled from text, with a cap
        fact = /regex/ in text                  1 if the pattern occurs in the text, else 0
        fact = source(text) in ledger           1 if every [tag] in the text is in the ledger
        pass = <0/1 arithmetic over the facts>
        after n: stop

Edges are values, not errors: dividing by zero gives Refuse, inverting a square gives Fork, and a Fork is
only turned into a value by an explicit `decide`. Nothing undefined ever becomes a number on its own.
"""
import re
from dataclasses import dataclass, field
from itertools import product

import sympy
from sympy import Eq, Symbol, nan, oo, solve, sympify, zoo

LABELS = ('[Established]', '[Measured]', '[Practice]', '[Framing]', '[Not claimed]')


# ---------------------------------------------------------------------------------------------- the three results
@dataclass(frozen=True)
class Value:
    v: object
    def __repr__(self): return f'{self.v}'


@dataclass(frozen=True)
class Fork:
    """Two or more values satisfy the relations; a fork is decided, never guessed."""
    values: tuple
    def __repr__(self): return 'fork {' + ', '.join(str(v) for v in self.values) + '}'
    def decide(self, keep):
        kept = tuple(v for v in self.values if keep(v))
        if len(kept) == 1: return Value(kept[0])
        if not kept: return Refuse('the decision rule kept nothing')
        return Fork(kept)
    def __float__(self): raise TypeError('a fork is not a number until it is decided')


@dataclass(frozen=True)
class Refuse:
    """No value, and the reason: a pole, an underdetermined question, or a cap reached."""
    reason: str
    def __repr__(self): return f'refuse: {self.reason}'
    def __float__(self): raise TypeError('a refusal is not a number')


# ---------------------------------------------------------------------------------------------- program pieces
@dataclass
class Rule:
    name: str; lhs: str; rhs: str; label: str; source: str


@dataclass
class Block:
    name: str; params: list; out: str; relations: list = field(default_factory=list); facts: bool = False


@dataclass
class Climb:
    name: str; x: str; y: str; step: str = ''; cap: int = 7


@dataclass
class Cell:
    """A saddle in a cube: an axis (the direction it bridges) and a hand (+ or -). The saddle z = xy has exactly six
    orientations under the 24 rotations of a cube (measured 2026-11-21): three axes, two hands."""
    name: str; axis: str; hand: str


@dataclass
class Join:
    """Two cells share a face, or two blocks share a variable. Cells join only when their hands match across the
    face (lock and key); a bridge is a mismatch made on purpose. Blocks joined via a variable re-derive it for each
    other: every point knows its neighbour."""
    a: str; b: str; via: str = ''; bridge: bool = False


@dataclass
class Gate:
    """A truth table over facts, with two caps: tries (`after n: stop`) and tokens (`within n tokens: stop`).
    z = token: when the level under the gate is a model, what crosses the gate is text, and text is priced in
    tokens, so every check reports the tokens it read and the tokens spent so far on the same key."""
    name: str; text: str; facts: list = field(default_factory=list); passes: str = ''; cap: int = 3
    budget: int = 0; tries: dict = field(default_factory=dict); spent: dict = field(default_factory=dict)


CHARS_PER_TOKEN = 4   # the estimate used in Ken's benchmarks, stated as an estimate, never as a count


def tokens(text):
    return (len(text) + CHARS_PER_TOKEN - 1) // CHARS_PER_TOKEN


# ---------------------------------------------------------------------------------------------- parsing
RULE = re.compile(r'rule\s+(\w+)\s*:\s*(.+?)\s*=\s*(.+?)\s*(\[[^\]]+\])\s*"([^"]*)"\s*$')
HEAD = re.compile(r'(block|circuit|climb|gate)\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*(\w+))?\s*:\s*$')
AFTER = re.compile(r'after\s+(\d+)\s*:\s*(collapse|stop)\s*$')
WITHIN = re.compile(r'within\s+(\d+)\s+tokens\s*:\s*stop\s*$')
REGEX_FACT = re.compile(r'(\w+)\s*=\s*/(.+)/\s+in\s+(\w+)\s*$')
LEDGER_FACT = re.compile(r'(\w+)\s*=\s*source\((\w+)\)\s+in\s+ledger\s*$')
JSON_FACT = re.compile(r'(\w+)\s*=\s*json\((\w+)\)\s*$')                       # the text is one JSON object
KEYS_FACT = re.compile(r'(\w+)\s*=\s*keys\((\w+)\)\s*=\s*([\w\s,]+)$')         # with exactly these keys
NUMBERS_FACT = re.compile(r'(\w+)\s*=\s*numbers\((\w+)\)\s+in\s+input\s*$')    # every number in it occurs in the input
DATES_FACT = re.compile(r'(\w+)\s*=\s*dates\((\w+)\)\s+in\s+input\s*$')        # every date in it occurs in the input, in any written form
STRINGS_FACT = re.compile(r'(\w+)\s*=\s*strings\((\w+)\)\s+in\s+input\s*$')    # every JSON string value occurs in the input
QUERY = re.compile(r'(\w+)\s*=\s*(\w+)\?\((.*)\)(?:\s*decide\s+(.+))?\s*$')
CELL_SADDLE = re.compile(r'cell\s+(\w+)\s*=\s*saddle\(\s*axis\s+([xyz])\s*,\s*hand\s*([+-])\s*\)\s*$')
CELL_TURN = re.compile(r'cell\s+(\w+)\s*=\s*turn\(\s*(\w+)\s*,\s*about\s+([xyz])\s*\)\s*$')
JOIN = re.compile(r'(join|bridge)\s+(\w+)\s+(\w+)(?:\s+via\s+(\w+))?\s*$')
USE = re.compile(r'use\s+(\w+)\s*$')

# A quarter turn of a saddle about a cube axis. Computed, not typed: rotate the points of z = hand * x * y and read
# off which axis is now the height and which hand it has. The same method that found the six orientations.
ROTATE = {'x': lambda x, y, z: (x, -z, y), 'y': lambda x, y, z: (z, y, -x), 'z': lambda x, y, z: (-y, x, z)}
AXES = 'xyz'


def turned(axis, hand, about):
    """The (axis, hand) of a saddle after a quarter turn about `about`."""
    i = AXES.index(axis); j, k = [n for n in range(3) if n != i]
    sign = 1 if hand == '+' else -1
    points = []
    for a in (-1, 0, 1, 2):
        for b in (-1, 0, 1, 2):
            p = [0, 0, 0]; p[j], p[k], p[i] = a, b, sign * a * b
            points.append(ROTATE[about](*p))
    for h in range(3):
        u, v = [n for n in range(3) if n != h]
        for s in (1, -1):
            if all(p[h] == s * p[u] * p[v] for p in points): return AXES[h], '+' if s > 0 else '-'
    raise ValueError('a quarter turn of a saddle is always a saddle; this cannot happen')


def strip_comment(line):
    return line.split('#', 1)[0].rstrip()


def json_object(text):
    """The JSON object in a text, if the text is nothing but that object (a code fence around it is allowed)."""
    import json
    t = text.strip()
    m = re.fullmatch(r'```(?:json)?\s*([\s\S]*?)\s*```', t)
    if m: t = m.group(1).strip()
    if not (t.startswith('{') and t.endswith('}')): return None
    try:
        v = json.loads(t)
    except ValueError:
        return None
    return v if isinstance(v, dict) else None


MONTHS = {m: i + 1 for i, m in enumerate(['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
                                           'september', 'october', 'november', 'december'])}
ISO_DATE = r'\b(\d{4})-(\d{2})-(\d{2})\b'


def dates_in(text):
    """Every date in a text, in any common written form, as YYYY-MM-DD: 2026-03-14, March 3, 2026, 7 January 2026,
    Mar 3, 2026, 03/14/2026 (month first, the American form), 2026/03/14."""
    found = set()
    def month(word):
        w = word.lower()
        return next((n for name, n in MONTHS.items() if name.startswith(w[:3]) and (len(w) == 3 or name.startswith(w))), None)
    for y, m, d in re.findall(ISO_DATE, text): found.add(f'{y}-{m}-{d}')
    for y, m, d in re.findall(r'\b(\d{4})/(\d{2})/(\d{2})\b', text): found.add(f'{y}-{m}-{d}')
    for m, d, y in re.findall(r'\b(\d{2})/(\d{2})/(\d{4})\b', text): found.add(f'{y}-{m}-{d}')
    for name, d, y in re.findall(r'\b([A-Za-z]{3,9})\.? (\d{1,2}), (\d{4})\b', text):
        if month(name): found.add(f'{y}-{month(name):02d}-{int(d):02d}')
    for d, name, y in re.findall(r'\b(\d{1,2}) ([A-Za-z]{3,9}) (\d{4})\b', text):
        if month(name): found.add(f'{y}-{month(name):02d}-{int(d):02d}')
    return found


def numbers_in(text):
    """Every number written in a text, as a value: 1,284.50 is 1284.5. Dates written YYYY-MM-DD are left to
    dates_in (their month number need not appear in an input that wrote the month as a word; the first benchmark
    run refused correct answers for that, fixed 2026-11-21 and labelled post hoc)."""
    text = re.sub(ISO_DATE, ' ', text)
    # a number may be followed by a full stop that ends the sentence, so only a letter, a digit or a decimal point
    # WITH a digit after it stops a match
    return {float(m.replace(',', '')) for m in re.findall(r'(?<![\w.])(\d(?:[\d,]*\d)?(?:\.\d+)?)(?!\w|\.\d)', text)}


def strings_in(value):
    """Every string inside a JSON value, however deep."""
    if isinstance(value, str): return [value]
    if isinstance(value, dict): return [s for v in value.values() for s in strings_in(v)]
    if isinstance(value, list): return [s for v in value for s in strings_in(v)]
    return []


def decides(rule, target, value):
    """Is `value` kept by a decide rule such as `y >= 0` or `y != 0`? The value is written in for the name first,
    so every comparison, `!=` included, is between numbers and gives a plain yes or no."""
    written = re.sub(rf'\b{re.escape(target)}\b', f'({value})', rule)
    return bool(sympify(written))


class Program:
    def __init__(self, text):
        self.rules, self.blocks, self.climbs, self.gates = {}, {}, {}, {}
        self.cells, self.joins = {}, []
        self._parse(text)

    def _parse(self, text):
        current = None
        for raw in text.splitlines():
            line = strip_comment(raw)
            if not line.strip(): continue
            indented = line[0] in ' \t'
            if indented and current is not None:
                self._body(current, line.strip())
            else:
                current = self._head(line.strip())

    def _head(self, line):
        m = RULE.match(line)
        if m:
            name, lhs, rhs, label, source = m.groups()
            if label not in LABELS: raise SyntaxError(f'rule {name}: unknown label {label}')
            if not source: raise SyntaxError(f'rule {name}: a rule with no source does not parse')
            self.rules[name] = Rule(name, lhs, rhs, label, source)
            return None
        if line.startswith('rule'): raise SyntaxError(f'a rule needs a label and a source: {line}')
        m = CELL_SADDLE.match(line)
        if m:
            self.cells[m.group(1)] = Cell(m.group(1), m.group(2), m.group(3)); return None
        m = CELL_TURN.match(line)
        if m:
            name, other, about = m.groups()
            if other not in self.cells: raise SyntaxError(f'cell {name}: no cell called {other} to turn')
            axis, hand = turned(self.cells[other].axis, self.cells[other].hand, about)
            self.cells[name] = Cell(name, axis, hand); return None
        m = JOIN.match(line)
        if m:
            kind, a, b, via = m.groups()
            self.joins.append(Join(a, b, via or '', kind == 'bridge')); return None
        m = HEAD.match(line)
        if not m: raise SyntaxError(f'cannot read: {line}')
        kind, name, params, out = m.groups()
        params = [p.strip() for p in params.split(',') if p.strip()]
        if kind in ('block', 'circuit'):
            self.blocks[name] = b = Block(name, params, out, facts=(kind == 'circuit')); return b
        if kind == 'climb':
            self.climbs[name] = c = Climb(name, params[0], out); return c
        self.gates[name] = g = Gate(name, params[0]); return g

    def _body(self, owner, line):
        m = AFTER.match(line)
        if m:
            owner.cap = int(m.group(1)); return
        m = WITHIN.match(line)
        if m and isinstance(owner, Gate):
            owner.budget = int(m.group(1)); return
        if isinstance(owner, Block):
            owner.relations.append(line); return
        if isinstance(owner, Climb):
            owner.step = line.split('=', 1)[1].strip(); return
        m = REGEX_FACT.match(line)
        if m: owner.facts.append((m.group(1), 'regex', m.group(2))); return
        m = LEDGER_FACT.match(line)
        if m: owner.facts.append((m.group(1), 'ledger', m.group(2))); return
        for kind, pattern in (('json', JSON_FACT), ('keys', KEYS_FACT), ('numbers', NUMBERS_FACT), ('strings', STRINGS_FACT), ('dates', DATES_FACT)):
            m = pattern.match(line)
            if m: owner.facts.append((m.group(1), kind, m.group(3).strip() if kind == 'keys' else '')); return
        if line.startswith('pass'): owner.passes = line.split('=', 1)[1].strip(); return
        raise SyntaxError(f'cannot read inside {owner.name}: {line}')

    # ------------------------------------------------------------------------------------------ asking a block
    def ask(self, block_name, target=None, decide=None, **known):
        """Read a block for one unknown, given any set of knowns. Returns Value, Fork or Refuse."""
        if block_name in self.rules:
            r = self.rules[block_name]
            block = Block(r.name, [], r.lhs, [f'{r.lhs} = {r.rhs}'])
        else:
            block = self.blocks[block_name]
        target = target or block.out
        for k, v in known.items():
            if isinstance(v, (Fork, Refuse)): return Refuse(f'{k} is {v!r}; nothing is built on it')
        if block.facts: return self._ask_facts(block, target, known)
        return self._ask_algebra(block, target, known, decide)

    def _equations(self, block):
        eqs = []
        for rel in block.relations:
            m = USE.match(rel)                                   # `use name`: the named rule's relation, by reference
            if m:
                if m.group(1) not in self.rules: raise SyntaxError(f'{block.name} uses a rule that does not exist: {m.group(1)}')
                r = self.rules[m.group(1)]; rel = f'{r.lhs} = {r.rhs}'
            lhs, rhs = rel.split('=', 1)
            eqs.append(Eq(sympify(lhs.replace('^', '**')), sympify(rhs.replace('^', '**'))))
        return eqs

    # ------------------------------------------------------------------------------------------ cells and seams
    def seam(self, a, b):
        """What happens where two cells meet: joined (hands match), bridged (a mismatch made on purpose), or a refusal."""
        join = next((j for j in self.joins if {j.a, j.b} == {a, b}), None)
        if join is None: return Refuse(f'{a} and {b} are not joined')
        ca, cb = self.cells[a], self.cells[b]
        match = (ca.axis, ca.hand) == (cb.axis, cb.hand)
        if match and not join.bridge: return Value(f'joined: both {ca.axis}{ca.hand}, the surface is continuous across the face')
        if match and join.bridge: return Refuse(f'bridge {a} {b}: the hands already match ({ca.axis}{ca.hand}); a bridge is for a mismatch')
        if join.bridge: return Value(f'bridged: {a} is {ca.axis}{ca.hand}, {b} is {cb.axis}{cb.hand}; the crossover is declared')
        return Refuse(f'{a} ({ca.axis}{ca.hand}) and {b} ({cb.axis}{cb.hand}) do not match across the face; turn one, or bridge on purpose')

    def lattice(self):
        """Every seam's verdict, in the order the joins were written."""
        return [(j.a, j.b, self.seam(j.a, j.b)) for j in self.joins if j.a in self.cells and j.b in self.cells]

    # ------------------------------------------------------------------------------------------ joined blocks
    def ask_lattice(self, target, **known):
        """Read a variable across blocks joined `via` shared variables. A value derived inside one block crosses to
        a neighbour only through a declared join, and only for the variable the join names. Two neighbours that
        derive the same variable must agree, or the lattice refuses: every point knows its neighbour, and a point
        that contradicts its neighbour is not trusted. A variable the asker gives is known to every block."""
        values = {k: (sympify(v), 'given') for k, v in known.items()}
        derived = {}                                              # (block, var) -> value, to stop re-deriving
        changed = True
        while changed:
            changed = False
            for name, block in self.blocks.items():
                if block.facts: continue
                symbols = {str(s) for e in self._equations(block) for s in e.free_symbols}
                seen = {v: values[v][0] for v in symbols if v in values and self._reaches(values[v][1], name, v)}
                for var in symbols - set(seen):
                    if (name, var) in derived: continue
                    r = self._ask_algebra(block, var, seen, None)
                    if not isinstance(r, Value): continue
                    derived[(name, var)] = r.v; changed = True
                    if var in values and values[var][1] != name and sympify(values[var][0]) != r.v:
                        return Refuse(f'{var} disagrees between neighbours: {values[var][1]} says {values[var][0]}, {name} says {r.v}')
                    if var not in values: values[var] = (r.v, name)
        if target in values: return Value(values[target][0])
        return Refuse(f'no block can reach {target} from what is given and what the joins carry')

    def _reaches(self, origin, block, var):
        """May a value of `var` that came from `origin` be used inside `block`? Given values reach everywhere; a
        derived value crosses only a join that names the variable."""
        if origin in ('given', block): return True
        return any({j.a, j.b} == {origin, block} and j.via == var for j in self.joins)

    def _ask_algebra(self, block, target, known, decide):
        subs = {Symbol(k): sympify(v) for k, v in known.items()}
        eqs = [e.subs(subs) for e in self._equations(block)]
        for e in eqs:
            if e.has(zoo, nan, oo) or e is sympy.false:
                return Refuse(f'pole: a relation in {block.name} has no value at these inputs')
        eqs = [e for e in eqs if e is not sympy.true]
        unknowns = sorted(set().union(*(e.free_symbols for e in eqs)), key=str) if eqs else []
        if Symbol(target) not in unknowns:
            if target in known: return Refuse(f'{target} was given, not asked')
            if any(Symbol(target) in e.free_symbols for e in self._equations(block)):
                zeros = [k for k, v in known.items() if sympify(v) == 0]
                return Refuse(f'pole: {target} vanishes at these inputs ({", ".join(zeros) or "a zero"} multiplies it away)')
            return Refuse(f'{target} does not appear in {block.name}')
        try:
            sols = solve(eqs, unknowns, dict=True)
        except Exception as ex:
            return Refuse(f'cannot solve {block.name}: {ex}')
        found = []
        for s in sols:
            v = s.get(Symbol(target))
            if v is None or v.free_symbols: continue
            if v.has(zoo, nan, oo): return Refuse('pole: division by zero')
            found.append(v)
        if not found: return Refuse(f'underdetermined: give more of {", ".join(map(str, unknowns))}')
        found = tuple(sorted(dict.fromkeys(found), key=lambda v: (0, float(v)) if v.is_real else (1, str(v))))
        if len(found) == 1: return Value(found[0])
        fork = Fork(found)
        return fork.decide(lambda v: decides(decide, target, v)) if decide else fork

    def _ask_facts(self, block, target, known):
        """Facts are 0 or 1: enumerate the unknown inputs and keep every assignment the relations allow."""
        eqs = self._equations(block)
        names = sorted(set().union(*(e.free_symbols for e in eqs)), key=str)
        free = [s for s in names if str(s) not in known]
        hits = []
        for bits in product((0, 1), repeat=len(free)):
            env = {Symbol(k): v for k, v in known.items()}; env.update(zip(free, bits, strict=True))
            if all(e.subs(env) == sympy.true for e in eqs):
                hits.append({str(s): int(env[s]) for s in names})
        if not hits: return Refuse(f'no 0/1 assignment satisfies {block.name}')
        if len(hits) == 1: return Value(hits[0])
        return Fork(tuple(hits))

    # ------------------------------------------------------------------------------------------ the ladder
    def climb(self, name, start, **constants):
        """Run one step at most `cap` times from `start`; return the ladder and the collapsed point."""
        c = self.climbs[name]
        expr = sympify(c.step.replace('^', '**'))
        consts = {Symbol(k): sympify(v) for k, v in constants.items()}
        x, ladder = sympify(start), []
        for _ in range(c.cap):
            x = expr.subs(consts).subs(Symbol(c.x), x)
            if x.has(zoo, nan, oo): return ladder, Refuse('pole reached on the ladder')
            ladder.append(x)
        return ladder, Value(ladder[-1])

    # ------------------------------------------------------------------------------------------ the gate
    def check(self, gate_name, text, ledger=(), key=None, input=''):
        """Evaluate the gate's truth table on one text. After `cap` failures on the same key it stops.
        `input` is the task's own input, for the facts that ask whether the answer's numbers or strings occur in it."""
        g = self.gates[gate_name]
        key = key or text
        if g.tries.get(key, 0) >= g.cap: return Refuse(f'stopped after {g.cap} tries, {g.spent.get(key, 0)} tokens spent')
        if g.budget and g.spent.get(key, 0) + tokens(text) > g.budget:
            return Refuse(f'stopped: {g.spent.get(key, 0) + tokens(text)} tokens would pass the budget of {g.budget}')
        g.spent[key] = g.spent.get(key, 0) + tokens(text)
        env = {}
        for name, kind, arg in g.facts:
            if kind == 'regex': env[name] = 1 if re.search(arg, text) else 0
            elif kind == 'ledger':
                tags = re.findall(r'\[([\w-]+)\]', text)
                env[name] = 1 if tags and all(t in ledger for t in tags) else 0
            elif kind == 'json': env[name] = 1 if json_object(text) is not None else 0
            elif kind == 'keys':
                obj = json_object(text)
                env[name] = 1 if obj is not None and sorted(obj) == sorted(k.strip() for k in arg.split(',')) else 0
            elif kind == 'numbers':
                env[name] = 1 if numbers_in(text) and numbers_in(text) <= numbers_in(input) else 0
            elif kind == 'dates':
                env[name] = 1 if dates_in(text) and dates_in(text) <= dates_in(input) else 0
            elif kind == 'strings':
                # exact, case included: "Call the Plumber" is not in "Call the plumber." (the first benchmark run
                # compared without case and let three capitalised titles through; changed 2026-11-21, labelled post hoc)
                obj = json_object(text)
                env[name] = 1 if obj is not None and all(s in input for s in strings_in(obj)) else 0
        # the fact values are written into the pass line by name before it is read as arithmetic, so a fact may be
        # called shape, date or amount without colliding with a function of the same name in the algebra engine
        written = g.passes
        for name, v in env.items(): written = re.sub(rf'\b{re.escape(name)}\b', str(v), written)
        ok = int(sympify(written))
        if ok: return Value({'pass': 1, **env, 'tokens': tokens(text), 'spent': g.spent[key]})
        g.tries[key] = g.tries.get(key, 0) + 1
        return Value({'pass': 0, **env, 'tries': g.tries[key], 'tokens': tokens(text), 'spent': g.spent[key]})

    # ------------------------------------------------------------------------------------------ text queries
    def run(self, line):
        """`w = area?(a = 12, h = 3) decide w >= 0` as text."""
        m = QUERY.match(strip_comment(line).strip())
        if not m: raise SyntaxError(f'not a query: {line}')
        target, block, args, decide = m.groups()
        known = {}
        for part in args.split(','):
            if part.strip():
                k, v = part.split('=', 1); known[k.strip()] = sympify(v.strip())
        return self.ask(block, target, decide, **known)

    def ledger(self):
        return [(r.name, f'{r.lhs} = {r.rhs}', r.label, r.source) for r in self.rules.values()]
