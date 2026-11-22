"""Enigma, the relation way.

The machine is a relation: for a given key (rotor order, ring settings, start positions, plugboard) the cipher
letter at position i is a fixed function of the plain letter, and the function is its own inverse. Encrypt and
decrypt are the same operation, which is the property the attack leans on.

Specification (the gate): a recovered key is right when decrypting the ciphertext with it gives the plaintext.
That is exact. The ATTACK has to work without the plaintext, so it scores candidate decrypts by a statistic the
plaintext has and noise does not: the index of coincidence (how often two letters drawn at random are equal;
about 0.066 for English, 0.038 for random letters). This is the established method (Gillogly 1995): rotor order
and positions first, by IC, treating the plugboard as noise; then the plugboard pairs by hill-climbing on IC.

Solver (the levels): level 1 is the rotor order and positions (60 orders x 17,576 positions with five rotors;
6 x 17,576 here with rotors I to III, the three the early machines shipped with). The best few are kept, the
rest collapse away. Level 2 is the plugboard, pair by pair, each pair kept only if it raises the score.
Level 3 is the gate: decrypt in full and compare. Honest scope: ring settings fixed at A, a short plugboard,
a few hundred letters of text. The real machine had more settings and the real codebreakers had cribs and
bombes; this is the statistical attack, done in full on that scope.
"""
import itertools, time

A = ord('A')
ROTORS = {  # wiring, notch (the letter at which the rotor steps its neighbour)
    'I': ('EKMFLGDQVZNTOWYHXUSPAIBRCJ', 'Q'), 'II': ('AJDKSIRUXBLHWTMCQGZNPYFVOE', 'E'), 'III': ('BDFHJLCPRTXVZNYEIWGAKMUSQO', 'V'),
    'IV': ('ESOVPZJAYQUIRHXLNFTGKDCMWB', 'J'), 'V': ('VZBRGITYUPSDNHLXAWMJQOFECK', 'Z'),
}
REFLECTOR_B = 'YRUHQSLDPXNGOKMIEBFZCWVJAT'


class Enigma:
    def __init__(self, order, positions, rings='AAA', plugboard=''):
        self.order = order
        self.wiring = [[ord(c) - A for c in ROTORS[r][0]] for r in order]
        self.back = [[w.index(i) for i in range(26)] for w in self.wiring]
        self.notch = [ord(ROTORS[r][1]) - A for r in order]
        self.pos = [ord(c) - A for c in positions]
        self.ring = [ord(c) - A for c in rings]
        self.plug = list(range(26))
        for pair in plugboard.split():
            a, b = ord(pair[0]) - A, ord(pair[1]) - A; self.plug[a], self.plug[b] = b, a
        self.refl = [ord(c) - A for c in REFLECTOR_B]

    def step(self):
        """The stepping, with the double step of the middle rotor."""
        left, mid, right = 0, 1, 2
        if self.pos[mid] == self.notch[mid]: self.pos[left] = (self.pos[left] + 1) % 26; self.pos[mid] = (self.pos[mid] + 1) % 26
        elif self.pos[right] == self.notch[right]: self.pos[mid] = (self.pos[mid] + 1) % 26
        self.pos[right] = (self.pos[right] + 1) % 26

    def letter(self, c):
        self.step()
        x = self.plug[c]
        for r in (2, 1, 0):
            off = self.pos[r] - self.ring[r]
            x = (self.wiring[r][(x + off) % 26] - off) % 26
        x = self.refl[x]
        for r in (0, 1, 2):
            off = self.pos[r] - self.ring[r]
            x = (self.back[r][(x + off) % 26] - off) % 26
        return self.plug[x]

    def run(self, text):
        return ''.join(chr(self.letter(ord(ch) - A) + A) for ch in text)


def ic(text):
    n = len(text); counts = [0] * 26
    for ch in text: counts[ord(ch) - A] += 1
    return sum(c * (c - 1) for c in counts) / (n * (n - 1))


def crack(cipher, rotors=('I', 'II', 'III'), keep=10, sample=250):
    """Level 1: order and positions by IC on a sample; level 2: plugboard pairs by hill-climb; returns the best key."""
    head = cipher[:sample]; found = []
    for order in itertools.permutations(rotors, 3):
        for p in itertools.product(range(26), repeat=3):
            positions = ''.join(chr(A + i) for i in p)
            score = ic(Enigma(order, positions).run(head))
            found.append((score, order, positions))
    found.sort(reverse=True); best = []
    for score, order, positions in found[:keep]:                 # level 2 on the survivors only
        plugs, current = [], score
        letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        improved = True
        while improved and len(plugs) < 6:
            improved = False; trial = None
            used = set(''.join(plugs))
            for a, b in itertools.combinations([c for c in letters if c not in used], 2):
                s = ic(Enigma(order, positions, plugboard=' '.join(plugs + [a + b])).run(head))
                if s > current + 1e-9 and (trial is None or s > trial[0]): trial = (s, a + b)
            if trial: current, pair = trial; plugs.append(pair); improved = True
        best.append((current, order, positions, ' '.join(sorted(plugs))))
    best.sort(reverse=True)
    return best[0]


def gate(cipher, plain, key):
    score, order, positions, plugs = key
    got = Enigma(order, positions, plugboard=plugs).run(cipher)
    if got != plain:
        agree = sum(a == b for a, b in zip(got, plain)) / len(plain)
        return False, f'decrypt agrees with the plaintext on {agree:.0%} of letters only'
    return True, f'decrypt equals the plaintext, {len(plain)} letters, key {"-".join(order)} at {positions} plugboard [{plugs}]'


PLAIN = ('THEWEATHERFORECASTFORTOMORROWISCLEARWITHLIGHTWINDSFROMTHENORTHWESTANDATEMPERATUREOFTWELVEDEGREES'
         'ALLUNITSAREORDEREDTOHOLDTHEIRPOSITIONSUNTILFURTHERNOTICEANDTOREPORTANYMOVEMENTONTHECOASTROADBEFORE'
         'DAWNTHESUPPLYCONVOYWILLARRIVEATTHEHARBOURATSIXINTHEMORNINGANDMUSTBEUNLOADEDBEFORETHETIDETURNS'
         'THECOMMANDERSENDSHISREGARDSANDEXPECTSAFULLREPORTBYNOONTOMORROWENDOFMESSAGE')

if __name__ == '__main__':
    secret = (('III', 'I', 'II'), 'QEV', 'AZ MK')
    cipher = Enigma(*secret[:2], plugboard=secret[2]).run(PLAIN)
    assert Enigma(*secret[:2], plugboard=secret[2]).run(cipher) == PLAIN, 'the machine is its own inverse'
    print(f'plaintext {len(PLAIN)} letters, IC {ic(PLAIN):.4f}; ciphertext IC {ic(cipher):.4f}; secret key {"-".join(secret[0])} at {secret[1]} plugboard [{secret[2]}]')
    print('cracking with rotors I, II, III (6 orders x 17,576 positions, then the plugboard) ...')
    t0 = time.perf_counter(); key = crack(cipher); s = time.perf_counter() - t0
    ok, why = gate(cipher, PLAIN, key)
    print(f'{"PASS" if ok else "FAIL"}  {why}  (IC {key[0]:.4f}, {s:.0f} s)')
    print('a tampered key:', gate(cipher, PLAIN, (0, key[1], 'QEW', key[3])))
