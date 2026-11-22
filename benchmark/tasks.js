// The tasks: forty small jobs with a known right answer, ten of each of four kinds.
//
// Every task has an `input` (the text the model is given to work on) and a
// `want` (the right answer, used by the grader in grade.js). The instruction
// that goes with the input is NOT here: it is written several ways in forms.js,
// and the point of the benchmark is to compare those ways on the same tasks.
//
// The answers are fixed by hand or by the plain sums below, never by a model.
'use strict';

// ── 1. Classify: the sentiment of a short review ──────────────────────────
const classify = [
  ['The frame arrived cracked and nobody answered my emails.', 'negative'],
  ['Beautiful print, carefully packed, and it came two days early.', 'positive'],
  ['The colours are far duller than the photo. I want a refund.', 'negative'],
  ['Exactly what I ordered. The staff were kind and quick.', 'positive'],
  ['It arrived on Tuesday in a brown box.', 'neutral'],
  ['Worst purchase I have made this year. It fell apart in a week.', 'negative'],
  ['I love it. It hangs over the fireplace and everyone asks about it.', 'positive'],
  ['The order contained one frame and one mounting kit.', 'neutral'],
  ['Great value and it looks even better in person.', 'positive'],
  ['They charged me twice and it took a month to get the money back.', 'negative'],
].map(([input, want], n) => ({ id: 'classify-' + (n + 1), kind: 'classify', input, want }));

// ── 2. Extract: the date and the amount from one line of an invoice ───────
// Dates are written several ways on purpose; the answer is always YYYY-MM-DD.
const extract = [
  ['Invoice 4471 dated 2026-03-14 for plumbing repair, total due $1,284.50.', '2026-03-14', 1284.5],
  ['Paid on March 3, 2026: annual licence renewal, $240.00, ref LX-88.', '2026-03-03', 240],
  ['Ref 77120. Amount: $58.99. Date of service: 2025-11-30. Thank you.', '2025-11-30', 58.99],
  ['On 7 January 2026 we billed $12,400.00 for roof replacement (job 31).', '2026-01-07', 12400],
  ['Statement 2026-06-01. Balance forward 0.00. New charges $315.75.', '2026-06-01', 315.75],
  ['Order #5580 shipped. Charged $19.00 on December 12, 2025.', '2025-12-12', 19],
  ['Consulting, 40 hours, invoiced 2026-02-28. Total: $6,000.', '2026-02-28', 6000],
  ['Receipt: parking, $7.50, 2026-04-09, lot C.', '2026-04-09', 7.5],
  ['Due $1,050.25 for tuition. Issued 15 August 2025. Account 2219.', '2025-08-15', 1050.25],
  ['Renewal notice dated 2026-09-30: domain registration, $10.44.', '2026-09-30', 10.44],
].map(([input, date, amount], n) => ({ id: 'extract-' + (n + 1), kind: 'extract', input, want: { date, amount } }));

// ── 3. Calculate: is a purchase worth it? ─────────────────────────────────
// Net saving = saving per use x number of uses - price. The same sum the
// Cost of Saving calculators start from. The answer is worked out here in
// plain arithmetic, in cents so that no rounding error can creep in.
const calculate = [
  [40, 3, 24], [120, 2.5, 30], [15, 0.75, 52], [299, 12, 20], [60, 4, 15],
  [89.99, 6.5, 12], [25, 1.25, 100], [450, 35, 10], [9.99, 0.4, 36], [180, 7.25, 26],
].map(([price, saving, uses], n) => ({
  id: 'calculate-' + (n + 1), kind: 'calculate',
  input: `price: ${price}\nsaving per use: ${saving}\nuses: ${uses}`,
  want: (Math.round(saving * 100) * uses - Math.round(price * 100)) / 100,
}));

// ── 4. Format: turn a spoken to-do into a record of a fixed shape ─────────
const format = [
  ['Fix the gallery signature. Priority 2. Tags: art, urgent.', 'Fix the gallery signature', 2, ['art', 'urgent']],
  ['Renew the domain. Priority 1. Tags: billing.', 'Renew the domain', 1, ['billing']],
  ['Write the release notes. Priority 4. Tags: docs, release, team.', 'Write the release notes', 4, ['docs', 'release', 'team']],
  ['Call the plumber. Priority 3. Tags: home.', 'Call the plumber', 3, ['home']],
  ['Back up the photographs. Priority 2. Tags: files, weekly.', 'Back up the photographs', 2, ['files', 'weekly']],
  ['Order more canvas. Priority 5. Tags: art, supplies.', 'Order more canvas', 5, ['art', 'supplies']],
  ['Update the resume. Priority 1. Tags: jobs, writing.', 'Update the resume', 1, ['jobs', 'writing']],
  ['Test the contact form. Priority 3. Tags: site, qa.', 'Test the contact form', 3, ['site', 'qa']],
  ['Book the dentist. Priority 4. Tags: health.', 'Book the dentist', 4, ['health']],
  ['Pay the electricity bill. Priority 1. Tags: billing, home.', 'Pay the electricity bill', 1, ['billing', 'home']],
].map(([input, title, priority, tags], n) => ({ id: 'format-' + (n + 1), kind: 'format', input, want: { title, priority, tags } }));

module.exports = { TASKS: [...classify, ...extract, ...calculate, ...format], KINDS: ['classify', 'extract', 'calculate', 'format'] };
