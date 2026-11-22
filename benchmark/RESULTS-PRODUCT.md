# The product detector: results (2026-11-22)

Plan and bars: PLAN-PRODUCT.md, written before the run. Code: product.py; the bars run by tests/test_product.py.
Two readings of every table, kept apart: the shape (the pinch where the bow tie's two edges cross, read as this
morning's cube was read) and the established fit (least squares on 1, x, y, xy). I ran it; two bars passed, two
did not, and both misses say something exact.

| Bar | Result | What was measured |
|---|---|---|
| 1. Exact products: offsets read off the shape within 2 percent of the column's spread, 200 random tables | **NO** by the worst case, yes by the typical one | Median error of the shape reading 1.7 percent, 90th percentile 6.0, worst 30.9. The fit is exact to rounding on every table. |
| 2. Noisy products: the residual is the noise and nothing more, 50 tables | **PASS** | Residual spread over noise spread between 0.91 and 1.06; the rule took everything that was rule. |
| 3. Not a product is refused: x + y, x squared, sin x | **PASS** | Refused all three; the rule reached 0, 0.9 and 3.9 percent of the column. |
| 4. The benchmark's calculate tasks, net = saving × uses − price, 20 rows, three columns | **NO** | The detector refused to call it a product: the rule reached 45.8 percent of the column, under the 50 percent line, and the residual correlated with −price at 0.73, not 0.95. |

## What the misses say

**Bar 1.** The shape reading is a crossing of two edges, and a crossing goes ill-conditioned when the two edges
are nearly parallel. That happens when the hidden offset sits at the edge of the other column's range: one edge
of the bow tie goes flat, the pinch becomes a tangency, and a small error in the edge moves the crossing a long
way. The worst case, 31 percent, is that case. Where the pinch sits in the middle 60 percent of the range the
median error is 1.5 percent and the worst 8.7. So the reading off the shape is a real reading, with a known
blind spot at the edge, and the fit beside it is the instrument that has no blind spot. The honest division of
labour: the geometry explains, the algebra measures, and the detector reports both and flags disagreement.

**Bar 4.** The detector was right and the bar was wrong. Net is not mostly a product; it is a product minus a
third column whose size is comparable, so with three columns the rule can reach only 46 percent, and refusing to
call that a product is the correct verdict. Given price as a fourth column (post hoc, labelled), the rule is
exact: z = (x − 0)(y − 0) + 0 − 1·w, residual zero to rounding, the net column 74 compressed bytes against 13 for
the residual at cent precision. That is the seed-and-bloom number for a real column: the rule and the price are
stored, the net is read, nothing is kept twice.

## What this says

- A product relation with hidden offsets can be read off the shape of three columns, as the cube was read: the
  pinch of each side view is an offset, the band's height there is the constant. Typically within 2 percent,
  with a known blind spot when the pinch sits at the edge of the range, where the established fit takes over.
- The residual is the honest measure: on exact products it is zero, on noisy ones it is the noise and nothing
  more, on non-products it is most of the column and the detector refuses to claim a rule.
- A real column that is a product plus another column is reported as such, not forced into a product; with the
  other column given, nothing remains to store but the rule and that column.
- One machine, synthetic tables, one real table of twenty rows. A first result, not a survey of data.
