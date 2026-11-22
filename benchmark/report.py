"""Reads results/raw-*.jsonl and reports every design, per model, against the bar for R (written before the run):
on the held-out tasks R lets through no more wrong answers than B, is right at least as often, and uses at most
half of B's tokens per correct answer.

    python report.py                 every results file
    python report.py llama3.2:3b     one model
"""
import glob
import json
import os
import sys

here = os.path.dirname(os.path.abspath(__file__))
only = sys.argv[1] if len(sys.argv) > 1 else None
NAMES = {'A': 'one call', 'B': 'agent pipeline', 'R': 'relation gate', 'G': 'library std'}
pct = lambda x: f'{100 * x:5.1f}%'


def summary(rs):
    n = len(rs); right = sum(r['ok'] for r in rs); abstain = sum(bool(r.get('abstained')) for r in rs)
    return {'n': n, 'right': right / n if n else 0, 'wrong': (n - right - abstain) / n if n else 0, 'abstain': abstain / n if n else 0,
            'tpc': sum(r['tokens'] for r in rs) / right if right else float('inf'), 'calls': sum(r['calls'] for r in rs) / n if n else 0}


for file in sorted(glob.glob(os.path.join(here, 'results', 'raw-*.jsonl'))):
    rows = [json.loads(line) for line in open(file, encoding='utf-8') if line.strip()]
    if only and not any(r['model'] == only for r in rows): continue
    designs = [d for d in NAMES if any(r['design'] == d for r in rows)]
    print(f'{os.path.basename(file)}: {len(rows)} answers, model {rows[0]["model"]}, designs {" ".join(designs)}')
    S = {}
    for s in ('original', 'heldout'):
        S[s] = t = {d: summary([r for r in rows if r['design'] == d and r['set'] == s]) for d in designs}
        print(f'  {s.upper():9s}          right   wrong  no answer  tokens/correct  calls')
        for d in designs: print(f'    {d} {NAMES[d]:15s} {pct(t[d]["right"])} {pct(t[d]["wrong"])} {pct(t[d]["abstain"])}   {t[d]["tpc"]:10.1f}   {t[d]["calls"]:5.2f}')
        for kind in ('classify', 'extract', 'calculate', 'format'):
            k = {d: summary([r for r in rows if r['design'] == d and r['set'] == s and r['kind'] == kind]) for d in designs}
            print(f'      {kind:9s} ' + ' | '.join(f'{d} {100 * k[d]["right"]:3.0f}% wrong {100 * k[d]["wrong"]:3.0f}% {k[d]["tpc"]:5.0f}' for d in designs))
    h = S['heldout']
    if 'R' in h and 'B' in h:
        ok = h['R']['wrong'] <= h['B']['wrong'] and h['R']['right'] >= h['B']['right'] and h['R']['tpc'] <= h['B']['tpc'] / 2
        print(f'  {"PASS" if ok else "NO  "}  R vs B on held-out: wrong {pct(h["R"]["wrong"])} vs {pct(h["B"]["wrong"])}; right {pct(h["R"]["right"])} vs {pct(h["B"]["right"])}; '
              f'tokens per correct {h["R"]["tpc"]:.0f} vs {h["B"]["tpc"]:.0f} ({h["B"]["tpc"] / h["R"]["tpc"]:.1f}x fewer; bar 2x)')
    R = [r for r in rows if r['design'] == 'R']
    if R:
        wrong = [r for r in R if not r.get('abstained') and not r['ok']]
        print(f'  R let through and wrong: {len(wrong)} of {len(R)}; abstained {sum(bool(r.get("abstained")) for r in R)}')
        for r in wrong: print(f'     {r["set"]} {r["task"]} seed {r["seed"]}: {r["answer"][:60]!r}')
    print()
