"""A gate program as a service over stdin and stdout, one JSON line in, one JSON line out, so a runner in
another language can call the gate hundreds of times without starting Python each time.

    python gate-server.py <program.gate>
    in:  {"gate": "extract", "text": "...the answer...", "input": "...the task input...", "key": "task-id|seed"}
    out: {"pass": 1, "facts": {"shape": 1, ...}} or {"pass": 0, "facts": {...}, "tries": 2} or {"refuse": "stopped after 3 tries, ..."}
"""
import json
import sys

from relation import Program, Refuse

program = Program(open(sys.argv[1], encoding='utf-8').read())
for line in sys.stdin:
    if not line.strip(): continue
    q = json.loads(line)
    r = program.check(q['gate'], q['text'], key=q.get('key'), input=q.get('input', ''))
    if isinstance(r, Refuse):
        out = {'pass': 0, 'refuse': r.reason}
    else:
        v = dict(r.v)
        out = {'pass': v.pop('pass'), 'tries': v.pop('tries', 0), 'tokens': v.pop('tokens'), 'spent': v.pop('spent'), 'facts': v}
    sys.stdout.write(json.dumps(out) + '\n'); sys.stdout.flush()
