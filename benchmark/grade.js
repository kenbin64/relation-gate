// The graders: is an answer right? Decided by fixed rules, never by a model.
//
// Each grader takes the text a model returned and the answer wanted, and says
// true or false. They are strict about the answer and forgiving about harmless
// wrapping: a code fence round JSON, a capital letter, a trailing full stop.
// They are not forgiving about extra talk when the instruction said "only".
'use strict';

// The JSON object in a reply, if the reply is nothing but that object (optionally inside a code fence).
function onlyJson(text) {
  let t = String(text).trim();
  const fenced = /^```(?:json)?\s*([\s\S]*?)\s*```$/.exec(t);
  if (fenced) t = fenced[1].trim();
  if (!t.startsWith('{') || !t.endsWith('}')) return null;
  try { const v = JSON.parse(t); return v && typeof v === 'object' && !Array.isArray(v) ? v : null; } catch (_) { return null; }
}
const sameKeys = (obj, keys) => Object.keys(obj).length === keys.length && keys.every((k) => k in obj);

const GRADERS = {
  // One word, one of the three labels. A capital or a final full stop is let through; a sentence is not.
  classify(text, want) {
    const word = String(text).trim().toLowerCase().replace(/[.!"'`*]+$/g, '').replace(/^["'`*]+/, '');
    return word === want;
  },
  // A JSON object with exactly the keys date and amount; the date as written, the amount as a number within a cent.
  extract(text, want) {
    const got = onlyJson(text);
    if (!got || !sameKeys(got, ['date', 'amount'])) return false;
    return got.date === want.date && typeof got.amount === 'number' && Math.abs(got.amount - want.amount) < 0.005;
  },
  // A number and nothing else, within a cent. A leading minus is allowed; a dollar sign or words are not.
  calculate(text, want) {
    const t = String(text).trim();
    if (!/^-?\d+(\.\d+)?$/.test(t)) return false;
    return Math.abs(Number(t) - want) < 0.005;
  },
  // A JSON object with exactly title, priority and tags: the title as given, a whole-number priority, the same tags in any order.
  format(text, want) {
    const got = onlyJson(text);
    if (!got || !sameKeys(got, ['title', 'priority', 'tags'])) return false;
    if (got.title !== want.title || !Number.isInteger(got.priority) || got.priority !== want.priority) return false;
    if (!Array.isArray(got.tags) || got.tags.length !== want.tags.length || !got.tags.every((x) => typeof x === 'string')) return false;
    return [...got.tags].sort().join('|') === [...want.tags].sort().join('|');
  },
};
const grade = (task, text) => GRADERS[task.kind](text, task.want);

module.exports = { grade, GRADERS, onlyJson };
