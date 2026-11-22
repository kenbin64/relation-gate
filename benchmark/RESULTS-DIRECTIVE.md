# The directive as a benchmark: results (2026-11-22)

Plan and bars: PLAN-DIRECTIVE.md, written before the run. Arms E (DIRECTIVE.md's rules as a prefix, about 740
tokens) and F (seven lines, about 160 tokens) in front of the free-text relation form, nothing forcing the output,
against L (the same form with no directive) and A (a plain-language answer). Held-out tasks, three seeds, one call
each. Tokens per correct answer count the prefix, because a user pays for it on every call.

## Qwen 2.5 Coder, 7 billion parameters

| Arm | Right | Wrong | Refused | Held the form unaided | Prompt tokens per call | Tokens per correct |
|---|---|---|---|---|---|---|
| A plain answer | 69.2% | 30.8% | 0.0% | | 0 prefix | 168 |
| L relation lines, no directive | 68.3% | 0.0% | 31.7% | 70.0% | 0 prefix | 284 |
| E lines + full directive | **87.5%** | 1.7% | 10.8% | **97.5%** | 895 | 1,069 |
| F lines + short directive | 84.2% | 1.7% | 14.2% | 86.7% | 312 | 414 |

## Llama 3.2, 3 billion parameters

| Arm | Right | Wrong | Refused | Held the form unaided | Prompt tokens per call | Tokens per correct |
|---|---|---|---|---|---|---|
| A plain answer | 50.8% | 49.2% | 0.0% | | 0 prefix | 218 |
| L relation lines, no directive | 30.0% | 0.0% | 70.0% | 30.8% | 0 prefix | 570 |
| E lines + full directive | 28.3% | 8.3% | 63.3% | 90.0% | 879 | 3,229 |
| F lines + short directive | 44.2% | 4.2% | 51.7% | 67.5% | 301 | 762 |

## The bars

1. **The directive teaches the form (90 percent held, 7B, unaided): PASS** with the full directive, 97.5 percent;
   the short one reached 86.7. Handing the model the rules did what forcing the server did, without the server.
2. **It helps (right at least as often as L, no more wrong, both models): NO by the letter, and the letter matters.**
   On the 7B, right rose from 68 to 88 percent, the best non-library number in the whole study, and two answers in
   120 were wrong where L had none: both are sentiment calls, "neutral" for broken chairs and a shrugging courier,
   "positive" for a blue box. Judgment, the fork, which no source check can see. On the 3B the directive hurt:
   the small model treated the rules as content, wrote "field = neutral" literally, numbered its lines, and spent
   900 tokens of prefix for 28 percent right. A directive is for a model that can read one.
3. **The short one is enough (within three points at fewer tokens): NO by 0.3 points.** 84.2 against 87.5 right,
   equal wrong, at 414 against 1,069 tokens per correct. The short directive buys 95 percent of the gain at 39
   percent of the cost. It is the one to ship; the full text is the documentation behind it.
4. **Cost, reported as it is:** the directive rides in every prompt. Full: 895 tokens a call, which makes each
   correct answer cost 6.4 times a plain one. Short: 312 a call, 2.5 times. In an assistant the prefix sits in a
   cached system prompt and is billed once per session, not per call, which this benchmark does not model; the
   per-call cost here is the ceiling.

## What was let through, and the one that teaches something

The short directive on the 7B let one date through wrong: "01/11/2026" read as the first of November, where the
task's generator meant the eleventh of January. The free-text arms check numbers against sources, and the source
was copied exactly, so nothing refused it. The gate's date relation would have, because 01/11/2026 read month-first
is 2026-01-11 and the answer said 2026-11-01. More to the point, that date is a genuine fork: two valid readings of
the same words, and the model decided it silently. The language's rule is that a fork is decided by a stated rule
or a person, never by the model picking the likelier reading. The next version of the date relation marks the
ambiguous forms as a fork instead of reading them one way, which is rule four applied to itself.

## What this says

- Handing a capable model the seven rules is enough to make it program in relations unaided: 97.5 percent held
  the form, 87.5 percent right, 1.7 percent wrong, against 69 percent right and 31 percent wrong for the same
  model answering plainly. That is the directive working as a directive.
- The cost of the directive is tokens, and it is not small on a per-call basis. The short form is the practical one.
- A 3B model is not the audience for a directive; it needs the form forced by the server (arm D), where it reached
  50 percent right with none wrong.
- The remaining wrong answers are judgment and an ambiguous date: the fork, both times. The language has a word for
  that, and the next change makes the date relation use it.
