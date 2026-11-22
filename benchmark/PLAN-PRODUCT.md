# The product detector: plan and bars (written 2026-11-22, before any result)

Ken: "so now z = xy and the cube, how can we harness this?" Chosen first: a detector that finds a product relation
in three columns of data, reads its hidden offsets off the shape, and keeps only the residual.

## The question

Given three columns x, y, z, is z a product of x and y up to a shift, z = (x − a)(y − b) + c? If it is, read a, b
and c from the geometry (the pinches of the side views, the height of the band at the pinch), store the rule and
the residual, and report how much of the column the rule reaches. If it is not, say so, and do not claim a rule.

## How the shape is read

Looking down x, the points (y, z) form a bow tie whose band is narrowest at y = b, and the band there sits at
height c. Looking down y, the pinch is at x = a. These are the same observations as this morning's cube (the
hole moves to the tangent of the tilt; here the "tilt" is the shift), read from data instead of from the saddle.
The reading is cross-checked by the established method, a bilinear least-squares fit of z on 1, x, y and xy,
which gives the same three numbers algebraically. A reading off the shape that disagrees with the fit by more
than the noise is reported as a disagreement, not averaged away.

## Bars

1. **Exact data:** on 200 random tables z = (x − a)(y − b) + c with no noise, the offsets read from the shape are
   within 2 percent of the truth (relative to the column's spread) and the residual is zero to rounding.
2. **Noisy data:** with Gaussian noise of known size added, the residual's spread is within 10 percent of the
   noise's spread: the residual is the noise and nothing more, and the rule took everything that was rule.
3. **Not a product:** on z = x + y and z = x², the detector refuses to claim a product (the residual keeps at
   least half of the column's spread, and the side views are not bow ties).
4. **A real table:** the benchmark's own calculate tasks, net = saving × uses − price. The detector should find the
   product saving × uses and leave a residual equal to −price: a plain column, which is reported as such. The
   residual's compressed size against the column's compressed size, at the data's own precision (cents), is the
   seed-and-bloom number for a real column.

Reported as it is: the readings, the fit, the residual sizes, and every refusal. No speed claim.
