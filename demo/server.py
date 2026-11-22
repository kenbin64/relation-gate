"""The relation gate, demonstrated in a browser on your own PC. Nothing leaves the machine.

    python demo/server.py            then open http://localhost:8765

Endpoints (JSON): POST /check {program, gate, text, input}  -> the gate's verdict with every fact
                  POST /ask   {model, prompt}               -> the local model's answer with its token count (Ollama)
                  GET  /tasks                               -> the benchmark tasks, for the pick list
"""
import json, os, sys, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from relation import Program, Refuse, tokens

OLLAMA = 'http://localhost:11434'
PORT = 8765


def check(q):
    program = Program(q['program'])
    r = program.check(q['gate'], q['text'], key=q.get('key') or None, input=q.get('input', ''))
    if isinstance(r, Refuse): return {'pass': 0, 'refuse': r.reason, 'tokens': tokens(q['text'])}
    v = dict(r.v)
    return {'pass': v.pop('pass'), 'tries': v.pop('tries', 0), 'tokens': v.pop('tokens'), 'spent': v.pop('spent'), 'facts': v}


def ask(q):
    body = json.dumps({'model': q['model'], 'prompt': q['prompt'], 'stream': False,
                       'options': {'temperature': q.get('temperature', 0.7), 'seed': q.get('seed', 1), 'num_predict': q.get('most', 120)}}).encode()
    with urllib.request.urlopen(urllib.request.Request(OLLAMA + '/api/generate', body, {'content-type': 'application/json'}), timeout=600) as r:
        j = json.load(r)
    return {'text': j.get('response', '').strip(), 'tokens': j.get('prompt_eval_count', 0) + j.get('eval_count', 0), 'ms': j.get('total_duration', 0) // 1_000_000}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, kind='application/json'):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code); self.send_header('content-type', kind + '; charset=utf-8'); self.send_header('content-length', str(len(data))); self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == '/' or self.path.startswith('/index'):
            return self._send(200, open(os.path.join(HERE, 'index.html'), 'rb').read(), 'text/html')
        if self.path == '/tasks':
            return self._send(200, open(os.path.join(HERE, '..', 'benchmark', 'tasks.json'), 'rb').read())
        if self.path == '/program':
            return self._send(200, open(os.path.join(HERE, '..', 'benchmark', 'tasks.gate'), 'rb').read(), 'text/plain')
        if self.path == '/favicon.ico':                       # found by TestThisPuppy's site check: a 404 here logs a console error
            self.send_response(204); self.end_headers(); return
        self._send(404, {'error': 'not here'})

    def do_POST(self):
        q = json.loads(self.rfile.read(int(self.headers.get('content-length', 0)) or b'{}'))
        try:
            if self.path == '/check': return self._send(200, check(q))
            if self.path == '/ask': return self._send(200, ask(q))
            self._send(404, {'error': 'not here'})
        except Exception as e:
            self._send(200, {'error': f'{type(e).__name__}: {e}'})

    def log_message(self, fmt, *args): pass


if __name__ == '__main__':
    print(f'relation gate demo: http://localhost:{PORT}   (Ctrl+C stops it)')
    ThreadingHTTPServer(('127.0.0.1', PORT), Handler).serve_forever()
