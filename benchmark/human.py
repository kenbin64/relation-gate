"""The human checker (PLAN-HUMAN.md): a browser page where a person accepts or rejects the same 80 answers the
model checker and the page of rules are judged on, with time per check recorded. Then a report of all three.

    python human.py                 opens the checking page at http://localhost:8766 (checks save as you go)
    python human.py --report        compares the person, the rules and the model checker on the same answers
                                    (asks the local models their YES/NO once, cached in results/model-checks.jsonl)
"""
import json, os, re, sys, time, urllib.request, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from relation import Program, Refuse

DATA = json.load(open(os.path.join(HERE, 'tasks.json'), encoding='utf-8'))
INSTR = DATA['instructions']
TASKS = {t['id']: t for t in DATA['heldout']}
MODELS = ['llama3.2:3b', 'qwen2.5-coder:7b']
HUMAN = os.path.join(HERE, 'results', 'human-checks.jsonl')
MODEL = os.path.join(HERE, 'results', 'model-checks.jsonl')
GATE = Program(open(os.path.join(HERE, 'tasks.gate'), encoding='utf-8').read())
sys.path.insert(0, HERE)
from native import grade, ask, prompt


def answers():
    """The 80 answers: each held-out task's first prose answer from each model, in a fixed order."""
    out = []
    for model in MODELS:
        f = os.path.join(HERE, 'results', 'native-' + re.sub(r'[^a-z0-9.]+', '-', model, flags=re.I) + '.jsonl')
        rows = [json.loads(l) for l in open(f, encoding='utf-8') if l.strip()]
        for r in rows:
            if r['set'] == 'heldout' and r['arm'] == 'A' and r['seed'] == 1:
                out.append({'key': f'{model}|{r["task"]}', 'model': model, 'task': r['task'], 'kind': r['kind'], 'answer': r['answer'], 'ok': r['ok']})
    return out


PAGE = r'''<!doctype html><html><head><meta charset="utf-8"><title>Human check</title>
<style>body{font:16px/1.5 system-ui;margin:0;background:#0f1420;color:#e8edf5}main{max-width:900px;margin:0 auto;padding:24px}
.box{background:#161d2c;border:1px solid #2a3448;border-radius:10px;padding:14px;margin:10px 0;white-space:pre-wrap;font-family:ui-monospace,Consolas,monospace;font-size:14px}
.label{color:#8e9ab3;font-size:13px;margin-top:10px}button{font:inherit;padding:12px 22px;border-radius:8px;border:0;cursor:pointer;margin-right:8px;font-weight:600}
#accept{background:#3ddc84}#reject{background:#ff5c6c}#unsure{background:#ffc857}.k{color:#8e9ab3}h1{font-size:20px}</style></head><body><main>
<h1>Check the answer <span class="k" id="n"></span></h1>
<p class="k">You see the instruction the model was given, the input, and its answer. No answer key. Accept if the answer is correct and exactly in the required format; Reject if not; Not sure if you cannot tell. Keys: A, R, N.</p>
<div class="label">Instruction</div><div class="box" id="instr"></div>
<div class="label">Input</div><div class="box" id="input"></div>
<div class="label">The model's answer</div><div class="box" id="answer"></div>
<p><button id="accept">Accept (A)</button><button id="reject">Reject (R)</button><button id="unsure">Not sure (N)</button></p>
<p class="k" id="done"></p>
<script>
let items=[],i=0,shown=0;
async function load(){items=await (await fetch('/items')).json();const d=await (await fetch('/done')).json();i=items.findIndex(x=>!d.includes(x.key));if(i<0){finish();return}show()}
function show(){const x=items[i];document.getElementById('n').textContent=(i+1)+' of '+items.length;document.getElementById('instr').textContent=x.instr;document.getElementById('input').textContent=x.input;document.getElementById('answer').textContent=x.answer;shown=performance.now()}
async function vote(v){const x=items[i];const ms=Math.round(performance.now()-shown);await fetch('/vote',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({key:x.key,verdict:v,ms})});i++;if(i>=items.length)finish();else show()}
function finish(){document.getElementById('done').textContent='All checked. Thank you. Now run: python human.py --report';document.getElementById('n').textContent='done';['instr','input','answer'].forEach(id=>document.getElementById(id).textContent='')}
document.getElementById('accept').onclick=()=>vote('accept');document.getElementById('reject').onclick=()=>vote('reject');document.getElementById('unsure').onclick=()=>vote('unsure');
document.onkeydown=e=>{const k=e.key.toLowerCase();if(k==='a')vote('accept');if(k==='r')vote('reject');if(k==='n')vote('unsure')};
load();
</script></main></body></html>'''


class Handler(BaseHTTPRequestHandler):
    def _send(self, body, kind='application/json'):
        data = body.encode() if isinstance(body, str) else json.dumps(body).encode()
        self.send_response(200); self.send_header('content-type', kind + '; charset=utf-8'); self.send_header('content-length', str(len(data))); self.end_headers(); self.wfile.write(data)

    def do_GET(self):
        if self.path == '/': return self._send(PAGE, 'text/html')
        if self.path == '/items':
            items = []
            for a in answers():
                t = TASKS[a['task']]; k = INSTR[t['kind']]
                items.append({'key': a['key'], 'instr': k['mixed'], 'input': t['input'], 'answer': a['answer']})
            return self._send(items)
        if self.path == '/done':
            done = [json.loads(l)['key'] for l in open(HUMAN, encoding='utf-8')] if os.path.exists(HUMAN) else []
            return self._send(done)
        self._send({'error': 'not here'})

    def do_POST(self):
        q = json.loads(self.rfile.read(int(self.headers.get('content-length', 0))))
        os.makedirs(os.path.dirname(HUMAN), exist_ok=True)
        with open(HUMAN, 'a', encoding='utf-8') as f: f.write(json.dumps({**q, 'at': time.time()}) + '\n')
        self._send({'ok': 1})

    def log_message(self, *a): pass


def model_checks():
    """The pipeline's own YES/NO on each answer, asked once and cached."""
    done = {}
    if os.path.exists(MODEL):
        for l in open(MODEL, encoding='utf-8'):
            if l.strip(): r = json.loads(l); done[r['key']] = r
    with open(MODEL, 'a', encoding='utf-8') as f:
        for a in answers():
            if a['key'] in done: continue
            t = TASKS[a['task']]
            text = (f"You are checking another assistant's work.\n\nThe instruction it was given:\n{prompt(t)}\n\nIts answer:\n{a['answer']}\n\n"
                    'Is the answer correct and exactly in the required format? Reply with one word: YES or NO.')
            reply, tokens, ms = ask(a['model'], text, 101, 3)
            r = {'key': a['key'], 'verdict': 'accept' if re.match(r'^\W*yes', reply, re.I) else 'reject', 'tokens': tokens, 'ms': ms, 'reply': reply}
            f.write(json.dumps(r) + '\n'); done[a['key']] = r
    return done


def report():
    human = {}
    for l in open(HUMAN, encoding='utf-8'):
        if l.strip(): r = json.loads(l); human[r['key']] = r
    items = answers()
    missing = [a['key'] for a in items if a['key'] not in human]
    if missing: print(f'{len(missing)} answers not yet checked by the person; run python human.py first'); return
    model = model_checks()
    rows = []
    for a in items:
        t = TASKS[a['task']]
        g = GATE.check(t['kind'], a['answer'], key='h|' + a['key'], input=t['input'])
        gate = 'reject' if isinstance(g, Refuse) or not g.v['pass'] else 'accept'
        rows.append({**a, 'human': human[a['key']]['verdict'], 'human_ms': human[a['key']]['ms'], 'model': model[a['key']]['verdict'], 'model_tokens': model[a['key']]['tokens'], 'gate': gate})
    def tally(name, pick, subset=lambda r: True):
        rs = [r for r in rows if subset(r)]
        through = sum(1 for r in rs if pick(r) == 'accept' and not r['ok']); thrown = sum(1 for r in rs if pick(r) == 'reject' and r['ok'])
        unsure = sum(1 for r in rs if pick(r) == 'unsure'); n = len(rs)
        return f'{name:16s} wrong let through {through:2d}/{n}   right thrown away {thrown:2d}/{n}   not sure {unsure:2d}'
    print(f'{len(rows)} answers, same for all three checkers; {sum(r["ok"] for r in rows)} of them are actually right\n')
    for label, subset in (('ALL', lambda r: True), ('shape-visible (extract, format)', lambda r: r['kind'] in ('extract', 'format')),
                          ('judgment and arithmetic (classify, calculate)', lambda r: r['kind'] in ('classify', 'calculate'))):
        print(label)
        print('  ' + tally('the person', lambda r: r['human'], subset))
        print('  ' + tally('the page of rules', lambda r: r['gate'], subset))
        print('  ' + tally('the model itself', lambda r: r['model'], subset))
    secs = sum(r['human_ms'] for r in rows) / 1000
    print(f'\ncost: the person {secs / len(rows):.1f} s per check, {secs / 60:.1f} minutes in all; the rules 0 tokens; '
          f'the model {sum(r["model_tokens"] for r in rows) / len(rows):.0f} tokens per check, {sum(r["model_tokens"] for r in rows):,} in all')
    print('\nBARS (PLAN-HUMAN.md, before the checks)')
    th = sum(1 for r in rows if r['human'] == 'accept' and not r['ok']); tm = sum(1 for r in rows if r['model'] == 'accept' and not r['ok'])
    print(f'  {"PASS" if th < tm else "NO  "}  1. the person lets through fewer wrong answers than the model checker: {th} vs {tm}')
    vis = [r for r in rows if r['kind'] in ('extract', 'format')]
    tg = sum(1 for r in vis if r['gate'] == 'accept' and not r['ok']); thv = sum(1 for r in vis if r['human'] == 'accept' and not r['ok'])
    print(f'  {"PASS" if tg <= thv else "NO  "}  2. on shape-visible answers the rules let through no more wrong than the person: {tg} vs {thv}')
    for r in rows:
        if (r['human'] == 'accept') != r['ok'] and r['human'] != 'unsure': print(f'   person {"accepted a wrong" if r["human"] == "accept" else "rejected a right"} answer: {r["task"]} ({r["model"]}): {r["answer"][:70]!r}')


if __name__ == '__main__':
    if '--report' in sys.argv: report()
    else:
        print(f'{len(answers())} answers to check at http://localhost:8766  (Ctrl+C when done; progress is saved as you go)')
        webbrowser.open('http://localhost:8766')
        ThreadingHTTPServer(('127.0.0.1', 8766), Handler).serve_forever()
