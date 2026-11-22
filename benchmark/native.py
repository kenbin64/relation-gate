"""The native-language experiment (PLAN-NATIVE.md): prose vs a traditional program vs the relation language,
one call each, same model, same tasks, same seeds. Needs Ollama and tasks.json (exported from the benchmark).

    python native.py llama3.2:3b           runs; one line per answer in results/native-<model>.jsonl (resumable)
    python native.py llama3.2:3b --report  reports against the bars
"""
import json, os, re, subprocess, sys, tempfile, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from relation import numbers_in

HOST = 'http://localhost:11434'
RUNS = 3
TEMPERATURE = 0.7
DATA = json.load(open(os.path.join(HERE, 'tasks.json'), encoding='utf-8'))
INSTR = DATA['instructions']


LAST = {}   # the last call's split counts, for arms that report output tokens on their own


def ask(model, text, seed, most, schema=None):
    req = {'model': model, 'prompt': text, 'stream': False, 'options': {'temperature': TEMPERATURE, 'seed': seed, 'num_predict': most}}
    if schema: req['format'] = schema          # constrained decoding: the server only emits output that fits the schema
    body = json.dumps(req).encode()
    for attempt in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(HOST + '/api/generate', body, {'content-type': 'application/json'}), timeout=600) as r:
                j = json.load(r)
            LAST.update(prompt_tokens=j.get('prompt_eval_count', 0), output_tokens=j.get('eval_count', 0))
            return j.get('response', '').strip(), j.get('prompt_eval_count', 0) + j.get('eval_count', 0), j.get('total_duration', 0) // 1_000_000
        except Exception as e:
            if attempt == 4: raise
            time.sleep(3 * (attempt + 1))


# ---- the graders, ported line for line from grade.js (fixed rules, never a model)
def only_json(text):
    t = text.strip()
    m = re.fullmatch(r'```(?:json)?\s*([\s\S]*?)\s*```', t)
    if m: t = m.group(1).strip()
    if not (t.startswith('{') and t.endswith('}')): return None
    try: v = json.loads(t)
    except ValueError: return None
    return v if isinstance(v, dict) else None


def grade(task, text):
    kind, want = task['kind'], task['want']
    if kind == 'classify':
        word = re.sub(r'^["\'`*]+', '', re.sub(r'[.!"\'`*]+$', '', text.strip().lower()))
        return word == want
    if kind == 'calculate':
        t = text.strip()
        return bool(re.fullmatch(r'-?\d+(\.\d+)?', t)) and abs(float(t) - want) < 0.005
    got = only_json(text)
    if kind == 'extract':
        return bool(got) and sorted(got) == ['amount', 'date'] and got['date'] == want['date'] and isinstance(got['amount'], (int, float)) and not isinstance(got['amount'], bool) and abs(got['amount'] - want['amount']) < 0.005
    if kind == 'format':
        if not got or sorted(got) != ['priority', 'tags', 'title']: return False
        if got['title'] != want['title'] or not isinstance(got['priority'], int) or isinstance(got['priority'], bool) or got['priority'] != want['priority']: return False
        tags = got['tags']
        return isinstance(tags, list) and len(tags) == len(want['tags']) and all(isinstance(x, str) for x in tags) and sorted(tags) == sorted(want['tags'])


def prompt(task):
    k = INSTR[task['kind']]
    return f"{k['mixed']}\n\n{k['label']}: {task['input']}"


# ---- arm A: prose
def arm_a(model, task, seed):
    text, tokens, ms = ask(model, prompt(task), seed, 80)
    return {'answer': text, 'tokens': tokens, 'ms': ms, 'refused': False}


# ---- arm P: a traditional program, written by the model, run by us
SHAPE = {'classify': 'one of the strings "positive", "negative" or "neutral"',
         'extract': 'a JSON string of an object {"date": "YYYY-MM-DD", "amount": number}',
         'calculate': 'a number: saving per use times uses, minus price',
         'format': 'a JSON string of an object {"title": string without its final full stop, "priority": integer, "tags": [lower-case strings]}'}


def arm_p(model, task, seed):
    k = INSTR[task['kind']]
    text = (f"Write a Python function solve(text: str) that takes the {k['label'].lower()} below and returns {SHAPE[task['kind']]}.\n"
            f"Use only the standard library. Output only the code, no explanation, no example calls.\n\n{k['label']}: {task['input']}")
    code, tokens, ms = ask(model, text, seed, 400)
    m = re.search(r'```(?:python)?\s*([\s\S]*?)```', code)
    if m: code = m.group(1)
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, 'prog.py')
        open(path, 'w', encoding='utf-8').write(code + '\n\nimport json, sys\n_r = solve(sys.argv[1])\nprint(_r if isinstance(_r, str) else json.dumps(_r))\n')
        try:
            r = subprocess.run([sys.executable, '-I', path, task['input']], capture_output=True, text=True, timeout=10, cwd=d)
            out = r.stdout.strip() if r.returncode == 0 else ''
            err = '' if r.returncode == 0 else (r.stderr.strip().splitlines() or ['failed'])[-1][:120]
        except subprocess.TimeoutExpired:
            out, err = '', 'timeout'
    return {'answer': out, 'tokens': tokens, 'ms': ms, 'refused': False, 'code': code[:400], 'error': err}


# ---- arm L: the relation language, with sources, checked by the gate
LINE = re.compile(r'^\s*(\w+)\s*=\s*(.+?)\s+from\s+"([^"]*)"\s*$')
FIELDS = {'classify': ['sentiment'], 'extract': ['date', 'amount'], 'calculate': ['price', 'saving', 'uses'], 'format': ['title', 'priority', 'tags']}
EXAMPLE = {
    'classify': 'sentiment = negative from "it fell apart in a week"',
    'extract': 'date = 2026-03-14 from "2026-03-14"\namount = 1284.50 from "$1,284.50"',
    'calculate': 'price = 40 from "price: 40"\nsaving = 3 from "saving per use: 3"\nuses = 24 from "uses: 24"',
    'format': 'title = Fix the gallery signature from "Fix the gallery signature."\npriority = 2 from "Priority 2"\ntags = art, urgent from "Tags: art, urgent"',
}
RULE = {'classify': 'The sentiment is one word: positive, negative or neutral; its source is the words that decided it.',
        'extract': 'The date is written YYYY-MM-DD. The amount is a plain number, no $ or commas.',
        'calculate': 'State the three figures as they appear in the input: the price, the saving per use, the number of uses.',
        'format': 'The title is the task without its final full stop. The priority is a whole number. The tags are lower case, separated by commas.'}


SHORT_DIRECTIVE = '''You program in relations. Seven rules:
1. Write relations, not assignments: say what is true; the direction is chosen when someone asks.
2. Every value names its source: the exact words it came from. No source, no value: write refuse.
3. Do not compute what a rule can compute: state the figures with sources; the rule does the arithmetic.
4. The edges are values: division by zero is refuse; two readings is a fork a person decides; every loop has a cap.
5. Logic is arithmetic over 0 and 1: a check is a product of facts.
6. Every rule carries its label and its source.
7. Write dense; a program renders it readable. Output only the relation lines.

'''


def full_directive():
    text = open(os.path.join(os.path.dirname(HERE), 'DIRECTIVE.md'), encoding='utf-8').read()
    return text.split('## What the checker does')[0] + '\n'          # the rules and the output section; not the measurements


def arm_l(model, task, seed, prefix='', normalise=False):
    k = INSTR[task['kind']]; kind = task['kind']
    fields = FIELDS[kind]
    text = (prefix + f"Read the {k['label'].lower()} and write exactly {len(fields)} line{'s' if len(fields) > 1 else ''}, one per field, in this form and nothing else:\n"
            f"field = value from \"words copied exactly from the {k['label'].lower()}\"\n"
            f"Fields, in order: {', '.join(fields)}. {RULE[kind]}\n"
            f"Example, for a different {k['label'].lower()}:\n{EXAMPLE[kind]}\n\n{k['label']}: {task['input']}\n\nLines:")
    out, tokens, ms = ask(model, text, seed, 120)
    got, facts = {}, {'parsed': 1, 'sourced': 1, 'consistent': 1}
    for line in out.splitlines():
        m = LINE.match(line)
        if not m: continue
        name, value, src = m.groups()
        if name not in FIELDS[kind]: continue
        got[name] = value.strip()
        if src not in task['input']: facts['sourced'] = 0                     # the quoted source must be in the input, verbatim
        if not numbers_in(value) <= numbers_in(src) and name not in ('title', 'tags', 'sentiment'): facts['consistent'] = 0
    if any(f not in got for f in FIELDS[kind]): facts['parsed'] = 0
    answer = ''
    if all(facts.values()):
        try:
            answer = assemble(kind, got, normalise)
        except (ValueError, KeyError):
            facts['consistent'] = 0
    refused = not all(facts.values())
    return {'answer': '' if refused else answer, 'tokens': tokens, 'ms': ms, 'refused': refused, 'facts': facts, 'raw': out[:300],
            'prompt_tokens': LAST.get('prompt_tokens', 0), 'output_tokens': LAST.get('output_tokens', 0)}


# ---- arms E and F (PLAN-DIRECTIVE.md): L with the directive in front, full and short, dates read by the relation
def arm_e(model, task, seed): return arm_l(model, task, seed, prefix=full_directive(), normalise=True)


def arm_f(model, task, seed): return arm_l(model, task, seed, prefix=SHORT_DIRECTIVE, normalise=True)


# ---- arm C: the same relations with sources, but the server is constrained to the form (post hoc, 2026-11-21:
# the 3B model could speak the free-text form only 27.5 percent of the time; with constrained decoding the model
# cannot leave the form, so what remains to measure is reliability and tokens, which was the question)
def schema_for(kind):
    field = {'type': 'object', 'properties': {'value': {'type': 'string'}, 'from': {'type': 'string'}}, 'required': ['value', 'from']}
    return {'type': 'object', 'properties': {f: field for f in FIELDS[kind]}, 'required': FIELDS[kind]}


def schema_terse(kind):
    """The terse form: each field is a two-element array, value then source. Same facts, fewer tokens to say them."""
    field = {'type': 'array', 'items': {'type': 'string'}, 'minItems': 2, 'maxItems': 2}
    return {'type': 'object', 'properties': {f: field for f in FIELDS[kind]}, 'required': FIELDS[kind]}


def arm_c(model, task, seed, normalise=False, terse=False):
    k = INSTR[task['kind']]; kind = task['kind']; fields = FIELDS[kind]
    if terse:
        text = (f"Read the {k['label'].lower()} and give each field as a two-element array: the value, then the exact words copied "
                f"from the {k['label'].lower()} that the value came from.\nFields: {', '.join(fields)}. {RULE[kind]}\n\n{k['label']}: {task['input']}")
    else:
        text = (f"Read the {k['label'].lower()} and give each field as an object with two keys: \"value\", and \"from\", the exact words copied "
                f"from the {k['label'].lower()} that the value came from.\nFields: {', '.join(fields)}. {RULE[kind]}\n\n{k['label']}: {task['input']}")
    out, tokens, ms = ask(model, text, seed, 200, schema_terse(kind) if terse else schema_for(kind))
    split = dict(LAST)
    got, facts = {}, {'parsed': 1, 'sourced': 1, 'consistent': 1}
    try:
        obj = json.loads(out)
        for name in fields:
            v = obj.get(name) or ({} if not terse else [])
            if terse: value, src = (str(v[0]).strip(), str(v[1])) if isinstance(v, list) and len(v) == 2 else ('', '')
            else: value, src = str(v.get('value', '')).strip(), str(v.get('from', ''))
            if not value: continue
            got[name] = value
            if src not in task['input']: facts['sourced'] = 0
            if not numbers_in(value) <= numbers_in(src) and name not in ('title', 'tags', 'sentiment'): facts['consistent'] = 0
    except ValueError:
        pass
    if any(f not in got for f in fields): facts['parsed'] = 0
    answer = ''
    if all(facts.values()):
        try:
            answer = assemble(kind, got, normalise)
        except (ValueError, KeyError):
            facts['consistent'] = 0
    refused = not all(facts.values())
    return {'answer': '' if refused else answer, 'tokens': tokens, 'ms': ms, 'refused': refused, 'facts': facts, 'raw': out[:300],
            'prompt_tokens': split.get('prompt_tokens', 0), 'output_tokens': split.get('output_tokens', 0), 'chars': len(out)}


# ---- arm T (PLAN-ENCODING.md): D's checks on the terse form, value and source as a two-element array
def arm_t(model, task, seed):
    return arm_c(model, task, seed, normalise=True, terse=True)


# ---- arm D (post hoc, after C was read): C plus the language's own date relation. In C the model copied dates as
# written ("March 3, 2026") and the grader wants YYYY-MM-DD; the relation that reads a date in any written form
# (dates_in, the same one the gate uses) turns the copied value into the required form, or refuses if it cannot.
def arm_d(model, task, seed):
    return arm_c(model, task, seed, normalise=True)


def assemble(kind, got, normalise=False):
    """The graded answer from the parsed fields; the arithmetic comes from the rule, never from the model."""
    if kind == 'classify': return got['sentiment'].lower()
    if kind == 'extract':
        date = got['date']
        if normalise:
            from relation import dates_in
            read = dates_in(date)
            if len(read) != 1: raise ValueError('the date could not be read in one way')
            date = read.pop()
        return json.dumps({'date': date, 'amount': float(got['amount'].replace(',', '').replace('$', ''))})
    if kind == 'calculate':
        price, saving, uses = (float(got[f].replace(',', '').replace('$', '')) for f in ('price', 'saving', 'uses'))
        net = (round(saving * 100) * int(uses) - round(price * 100)) / 100
        return str(int(net)) if net == int(net) else str(net)
    tags = got['tags']
    tags = json.loads(tags) if tags.startswith('[') else [t.strip().lower() for t in tags.split(',') if t.strip()]
    return json.dumps({'title': got['title'].rstrip('.'), 'priority': int(got['priority']), 'tags': tags})


ARMS = {'A': arm_a, 'P': arm_p, 'L': arm_l, 'C': arm_c, 'D': arm_d, 'T': arm_t, 'E': arm_e, 'F': arm_f}


def run(model, arms=None):
    arms = {a: ARMS[a] for a in (arms or ARMS)}
    os.makedirs(os.path.join(HERE, 'results'), exist_ok=True)
    file = os.path.join(HERE, 'results', 'native-' + re.sub(r'[^a-z0-9.]+', '-', model, flags=re.I) + '.jsonl')
    done = set()
    if os.path.exists(file):
        for line in open(file, encoding='utf-8'):
            if line.strip(): r = json.loads(line); done.add((r['task'], r['arm'], r['seed']))
    began = time.time(); n = 0
    with open(file, 'a', encoding='utf-8') as out:
        for setname in ('original', 'heldout'):
            for task in DATA[setname]:
                for arm, fn in arms.items():
                    for seed in range(1, RUNS + 1):
                        if (task['id'], arm, seed) in done: continue
                        r = fn(model, task, seed)
                        r.update(model=model, set=setname, task=task['id'], kind=task['kind'], arm=arm, seed=seed, ok=(not r['refused']) and grade(task, r['answer']))
                        out.write(json.dumps(r) + '\n'); out.flush(); n += 1
                        if n % 60 == 0: print(f'  {model}: {n} new answers, {time.time() - began:.0f}s', flush=True)
    print(f'{model}: finished, {n} new answers in {time.time() - began:.0f}s')


def report(model):
    file = os.path.join(HERE, 'results', 'native-' + re.sub(r'[^a-z0-9.]+', '-', model, flags=re.I) + '.jsonl')
    rows = [json.loads(l) for l in open(file, encoding='utf-8') if l.strip()]
    pct = lambda x: f'{100 * x:5.1f}%'
    def summary(rs):
        n = len(rs); right = sum(r['ok'] for r in rs); ref = sum(r['refused'] for r in rs)
        return {'n': n, 'right': right / n if n else 0, 'wrong': (n - right - ref) / n if n else 0, 'refused': ref / n if n else 0, 'tpc': sum(r['tokens'] for r in rs) / right if right else float('inf')}
    print(f'{len(rows)} answers, {model}\n')
    present = [a for a in ARMS if any(r['arm'] == a for r in rows)]
    NAMES = {'A': 'prose', 'P': 'program', 'L': 'relation lines', 'C': 'relations, constrained', 'D': 'constrained + date rule', 'T': 'terse form (arrays)',
             'E': 'lines + full directive', 'F': 'lines + short directive'}
    S = {}
    for s in ('original', 'heldout'):
        S[s] = t = {a: summary([r for r in rows if r['arm'] == a and r['set'] == s]) for a in present}
        print(f'{s.upper():9s}                       right   wrong  refused  tokens/correct')
        for a in present:
            print(f'  {a} {NAMES[a]:22s} {pct(t[a]["right"])} {pct(t[a]["wrong"])} {pct(t[a]["refused"])}   {t[a]["tpc"]:10.0f}')
        for kind in ('classify', 'extract', 'calculate', 'format'):
            k = {a: summary([r for r in rows if r['arm'] == a and r['set'] == s and r['kind'] == kind]) for a in present}
            print(f'    {kind:9s} ' + ' | '.join(f'{a} {100 * k[a]["right"]:3.0f}% wrong {100 * k[a]["wrong"]:3.0f}% {k[a]["tpc"]:5.0f}' for a in present))
        print()
    if 'C' in present:
        C = [r for r in rows if r['arm'] == 'C']; h = S['heldout']
        print(f'C (constrained) parse rate {pct(sum(r["facts"]["parsed"] for r in C) / len(C))}; sourced {pct(sum(r["facts"]["sourced"] for r in C) / len(C))}; '
              f'held-out: right {pct(h["C"]["right"])} wrong {pct(h["C"]["wrong"])} refused {pct(h["C"]["refused"])} tokens per correct {h["C"]["tpc"]:.0f} (post hoc arm)')
        for r in [r for r in C if not r['refused'] and not r['ok']][:6]: print(f'   C wrong: {r["task"]} seed {r["seed"]}: {r["answer"][:50]!r}  raw {r["raw"][:90]!r}')
        for r in [r for r in C if r['refused']][:4]: print(f'   C refused: {r["task"]} seed {r["seed"]}: facts {r["facts"]} raw {r["raw"][:90]!r}')
    L = [r for r in rows if r['arm'] == 'L']
    parsed = sum(r['facts']['parsed'] for r in L) / len(L)
    print(f'L parse rate (all fields present on the first try): {pct(parsed)}; sourced {pct(sum(r["facts"]["sourced"] for r in L) / len(L))}; consistent {pct(sum(r["facts"]["consistent"] for r in L) / len(L))}')
    P = [r for r in rows if r['arm'] == 'P']
    print(f'P programs that ran without error: {pct(sum(not r.get("error") for r in P) / len(P))}')
    h = S['heldout']
    print('\nBARS (PLAN-NATIVE.md, before the run)')
    print(f'  {"PASS" if parsed >= 0.9 else "NO  "}  1. the model can speak it: parse rate {pct(parsed)} (bar 90%)')
    print(f'  {"PASS" if h["L"]["wrong"] < h["A"]["wrong"] and h["L"]["wrong"] < h["P"]["wrong"] else "NO  "}  2. held-out wrong: L {pct(h["L"]["wrong"])} vs A {pct(h["A"]["wrong"])} vs P {pct(h["P"]["wrong"])}')
    print(f'  {"PASS" if h["L"]["right"] >= h["P"]["right"] and h["L"]["tpc"] <= h["P"]["tpc"] else "NO  "}  3. held-out right L {pct(h["L"]["right"])} vs P {pct(h["P"]["right"])}; tokens per correct L {h["L"]["tpc"]:.0f} vs P {h["P"]["tpc"]:.0f}')
    print(f'  {"PASS" if h["L"]["tpc"] < h["A"]["tpc"] and h["L"]["tpc"] < h["P"]["tpc"] else "NO  "}  4. fewer tokens per correct on held-out: L {h["L"]["tpc"]:.0f} vs A {h["A"]["tpc"]:.0f} vs P {h["P"]["tpc"]:.0f}')
    for r in [r for r in L if not r['refused'] and not r['ok']][:8]: print(f'   L wrong: {r["task"]} seed {r["seed"]}: {r["answer"][:50]!r}  raw {r["raw"][:80]!r}')
    for r in [r for r in L if r['refused']][:6]: print(f'   L refused: {r["task"]} seed {r["seed"]}: facts {r["facts"]} raw {r["raw"][:80]!r}')


if __name__ == '__main__':
    model = sys.argv[1] if len(sys.argv) > 1 else 'llama3.2:3b'
    arms = sys.argv[sys.argv.index('--arms') + 1] if '--arms' in sys.argv else None
    report(model) if '--report' in sys.argv else run(model, arms)
