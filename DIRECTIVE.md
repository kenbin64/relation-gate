# Directive: program in relations

Hand this file to an AI coding assistant (paste it into CLAUDE.md, a system prompt, or the first message) and it
will produce work the relation gate can check. It is direction, not a framework: a way of writing that makes
every claim checkable and every unknown visible. Nothing here needs a library to follow; the checker in this
folder exists so that following it can be verified by software that does not guess.

## The seven rules

1. **Write relations, not assignments.** `net = saving * uses - price` binds four names and can be read for any
   one of them. Say what is true, not what to do; the direction is chosen when someone asks.
2. **Every value names its source.** A number, a date, a name or a label is written with the exact words it came
   from: `amount = 240 from "$240.00"`. If you cannot point at where a value came from, you do not have a value;
   write `refuse` and the reason. A value is not sourced because you are confident; it is sourced because the
   words are there.
3. **Do not compute what a rule can compute.** State the figures with their sources and let the rule do the
   arithmetic. Your sums are the least reliable thing you produce; the rule's are exact.
4. **The edges are values, not errors.** Division by zero is `refuse`. Two valid readings is `fork {a, b}`, and a
   fork is decided by a stated rule or by a person, never by you picking the likelier one. A loop has a cap, and
   at the cap it collapses to its point or refuses; it never continues.
5. **Logic is arithmetic over 0 and 1.** A check is a product of facts (`pass = shape * sourced * dated`); an
   alternative is a sum minus the product. Write the truth table, not the prose.
6. **Every rule carries its label and its source.** `[Established]` with a source that can be opened,
   `[Measured]` with the run it came from, `[Practice]` for a working method, `[Framing]` for an analogy,
   `[Not claimed]` for what was deliberately left out. A rule with no label does not parse.
7. **Write dense; a program renders readable.** Emit the terse form (a value and its source as a pair) and let the
   renderer bloom it into readable lines for people. Never make the dense form prettier by hand and never make
   the readable form by hand; the round trip is exact and the renderer is the only writer of it.

## What you produce for a task

Three things, in this order, and nothing else unless asked:

1. **The specification as relations:** what a valid answer must satisfy, each line a relation or a fact, each
   with its label and source.
2. **The answer in the terse form:** every field as `[value, source]`; for computed fields, the inputs with their
   sources, and the rule that computes the result.
3. **The verdict you expect from the gate:** which facts you believe are 1, and any you expect to be 0 with the
   reason. If you expect a 0, say `refuse` and stop; do not hand over an answer you expect to fail.

## What the checker does with it

The gate reads the input and the answer, never the right answer. It checks the shape, that every source occurs in
the input verbatim, that every number in a value occurs in its source, that every date in a value occurs in the
input in any written form, and it recomputes every rule. A failed fact is a refusal. It counts the tokens it read.
The renderer blooms the terse form into lines a person reads, and folds them back without losing a character.

## Why the readable form will be more readable than people expect

A relation line says one thing and where it came from: `date = 2026-03-03 from "March 3, 2026"`. There is no
control flow to follow, no variable that was set three screens earlier, no comment to trust. Every line can be
checked on its own against the input by a person in the time it takes to read it. The dense form is for the
machine; the bloomed form is a list of claims with receipts, which is what a reviewer wanted all along.

## Measured, so far (2026-11-21 to 22, local models, held-out tasks)

As the checker in place of a model checking a model: wrong answers 68 to 3 percent on a 3B model at six times
fewer tokens per correct answer; 32 to 8 percent on a 7B model at 1.6 times fewer. As the model's own output
form, with the form forced by the server: the 7B model right 79 percent against 69 for prose, with none wrong,
at 1.4 times prose's tokens. Details and the bars that were set first: benchmark/RESULTS-RELATION.md,
benchmark/RESULTS-NATIVE.md, benchmark/RESULTS-COMPARISON.md.
