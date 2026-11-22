"""The relation language as an API, so any tool (an editor, a pipeline, TestThisPuppy, a script) can use it.

Python:
    from api import check, bloom, fold, ask, ledger
HTTP (JSON in, JSON out), nothing leaves the machine:
    python api.py                 serves on http://127.0.0.1:8767
    POST /check  {program, gate, text, input, key?, ledger?}   -> {pass, facts, tokens, spent, tries} or {pass: 0, refuse}
    POST /bloom  {terse}                                      -> {readable}
    POST /fold   {readable}                                   -> {terse}
    POST /ask    {program, block, target?, decide?, known}     -> {value} | {fork: [...]} | {refuse}
    POST /ledger {program}                                    -> {rules: [[name, relation, label, source], ...]}
    GET  /directive                                           -> DIRECTIVE.md, the text to hand an AI
"""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from relation import Fork, Program, Refuse, tokens
from render import bloom as _bloom, fold as _fold

PORT = 8767


def check(program, gate, text, input='', key=None, ledger=()):
    r = Program(program).check(gate, text, ledger=ledger, key=key, input=input)
    if isinstance(r, Refuse): return {'pass': 0, 'refuse': r.reason, 'tokens': tokens(text)}
    v = dict(r.v)
    return {'pass': v.pop('pass'), 'tries': v.pop('tries', 0), 'tokens': v.pop('tokens'), 'spent': v.pop('spent'), 'facts': v}


def bloom(terse): return {'readable': _bloom(terse)}


def fold(readable): return {'terse': _fold(readable)}


def ask(program, block, known, target=None, decide=None):
    r = Program(program).ask(block, target, decide, **known)
    if isinstance(r, Refuse): return {'refuse': r.reason}
    if isinstance(r, Fork): return {'fork': [str(v) for v in r.values]}
    return {'value': str(r.v)}


def ledger(program): return {'rules': Program(program).ledger()}


ROUTES = {'/check': lambda q: check(q['program'], q['gate'], q['text'], q.get('input', ''), q.get('key'), q.get('ledger', ())),
          '/bloom': lambda q: bloom(q['terse']), '/fold': lambda q: fold(q['readable']),
          '/ask': lambda q: ask(q['program'], q['block'], q.get('known', {}), q.get('target'), q.get('decide')),
          '/ledger': lambda q: ledger(q['program'])}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, kind='application/json'):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code); self.send_header('content-type', kind + '; charset=utf-8'); self.send_header('content-length', str(len(data))); self.end_headers(); self.wfile.write(data)

    def do_GET(self):
        if self.path == '/directive': return self._send(200, open(os.path.join(HERE, 'DIRECTIVE.md'), 'rb').read(), 'text/markdown')
        if self.path == '/': return self._send(200, __doc__.encode(), 'text/plain')
        self._send(404, {'error': 'not here'})

    def do_POST(self):
        q = json.loads(self.rfile.read(int(self.headers.get('content-length', 0)) or b'{}'))
        route = ROUTES.get(self.path)
        if not route: return self._send(404, {'error': 'not here'})
        try:
            self._send(200, route(q))
        except Exception as e:
            self._send(200, {'error': f'{type(e).__name__}: {e}'})

    def log_message(self, *a): pass


if __name__ == '__main__':
    print(f'relation language API: http://127.0.0.1:{PORT}   (GET / for the routes, GET /directive for the directive)')
    ThreadingHTTPServer(('127.0.0.1', PORT), Handler).serve_forever()
