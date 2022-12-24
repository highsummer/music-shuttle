from .note import Note, Interval

def _get_melody_weight(melody):
    return [key.length for key in melody]


from collections import defaultdict
from math import floor


class ChordNode:
    def __init__(self, number, value, start, length):
        self.value = value
        self.total_value = None
        self.start = start
        self.length = length
        self.number = number
        self.prevs = []
        self.target = None
    
    def actual_value(self, length_advantage=1.1):
        return (self.length ** length_advantage) * self.value


class ChordDag:
    def __init__(self):
        self.nodes = []

    def add_node(self, number, value, start, length):
        self.nodes.append(ChordNode(number, value, start, length))
    
    def _build_edge(self, scale):
        for n in self.nodes:
            n.prev = []

        nodes_at_ending = defaultdict(list)
        for n in self.nodes:
            nodes_at_ending[n.start + n.length].append(n)
        
        for n in self.nodes:
            for m in nodes_at_ending[n.start]:
                if scale.is_transitable(m.number, n.number):
                    n.prev.append(m)

    def solve(self, scale):
        self._build_edge(scale)
        topological_nodes = sorted(self.nodes, key=lambda n: n.start)

        for n in topological_nodes:
            if n.prev:
                m = max(n.prev, key=lambda m: m.total_value)
                n.total_value = m.total_value + n.actual_value()
                n.target = m
            else:
                n.total_value = n.actual_value()
        
        timing_max = max([n.start + n.length for n in self.nodes])
        endnodes = [n for n in self.nodes if n.start + n.length == timing_max]
        endnode = max(endnodes, key=lambda n: n.total_value)
        result = []
        node = endnode
        while node:
            result.insert(0, node)
            node = node.target

        return result


def _score_melody(scale, melody, number, weight=None, score_consonance=1, score_fifth=0.5, score_primary=0.25, score_secondary=0.125, score_dissonance=-1):
    is_rest = [key.note is None for key in melody]
    melody = list(map(lambda x: x[1], filter(lambda x: not x[0], zip(is_rest, melody))))
    weight = list(map(lambda x: x[1], filter(lambda x: not x[0], zip(is_rest, weight))))

    if not melody:
        return 0

    base = scale.chord(number)
    primary = scale.available_tension_note_primary(number)
    secondary = scale.available_tension_note_secondary(number)
    
    def check_tuple(tup, x):
        for y in tup:
            if x.replace(octave=0) == y.replace(octave=0):
                return True
        return False

    if weight is None:
        weight = [1] * len(melody)
    
    score = []
    for key in melody:
        note = key.note
        if check_tuple(base[:2], note):
            score.append(score_consonance)
        elif check_tuple(base[2:], note):
            score.append(score_fifth)
        elif check_tuple(primary, note):
            score.append(score_primary)
        elif check_tuple(secondary, note):
            score.append(score_secondary)
        else:
            score.append(score_dissonance)

    return sum([s * w for s, w in zip(score, weight)]) / sum(weight)


def _song_to_chord(song, scale, granularity=(1, 2, 4), 
                   offset=0, cadence_at=16, cadence_score=1, restrictions=None):

    melody = list(song.sing())

    def _slice_melody(melody, start, length):
        end = start + length
        for k in melody:
            k_end = k.start + k.length
            if k.start >= start and k_end <= end:
                yield k
            elif k.start >= start and k.start < end and k_end > end:
                yield k.replace(length=start + length - k.start)
            elif k.start < start and k_end > start and k_end <= end:
                yield k.replace(start=start, length=k.start + k.length - start)
            else:
                pass
    
    time_max = int(max([k.start + k.length for k in melody]))
    dag = ChordDag()
    numbers = scale.possible_numbers()

    number_advantage = {
        'i': 0.2,
        'ii': -0.2,
        'iii': -0.2,
        'iv': 0.2,
        'v': 0.2,
        'vi': -0.2,
        'vii': -0.2,
        'v7/ii': -0.2,
        'v7/iii': -0.2,
        'v7/iv': -0.2,
        'v7/v': -0.2,
        'v7/vi': -0.2,
        'v7/vii': -0.2,
    }
    number_advantage = { k: 0 for k in number_advantage }

    for g in granularity:
        timing = offset
        while timing < time_max:
            if restrictions and timing in restrictions:
                dag.add_node(restrictions[timing], 0, timing, g)
            else:
                part = list(_slice_melody(melody, timing, g))
                weight = _get_melody_weight(part)
                scores = []
                for number in numbers:
                    score = _score_melody(scale, part, number, weight)
                    score += number_advantage[number]
                    if (timing + g - offset) % cadence_at == 0:
                        if number not in scale.possible_cadences():
                            score -= cadence_score
                    scores.append((number, score))
                for number, score in scores:
                    dag.add_node(number, score, timing, g)
            timing += g
    
    return dag.solve(scale)