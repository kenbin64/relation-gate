"""Tests for the multi-facing cube. Run: python tests/test_cube.py"""
import os, random, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cube import bloom, compose, decode, encode, face_of, hole_position, orientations, rotations, turned, verify, views

passed = 0
R = rotations()
assert len(R) == 24 and len(set(R)) == 24, 'a cube has 24 rotations'
assert all(compose(a, b) in set(R) for a in R for b in R), 'rotations compose to rotations'
passed += 1; print('  ok  24 rotations, closed under composition')

faces = orientations()
assert sorted(faces) == [('x', '+'), ('x', '-'), ('y', '+'), ('y', '-'), ('z', '+'), ('z', '-')]
assert all(len(v) == 4 for v in faces.values()), 'four rotations show each face'
passed += 1; print('  ok  six faces, four rotations each')

for axis in 'xyz':
    for hand in '+-':
        assert turned(axis, hand, axis) == (axis, '-' if hand == '+' else '+'), 'a turn about the own axis flips the hand'
        a, h = axis, hand
        for _ in range(4): a, h = turned(a, h, 'x')
        assert (a, h) == (axis, hand)
passed += 1; print('  ok  own-axis turn flips the hand; four turns is the identity')

v = views(0)
assert v['down z']['occupied'] > 0.99 and v['down z']['hole'] is None, 'the top is full'
assert abs(v['down x']['occupied'] - 0.5) < 0.03 and abs(v['down x']['hole']) < 0.03, 'a side is half, pinched at the centre'
assert abs(v['down y']['occupied'] - 0.5) < 0.03 and abs(v['down y']['hole']) < 0.03
for tilt in (15, 30):
    assert abs(views(tilt)['down x']['hole'] - hole_position(tilt)) < 0.04, f'the hole sits at tan({tilt})'
assert hole_position(45) is None, 'at 45 degrees the hole has left the cube'
passed += 1; print('  ok  top full, sides half with the hole at the centre; tilt moves the hole to tan(tilt); gone at 45')

random.seed(3)
for _ in range(200):
    bits = [random.randint(0, 1) for _ in range(random.randint(0, 40))]
    cells, bridges = encode(bits)
    assert decode(cells) == bits, 'the seams are the bits'
    assert bloom(len(bits), bridges) == cells, 'the chain regrows from the bridges alone'
    assert verify(cells, bridges)[0]
    assert len(bridges) == sum(bits), 'only the ones are stored'
passed += 1; print('  ok  200 messages: seams decode to the bits, the chain regrows from the bridges, only the ones are stored')

cells, bridges = encode([1, 0, 1, 1, 0])
bad = list(cells); bad[2] = ('z', '+' if cells[2][1] == '-' else '-')
ok, why = verify(bad, bridges); assert not ok and why.startswith('seam 1'), why
bad = list(cells); bad[3] = ('y', cells[3][1])
ok, why = verify(bad, bridges); assert not ok and 'axis changed' in why, why
ok, why = verify(cells, bridges + [1]); assert not ok and 'declared a bridge but the hands match' in why, why
passed += 1; print('  ok  a flipped cell, a wrong axis and a false bridge are each caught at a named seam')
from cube import collapse, rotate_all, whole
cells, bridges = encode([1, 0, 1, 1, 0, 0, 1, 0, 1])
views_seen = set(); unchanged = 0
for m in rotations():
    held = rotate_all(cells, m)
    assert whole(held) == whole(cells), 'the whole is the same however the cube is held'
    views_seen.add(tuple(held)); unchanged += held == cells
assert len(views_seen) == 6, 'six views of one whole: one per face the first cell can show'
assert unchanged == 4, 'four rotations leave every face as it was (the saddle\'s own symmetry: identity and the three half turns)'
passed += 1; print('  ok  the whole (the seams) is invariant under all 24 rotations; they show it as six views, four rotations each')
assert collapse([('z', '+'), ('z', '+'), ('z', '-')]) == ('z', '+')
assert collapse([('z', '+'), ('z', '-')]) == ('fork', [('z', '+'), ('z', '-')])
assert collapse([('x', '-')] * 7) == ('x', '-')
passed += 1; print('  ok  a block collapses to its majority face; a tie is a fork, not a guess')
print(f'\n{passed} checks passed')
