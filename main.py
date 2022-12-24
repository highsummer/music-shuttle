import mido
import time
import random
import numpy as np
from reharmonizer.note import MajorScale, NaturalMinorScale
from reharmonizer.note import Note as SingableNote
from reharmonizer.singable import Key, Enumerate, Parallel, AtChannel, Arpeggio, Transpose, Interval, Reharmonize, Repeat
from reharmonizer.singable import to_midi
from reharmonizer.instruments.piano import acoustic_grand_piano

PATTERN_CONSTRAINT = 1.0
PATTERN_HINGE_COEFF = 0.0
TENSION_CONSTRAINT = 0.75
HINGE_CONSTRAINT = 0.0
NEIGHBOR_CONSTRAINT = 1.0
MOMENTUM_CONSTRAINT = 0.5

port = mido.open_output('sforzando')

notations = ['C4', 'C#4', 'D4', 'D#4', 'E4', 'F4', 'F#4', 'G4', 'G#4', 'A4', 'A#4', 'B4']
notations = [*notations, *[n[:-1] + '5' for n in notations]]
key_offset = random.choice(list(range(12)))
print(f'Offset: {key_offset}')

if random.randint(0, 1) == 0:
    # C Ionian
    print('Ionian')
    offsets = [0, 2, 4, 5, 7, 9, 11]
    scale = MajorScale(tonic=SingableNote(notations[key_offset]))
else:
    # C Aeolian
    print('Aeolian')
    offsets = [0, 2, 3, 5, 7, 8, 10]
    scale = NaturalMinorScale(tonic=SingableNote(notations[key_offset]))

notation = [notations[o + key_offset] for o in offsets]

degrees = ['I', 'ii', 'iii', 'IV', 'V', 'vi', 'vii']
melodic_tensions = [0, 4, 2, 3, 5, 1, 6]
max_melodic_tension = max(melodic_tensions)
inv_melodic_tensions = [melodic_tensions.index(i) for i in range(len(melodic_tensions))]

distance_matrix = np.array([[[0, 1, 2, 3, -3, -2, 1][(i - j + 7) % 7] for j in range(7)] for i in range(7)])
neighbor_matrix = np.array([[[2, 0, 1, 2, -2, -1, 1][(i - j + 7) % 7] for j in range(7)] for i in range(7)])

def proportional_collapse(x):
    i = int(np.floor(x))
    j = i + 1
    if random.random() < 1 - (x - i):
        return i
    else:
        return j

def find_fraction(x, error):
    for i in range(1, 100):
        for j in range(1, 100):
            if abs(x - i / j) < error / j:
                return i, j
    raise ValueError(f'cannot find fraction for {x}')


class Scale:
    def __init__(self, index):
        self.index = index % 7
        self.offset = offsets[self.index]
        self.degree = degrees[self.index]
        self.freq = pow(2, self.offset / 12)
        _, denom = find_fraction(self.freq, 1 / 24)
        self.harmonic_tension = denom
        self.melodic_tension = melodic_tensions[self.index]
        
    def __str__(self):
        return f'Scale({self.degree}, +{self.offset}, x{self.freq:.2f}, ht:{self.harmonic_tension}, mt:{self.melodic_tension})'

scales = [Scale(i) for i in range(7)]

rhythm_entites = [('w', 4), ('q. q. q', 4), ('h.', 3), ('h', 2), ('q. e', 2), ('q', 1), ('e e', 1)]
rhythm_lengths = {
    **{
        key: value for key, value in rhythm_entites if len(key.split()) == 1
    },
    'q.': 1.5,
    'e': 0.5
}

class Note:
    def __init__(self, scale, length):
        self.scale = scale
        self.length = length
    
    def __repr__(self):
        return f'<Note {str(self.scale)} :{self.length}>'


class Melody:
    def __init__(self, other=None):
        self.progress = []
        if other is not None:
            self.progress = other.progress[:]

    def append(self, note):
        self.progress.append((note, self.length()))

    def length(self):
        if len(self.progress) == 0:
            return 0
        else:
            return self.progress[-1][0].length + self.progress[-1][1]

    def get_range(self, begin, end):
        return [n for n, t in self.progress if t >= begin and t < end]
    
    def mut_range(self, begin, end, mut):
        for n, t in self.progress:
            if t >= begin and t < end:
                mut(n)

    def assign_scale(self, i, scale):
        note, timing = self.progress[i]
        self.progress[i] = Note(scale, note.length), timing

    def __add__(self, other):
        m = Melody()
        for note, _ in self.progress:
            m.append(note)
        for note, _ in other.progress:
            m.append(note)
        return m


def generate_rhythm(length, epsilon=1e-2):
    rhythm = Melody()
    while rhythm.length() < length - epsilon:
        candidates = [e for e in rhythm_entites if e[1] <= length - rhythm.length()]
        mark, _ = random.choice(candidates)
        for token in mark.split():
            token_length = rhythm_lengths[token]
            rhythm.append(Note(scales[0], token_length))
    return rhythm


patterns = ['AABA', 'AAAB', 'AABC', 'ABAC']


class Constraint:
    def loss(self, melody):
        pass

class EqualTensionConstraint(Constraint):
    def __init__(self, i, j, weight):
        self.i = i
        self.j = j
        self.weight = weight

    def loss(self, melody):
        a, _ = melody.progress[self.i]
        b, _ = melody.progress[self.j]
        diff = b.scale.melodic_tension - a.scale.melodic_tension
        return abs(diff) * self.weight

class EqualScaleMomentumConstraint(Constraint):
    def __init__(self, i, j, k, l, weight):
        self.i = i
        self.j = j
        self.k = k
        self.l = l
        self.weight = weight

    def loss(self, melody):
        a, _ = melody.progress[self.i]
        b, _ = melody.progress[self.j]
        c, _ = melody.progress[self.k]
        d, _ = melody.progress[self.l]

        diff_ab = distance_matrix[a.scale.index, b.scale.index]
        diff_cd = distance_matrix[c.scale.index, d.scale.index]
        return abs(diff_ab - diff_cd) * self.weight

class NeighborScaleConstraint(Constraint):
    def __init__(self, i, j, weight):
        self.i = i
        self.j = j
        self.weight = weight

    def loss(self, melody):
        a, _ = melody.progress[self.i]
        b, _ = melody.progress[self.j]
        diff = neighbor_matrix[a.scale.index, b.scale.index]
        return abs(diff) * self.weight

class MomentumScaleConstraint(Constraint):
    def __init__(self, i, j, k, weight):
        self.i = i
        self.j = j
        self.k = k
        self.weight = weight

    def loss(self, melody):
        a, _ = melody.progress[self.i]
        b, _ = melody.progress[self.j]
        c, _ = melody.progress[self.k]
        diff_ab = distance_matrix[a.scale.index, b.scale.index]
        diff_ab = 1 if diff_ab > 0 else (-1 if diff_ab < 0 else 0)
        diff_bc = distance_matrix[b.scale.index, c.scale.index]
        diff_bc = 1 if diff_bc > 0 else (-1 if diff_bc < 0 else 0)
        return abs(diff_ab - diff_bc) * self.weight

class AssignTensionConstraint(Constraint):
    def __init__(self, i, x, weight):
        self.i = i
        self.x = x
        self.weight = weight

    def loss(self, melody):
        a, _ = melody.progress[self.i]
        diff = self.x - a.scale.melodic_tension
        return abs(diff) * self.weight * a.length


def generate_rhythmic_period(pattern, base_rhythm_length=4, motive_count=2):
    runes = sorted(set(pattern))
    rhythms = {
        rune: sum([generate_rhythm(base_rhythm_length) for _ in range(motive_count)], Melody()) for rune in runes
    }
    rhythmic_prog = sum([rhythms[motive] for motive in pattern], Melody())
    
    motive_length = base_rhythm_length * motive_count
    constraints = []
    for rune in runes:
        runes_interval = [(i * motive_length, (i + 1) * motive_length) for i, r in enumerate(pattern) if r == rune]
        notes_per_interval = [[i for i, (note, timing) in enumerate(rhythmic_prog.progress) if begin <= timing and timing < end] for begin, end in runes_interval]
        interval_per_notes = list(zip(*notes_per_interval))
        for k, pair in enumerate(interval_per_notes):
            for i, a in enumerate(pair):
                for b in pair[i + 1:]:
                    weight = PATTERN_CONSTRAINT # / pow(len(pair) - 1, 2) * (PATTERN_HINGE_COEFF if k == 0 or k == len(interval_per_notes) - 1 else 1.0)
                    constraints.append(EqualTensionConstraint(a, b, weight))
                    if a < len(rhythmic_prog.progress) - 1 and b < len(rhythmic_prog.progress) - 1:
                        constraints.append(EqualScaleMomentumConstraint(a, a + 1, b, b + 1, weight))

    return rhythmic_prog, constraints


def generate_part(pattern, min_tension, max_tension):
    rhythm, consts = generate_rhythmic_period(pattern)

    def fractal(base, n):
        if n == 0:
            return base
        else:
            return [x + y for x in base for y in fractal(base, n - 1)]

    tension = fractal([0, 1, 2, 0], 2)
    tension = (np.array(tension) / max(tension)) * (max_tension - min_tension) + min_tension

    def optimize(melody, consts, iters=50, num_mutants=128, fluctuations=8, force=0.5):
        for trial in range(iters):
            candidates = [melody]
            for _ in range(num_mutants):
                mutant_melody = Melody(melody)
                for _ in range(random.randint(1, fluctuations)):
                    target = random.randint(0, len(mutant_melody.progress) - 1)
                    mutant_melody.assign_scale(target, Scale(random.randint(0, 6)))
                candidates.append(mutant_melody)
            next_melody = min(candidates, key=lambda x: sum(c.loss(x) for c in consts))
            melody = next_melody
            if (trial + 1) % 10 == 0:
                current_loss = sum(c.loss(melody) for c in consts)
                print(f'trial {trial + 1}: {current_loss:.2f}')

        return melody


    def generate_melody(rhythm, tension, pattern_constraints):
        unit = len(tension) / rhythm.length()
        tension_constraints = [
            AssignTensionConstraint(i, tension[int(timing * unit)] * max_melodic_tension, TENSION_CONSTRAINT)
            for i, (note, timing) in enumerate(rhythm.progress)
        ]

        neighbor_smooth_constraints = [
            NeighborScaleConstraint(i, i + 1, NEIGHBOR_CONSTRAINT)
            for i in range(len(rhythm.progress) - 1)
        ]

        momentum_smooth_constraints = [
            MomentumScaleConstraint(i, i + 1, i + 2, NEIGHBOR_CONSTRAINT)
            for i in range(len(rhythm.progress) - 2)
        ]

        hinge_constraints = [
            AssignTensionConstraint(0, 0, HINGE_CONSTRAINT),
            AssignTensionConstraint(len(rhythm.progress) - 1, 0, HINGE_CONSTRAINT)
        ]

        total_constraints = [
            *pattern_constraints, 
            *tension_constraints, 
            *neighbor_smooth_constraints, 
            *momentum_smooth_constraints, 
            *hinge_constraints
        ]

        melody = Melody()
        for note, timing in rhythm.progress:
            melody.append(Note(Scale(random.randint(0, 6)), note.length))

        melody = optimize(melody, total_constraints)
        
        return melody

    melody = generate_melody(rhythm, tension, consts)
    return melody


# verse_part = generate_part(random.choice(patterns), 0, 0.5)
for i in range(8):
    print(f'Generating {i}...')
    melody = generate_part(random.choice(patterns), 0, 0.75)

    singable_scale = scale
    singable_melody = Enumerate()([Key(length=note.length, note=SingableNote(notation[note.scale.index])) for note, _ in melody.progress])

    reham = Reharmonize(singable_scale)(singable_melody)

    song = Parallel()([
        AtChannel(0)(singable_melody),
        AtChannel(1)(
            Arpeggio()(
                (
                    Transpose(Interval('-P8'))(
                        reham
                    ),
                    Repeat(8)(
                        Enumerate()([
                            Key(length=1/2, note=SingableNote('C4')),
                            Key(length=1/2, note=SingableNote('C##4')),
                            Key(length=1/2, note=SingableNote('C#4')),
                            Key(length=1/2, note=SingableNote('C##4')),
                            Key(length=1/2, note=SingableNote('C4')),
                            Key(length=1/2, note=SingableNote('C##4')),
                            Key(length=1/2, note=SingableNote('C#4')),
                            Key(length=1/2, note=SingableNote('C##4')),
                        ])
                    )
                )
            )
        ),
        AtChannel(2)(
            Transpose(Interval('-P15'))(
                reham
            ),
        ),
    ])

    mid = to_midi(song, instruments={ 
        0: acoustic_grand_piano,
        1: acoustic_grand_piano,
        2: acoustic_grand_piano,
    })
    mid.save(f'new_song_{i}.mid')

# for msg in mid.play():
#     port.send(msg)
