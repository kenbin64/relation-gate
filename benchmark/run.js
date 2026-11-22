#!/usr/bin/env node
// The benchmark behind RESULTS-RELATION.md, the public part: designs A (one call), B (a model checks a model)
// and R (the same worker, checked by the gate program in tasks.gate). Needs Ollama with the model, Node 18+,
// Python 3 with sympy.
//
//   node run.js llama3.2:3b                      all three designs, both task sets, three seeds
//   node run.js llama3.2:3b --designs R --tag v2 some designs, into results/raw-v2-<model>.jsonl
//
// One line per answer; answers already saved are not asked again. Token counts are the model's own.
'use strict';
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const { TASKS } = require('./tasks.js');
const { HELDOUT } = require('./heldout.js');
const { prompt } = require('./forms.js');
const { grade } = require('./grade.js');

const RUNS = 3;
const TEMPERATURE = 0.7;
const MOST_OUT = 80;
const HOST = 'http://localhost:11434';
const OUT = path.join(__dirname, 'results');
const FORM = 'mixed';
const GATE_SERVER = path.join(__dirname, '..', 'gate-server.py');
const GATE_PROGRAM = path.join(__dirname, 'tasks.gate');

async function ask(model, text, seed, most) {
  let j = null;
  for (let attempt = 1; !j; attempt++) {
    try {
      const r = await fetch(HOST + '/api/generate', {
        method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ model, prompt: text, stream: false, options: { temperature: TEMPERATURE, seed, num_predict: most } }),
      });
      if (!r.ok) throw new Error(`the model server answered ${r.status}`);
      j = await r.json();
    } catch (e) {
      if (attempt >= 5) throw new Error(`${model}: ${e.message}, five times running`);
      await new Promise(w => setTimeout(w, 3000 * attempt));
    }
  }
  return { text: (j.response || '').trim(), tokens: (j.prompt_eval_count || 0) + (j.eval_count || 0), ms: Math.round((j.total_duration || 0) / 1e6) };
}

// The gate as a service: one Python process, one JSON line per question, answered in order.
class GateClient {
  constructor() {
    this.proc = spawn('python', [GATE_SERVER, GATE_PROGRAM], { stdio: ['pipe', 'pipe', 'inherit'] });
    this.waiting = []; let buffer = '';
    this.proc.stdout.on('data', chunk => {
      buffer += chunk;
      let nl;
      while ((nl = buffer.indexOf('\n')) >= 0) { const line = buffer.slice(0, nl); buffer = buffer.slice(nl + 1); if (line.trim()) this.waiting.shift()(JSON.parse(line)); }
    });
  }
  check(q) { return new Promise(resolve => { this.waiting.push(resolve); this.proc.stdin.write(JSON.stringify(q) + '\n'); }); }
  close() { this.proc.stdin.end(); }
}
const gate = new GateClient();

// A. One call.
async function designA(model, task, seed) {
  const a = await ask(model, prompt(task, FORM), seed, MOST_OUT);
  return { answer: a.text, calls: 1, tokens: a.tokens, ms: a.ms, path: 'model' };
}

// B. Agent pipeline: answer, a model checks it (YES or NO), retry on NO, up to two retries. The last answer is
// handed over whatever the checker said.
async function designB(model, task, seed) {
  let calls = 0, tokens = 0, ms = 0, answer = '', path = 'model';
  const add = r => { calls++; tokens += r.tokens; ms += r.ms; return r; };
  let text = prompt(task, FORM);
  for (let attempt = 0; attempt <= 2; attempt++) {
    answer = add(await ask(model, text, seed + 100 * attempt, MOST_OUT)).text;
    const check = add(await ask(model,
      `You are checking another assistant's work.\n\nThe instruction it was given:\n${prompt(task, FORM)}\n\nIts answer:\n${answer}\n\n`
      + 'Is the answer correct and exactly in the required format? Reply with one word: YES or NO.', seed + 100 * attempt + 1, 3)).text;
    if (/^\W*yes/i.test(check)) break;
    if (attempt < 2) { path = 'model+retry'; text = `${prompt(task, FORM)}\n\nA checker rejected this earlier answer: ${answer}\nAnswer again, correctly and in the required format.`; }
  }
  return { answer, calls, tokens, ms, path };
}

// R. Relation gate: B's worker and B's retry wording; the checker is the gate program, no model call.
// Three failed tries and R abstains, where B hands over its last answer regardless.
async function designR(model, task, seed) {
  let calls = 0, tokens = 0, ms = 0, answer = '', path = 'model', passed = false, facts = null;
  let text = prompt(task, FORM);
  for (let attempt = 0; attempt <= 2; attempt++) {
    const a = await ask(model, text, seed + 100 * attempt, MOST_OUT);
    calls++; tokens += a.tokens; ms += a.ms; answer = a.text;
    const g = await gate.check({ gate: task.kind, text: answer, input: task.input, key: `${task.id}|${seed}` });
    facts = g.facts || null;
    if (g.pass) { passed = true; break; }
    if (attempt < 2) { path = 'model+retry'; text = `${prompt(task, FORM)}\n\nA checker rejected this earlier answer: ${answer}\nAnswer again, correctly and in the required format.`; }
  }
  return { answer, abstained: !passed, calls, tokens, ms, path: passed ? path : 'abstain', facts };
}

const ALL = { A: designA, B: designB, R: designR };
const SETS = [['original', TASKS], ['heldout', HELDOUT]];
const args = process.argv.slice(2);
const flag = (name, fallback) => { const i = args.indexOf('--' + name); return i >= 0 ? args[i + 1] : fallback; };
const DESIGNS = Object.fromEntries(flag('designs', 'ABR').split('').map(d => [d, ALL[d]]));
const TAG = flag('tag', '');
const models = args.filter((a, i) => !a.startsWith('--') && !(i > 0 && args[i - 1].startsWith('--')));

async function runModel(model) {
  fs.mkdirSync(OUT, { recursive: true });
  const file = path.join(OUT, 'raw-' + (TAG ? TAG + '-' : '') + model.replace(/[^a-z0-9.]+/gi, '-') + '.jsonl');
  const done = new Set();
  if (fs.existsSync(file)) for (const line of fs.readFileSync(file, 'utf8').split('\n')) if (line.trim()) { const r = JSON.parse(line); done.add(`${r.task}|${r.design}|${r.seed}`); }
  const began = Date.now(); let asked = 0;
  for (const [set, tasks] of SETS) for (const task of tasks) for (const design of Object.keys(DESIGNS)) for (let seed = 1; seed <= RUNS; seed++) {
    if (done.has(`${task.id}|${design}|${seed}`)) continue;
    const r = await DESIGNS[design](model, task, seed);
    fs.appendFileSync(file, JSON.stringify({ model, set, task: task.id, kind: task.kind, design, seed, abstained: false, ...r, ok: !r.abstained && grade(task, r.answer) }) + '\n');
    if (++asked % 60 === 0) console.log(`  ${model}: ${asked} new answers, ${Math.round((Date.now() - began) / 1000)}s`);
  }
  console.log(`${model}: finished, ${asked} new answers in ${Math.round((Date.now() - began) / 1000)}s`);
}

(async () => {
  if (!models.length) { console.log('usage: node run.js <model> [--designs ABR] [--tag name]'); gate.close(); return; }
  for (const model of models) await runModel(model);
  gate.close();
})().catch(e => { console.error(e.message); process.exit(1); });
