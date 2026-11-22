// The held-out tasks, written after the readers in seed.js, with a fixed seed so they never change.
//
// The wording varies on purpose, and some styles are ones the readers do not handle (03/14/2026, Mar 3, 2026,
// "USD 240.00", "Priority: 3", labels like "cost"), so the fallback to the model gets exercised. The right
// answers come from the generator's own numbers, never from a model. The reviews are written by hand.
'use strict';

let s = 20261026;
const rnd = () => (s = (s * 1103515245 + 12345) % 2147483648) / 2147483648;
const pick = a => a[Math.floor(rnd() * a.length)];
const int = (lo, hi) => lo + Math.floor(rnd() * (hi - lo + 1));
const pad = n => String(n).padStart(2, '0');
const MON = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
const money = c => (c / 100).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const extract = Array.from({ length: 10 }, (_, n) => {
  const y = int(2025, 2026), m = int(1, 12), d = int(1, 28), cents = int(500, 2000000);
  const date = pick([
    `${y}-${pad(m)}-${pad(d)}`, `${MON[m - 1]} ${d}, ${y}`, `${d} ${MON[m - 1]} ${y}`,          // styles the reader knows
    `${pad(m)}/${pad(d)}/${y}`, `${MON[m - 1].slice(0, 3)} ${d}, ${y}`, `${y}/${pad(m)}/${pad(d)}`, // styles it does not
  ]);
  const amount = pick([`$${money(cents)}`, `USD ${money(cents)}`, `${money(cents)} dollars`]);
  const line = pick([
    `Invoice ${int(1000, 9999)} issued ${date}. Amount due ${amount}.`,
    `${amount} paid on ${date} for ${pick(['window cleaning', 'software licence', 'freight', 'catering'])}.`,
    `Date: ${date} | Ref ${int(100, 999)} | Total ${amount}`,
  ]);
  return { id: 'h-extract-' + (n + 1), kind: 'extract', input: line, want: { date: `${y}-${pad(m)}-${pad(d)}`, amount: cents / 100 } };
});

const TITLES = ['Clean the gutters', 'Email the framer', 'Update the price list', 'Book the venue', 'Sharpen the tools', 'Pay the insurance', 'Sort the receipts', 'Plan the workshop', 'Fix the bike light', 'Test the backup'];
const TAGS = ['home', 'art', 'billing', 'urgent', 'weekly', 'team', 'garden', 'admin'];
const format = TITLES.map((title, n) => {
  const p = int(1, 5), tags = [...new Set([pick(TAGS), pick(TAGS)])];
  const input = pick([
    `${title}. Priority ${p}. Tags: ${tags.join(', ')}.`,                 // the style the reader knows
    `${title}. Priority: ${p}. Tags - ${tags.join(', ')}`,                // the rest it does not
    `${title} (priority ${p}), tagged ${tags.join(' and ')}.`,
    `Tags: ${tags.join(', ')}. ${title}. Priority ${p}.`,
  ]);
  return { id: 'h-format-' + (n + 1), kind: 'format', input, want: { title, priority: p, tags } };
});

const calculate = Array.from({ length: 10 }, (_, n) => {
  const price = int(5, 500) + pick([0, 0.5, 0.99]), saving = int(1, 40) * 0.25, uses = int(5, 120);
  const labels = pick([['price', 'saving per use', 'uses'], ['cost', 'saves per use', 'times used'], ['price', 'saving each time', 'number of uses']]);
  return { id: 'h-calculate-' + (n + 1), kind: 'calculate', input: `${labels[0]}: ${price}\n${labels[1]}: ${saving}\n${labels[2]}: ${uses}`,
    want: (Math.round(saving * 100) * uses - Math.round(price * 100)) / 100 };
});

const classify = [
  ['Two of the four chairs were broken and the courier just shrugged.', 'negative'],
  ['Fast delivery, solid build, and the instructions were clear. Very happy.', 'positive'],
  ['The parcel contained the lamp and a spare bulb.', 'neutral'],
  ['Still waiting for a refund after six weeks. Avoid this shop.', 'negative'],
  ['It does exactly what it says and the support team was lovely.', 'positive'],
  ['Delivered on the 12th. The box was blue.', 'neutral'],
  ['Cheap material, it tore the first time I used it.', 'negative'],
  ['My kids adore it and it has survived a whole summer of use.', 'positive'],
  ['The kit includes two brushes, a tray and a roller.', 'neutral'],
  ['Brilliant. I have already ordered a second one for my sister.', 'positive'],
].map(([input, want], n) => ({ id: 'h-classify-' + (n + 1), kind: 'classify', input, want }));

module.exports = { HELDOUT: [...classify, ...extract, ...calculate, ...format] };
