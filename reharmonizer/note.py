import re

class Interval:
    def __init__(self, notation=None, number=None, quality=None, inverted=False):
        if notation:
            # TODO: add notation syntax check
            inverted, quality, number = re.match(r'(-)?(M|m|A|AA|d|dd|P)(\d+)', notation).groups()
            number = int(number)
            inverted = True if inverted else False
        
        self.number = number
        self.quality = quality
        self.inverted = inverted

    def is_potentially_perfect(self):
        corrected_number = ((self.number - 1) % 7) + 1
        return corrected_number == 1 or corrected_number == 4 or corrected_number == 5 or corrected_number == 8

    def augment(self):
        if self.is_potentially_perfect():
            order_perfect = ['dd', 'd', 'P', 'A', 'AA']
            # TODO: add out of range exception
            return Interval(number=self.number, quality=order_perfect[order_perfect.index(self.quality) + 1], inverted=self.inverted)
        else:
            order_major = ['dd', 'd', 'm', 'M', 'A', 'AA']
            # TODO: add out of range exception
            return Interval(number=self.number, quality=order_major[order_major.index(self.quality) + 1], inverted=self.inverted)

    def diminish(self):
        if self.is_potentially_perfect():
            order_perfect = ['dd', 'd', 'P', 'A', 'AA']
            # TODO: add out of range exception
            return Interval(number=self.number, quality=order_perfect[order_perfect.index(self.quality) - 1], inverted=self.inverted)
        else:
            order_major = ['dd', 'd', 'm', 'M', 'A', 'AA']
            # TODO: add out of range exception
            return Interval(number=self.number, quality=order_major[order_major.index(self.quality) - 1], inverted=self.inverted)
    
    def fundamental(self):
        number = self.number
        while number > 7:
            number -= 7
        return Interval(number=number, quality=self.quality, inverted=self.inverted)

    def invert(self):
        return Interval(number=self.number, quality=self.quality, inverted=~self.inverted)

    def __str__(self):
        return self.quality + str(self.number)
    
    def __eq__(self, other):
        return self.get_semitones() == other.get_semitones()

    def __neg__(self):
        return self.invert()

    def get_semitones(self):
        number = self.number
        semitones = 0
        while number > 7:
            number -= 7
            semitones += 12

        semitones += { 1: 0, 2: 2, 3: 4, 4: 5, 5: 7, 6: 9, 7: 11 }[number]

        order_perfect = ['dd', 'd', 'P', 'A', 'AA']
        order_major = ['dd', 'd', 'm', 'M', 'A', 'AA']
        semitones_map = {
            1: { q: s for q, s in zip(order_perfect, range(-2, 3)) },
            2: { q: s for q, s in zip(order_major, range(-3, 3)) },
            3: { q: s for q, s in zip(order_major, range(-3, 3)) },
            4: { q: s for q, s in zip(order_perfect, range(-2, 3)) },
            5: { q: s for q, s in zip(order_perfect, range(-2, 3)) },
            6: { q: s for q, s in zip(order_major, range(-3, 3)) },
            7: { q: s for q, s in zip(order_major, range(-3, 3)) },
        }

        semitones += semitones_map[number][self.quality]
        
        return semitones

    @staticmethod
    def get_quality(number, halves):
        while number > 7:
            number -= 7
            halves -= 2

        order_perfect = ['dd', 'd', 'P', 'A', 'AA']
        order_major = ['dd', 'd', 'm', 'M', 'A', 'AA']
        quality_map = {
            1: { h: q for q, h in zip(list(reversed(order_perfect)), range(-2, 3)) },
            2: { h: q for q, h in zip(list(reversed(order_major)), range(-2, 4)) },
            3: { h: q for q, h in zip(list(reversed(order_major)), range(-2, 4)) },
            4: { h: q for q, h in zip(list(reversed(order_perfect)), range(-1, 4)) },
            5: { h: q for q, h in zip(list(reversed(order_perfect)), range(-1, 4)) },
            6: { h: q for q, h in zip(list(reversed(order_major)), range(-1, 5)) },
            7: { h: q for q, h in zip(list(reversed(order_major)), range(-1, 5)) },
        }

        # TODO: add out of range exception
        return quality_map[number][halves]


class Note:
    def __init__(self, notation=None, octave=None, tone=None, semitones=None):
        if notation:
            # TODO: add notation syntax check
            octave = int(re.sub('[^0-9]', '', notation))
            tone = re.sub('[^A-G]', '', notation)
            semitones = notation.count('#') + 2 * notation.count('x') - notation.count('b')
        
        self.octave = octave
        self.tone = tone
        self.semitones = semitones if semitones else 0
    
    def replace(self, notation=None, octave=None, tone=None, semitones=None):
        return Note(
            notation=notation, 
            octave=self.octave if octave is None else octave, 
            tone=self.tone if tone is None else tone, 
            semitones=self.semitones if semitones is None else semitones, 
        )
    
    def sharp(self):
        return Note(octave=self.octave, tone=self.tone, semitones=self.semitones + 1)

    def flat(self):
        return Note(octave=self.octave, tone=self.tone, semitones=self.semitones - 1)

    def add_octave(self, diff):
        return Note(octave=self.octave + diff, tone=self.tone, semitones=self.semitones)

    def midi_number(self):
        return Note._tone_to_midi_number(self.tone) + self.semitones + self.octave * 12

    def __sub__(self, other):
        if isinstance(other, Note):
            tone_index_a = Note._tone_to_index(self.tone) + self.octave * 7
            tone_index_b = Note._tone_to_index(other.tone) + other.octave * 7
            number = tone_index_a - tone_index_b + 1

            midi_number_a = self.midi_number()
            midi_number_b = other.midi_number()
            halves = (number - 1) * 2 - (midi_number_a - midi_number_b)

            return Interval(number=number, quality=Interval.get_quality(number, halves))

        elif isinstance(other, Interval):
            return self + (-other)

        else:
            raise ValueError('Subtraction is supported only between notes')

    def __add__(self, other):
        if isinstance(other, Interval):
            if not other.inverted:
                tone_index_self = Note._tone_to_index(self.tone) + self.octave * 7
                tone_index_other = other.number - 1
                tone_index_result = tone_index_self + tone_index_other
                tone_result = Note._index_to_tone(tone_index_result)
                octave_result = tone_index_result // 7

                note_neutral = Note(octave=octave_result, tone=tone_result, semitones=0)
                semitones_interval = other.get_semitones()
                semitones_neutral = note_neutral.midi_number() - self.midi_number()

                return Note(octave=octave_result, tone=tone_result, semitones=semitones_interval - semitones_neutral)
            
            else:
                tone_index_self = Note._tone_to_index(self.tone) + self.octave * 7
                tone_index_other = other.number - 1
                tone_index_result = tone_index_self - tone_index_other
                tone_result = Note._index_to_tone(tone_index_result)
                octave_result = tone_index_result // 7

                note_neutral = Note(octave=octave_result, tone=tone_result, semitones=0)
                semitones_interval = other.get_semitones()
                semitones_neutral = note_neutral.midi_number() - self.midi_number()

                return Note(octave=octave_result, tone=tone_result, semitones=-(semitones_interval + semitones_neutral))

        else:
            raise ValueError('Need to add Interval and Note')
    
    def __radd__(self, other):
        return self.__add__(other)

    def __eq__(self, other):
        return self.midi_number() == other.midi_number()

    def __str__(self):
        return self.tone + Note._semitone_notation(self.semitones) + str(self.octave)

    def __lt__(self, other):
        return self.midi_number() < other.midi_number()
    
    def __le__(self, other):
        return self.midi_number() <= other.midi_number()
    
    def __gt__(self, other):
        return self.midi_number() > other.midi_number()

    def __ge__(self, other):
        return self.midi_number() >= other.midi_number()

    @staticmethod
    def _tone_to_midi_number(tone):
        numbers = { 'C': 12, 'D': 14, 'E': 16, 'F': 17, 'G': 19, 'A': 21, 'B': 23 }
        return numbers[tone]

    @staticmethod
    def _tone_to_index(tone):
        tone_map = { tone: num for num, tone in enumerate(['C', 'D', 'E', 'F', 'G', 'A', 'B']) }
        return tone_map[tone]

    @staticmethod
    def _index_to_tone(index):
        return ['C', 'D', 'E', 'F', 'G', 'A', 'B'][index % 7]

    @staticmethod
    def _semitone_notation(semitones):
        return { 3: '#x', 2: 'x', 1: '#', 0: '', -1: 'b', -2: 'bb', -3: 'bbb' }[semitones]


from .utils import length_notation


class Chord:
    def __init__(self, base, *args):
        self.base = base
        self.tags = args

    def to_lilypond(self, length):
        tag_map = {
            '7': '7',
            'M7': 'M7',
            'minor': 'm',
            'diminished': 'dim',
        }
        # TODO: more tag represetation
        tag_string = ''.join((tag_map.get(t, '') for t in self.tags))
        return self.base.lower() + length_notation(length) + ((':' + tag_string) if tag_string else '')

    def to_notes(self, octave=4):
        result = { 1: Note(octave=octave, tone=self.base) }

        if 'major' in self.tags:
            result[3] = result[1] + Interval('M3')
            result[5] = result[1] + Interval('P5')
        
        if 'minor' in self.tags:
            result[3] = result[1] + Interval('m3')
            result[5] = result[1] + Interval('P5')

        if 'augumented' in self.tags:
            result[3] = result[1] + Interval('M3')
            result[5] = result[1] + Interval('A5')
        
        if 'diminished' in self.tags:
            result[3] = result[1] + Interval('m3')
            result[5] = result[1] + Interval('d5')
        
        if '7' in self.tags:
            result[7] = result[1] + Interval('m7')
        
        if '7major' in self.tags:
            result[7] = result[1] + Interval('M7')
        
        if 'b5' in self.tags:
            result[5] = result[1] + Interval('d5')
        
        if 'sus2' in self.tags:
            del result[3]
            result[2] = result[1] + Interval('M2')
        
        if 'sus4' in self.tags:
            del result[3]
            result[4] = result[1] + Interval('P4')
        
        return tuple([result[k] for k in sorted(result.keys())])

    @staticmethod
    def from_notation(notation):
        symbol_map = {
            'm': 'minor', 'min': 'minor', '-': 'minor',
            'M': 'major', 'Ma': 'major', 'Maj': 'major', 'maj': 'major',
            '+': 'augumented', 'aug': 'augumented',
            'o': 'diminished', 'dim': 'diminished',
            'sus2': 'sus2', 'sus4': 'sus4',
            '7': '7', 'dom': '7',
            'M7': '7major', 'maj7': '7major',
            'b5': 'b5',
        }
        symbols = [re.escape(sym) for sym in reversed(sorted(symbol_map.keys()))]
        base = notation[0]
        matched = re.findall('{}'.format('|'.join(symbols)), notation[1:])
        
        # TODO: add chord notation syntax check
        tags = set()
        for sym in matched:
            tags.add(symbol_map[sym])
        
        if 'major' not in tags and ('minor' not in tags and 'augumented' not in tags and 'diminished' not in tags):
            tags.add('major')
        
        return Chord(base, *tags)
    
    @staticmethod
    def from_notes(notes):
        tags = set()

        if notes[1] - notes[0] == Interval('M3') and notes[2] - notes[0] == Interval('P5'):
            tags.add('major')
        elif notes[1] - notes[0] == Interval('m3') and notes[2] - notes[0] == Interval('P5'):
            tags.add('minor')
        elif notes[1] - notes[0] == Interval('M3') and notes[2] - notes[0] == Interval('A5'):
            tags.add('augumented')
        elif notes[1] - notes[0] == Interval('m3') and notes[2] - notes[0] == Interval('d5'):
            tags.add('diminished')
        else:
            raise ValueError('Unparsable notes')
        
        if len(notes) >= 4:
            if notes[3] - notes[0] == Interval('M7'):
                tags.add('7major')
            elif notes[3] - notes[0] == Interval('m7'):
                tags.add('7')
        
        return Chord(notes[0].tone, *tags)

        # TODO: do full support on note conversion


def chord(notation, octave=4):
    return Chord.from_notation(notation).to_notes(octave=octave)


# def chord_to_notation(c):
    



class Scale:

    transitions = {}

    def __init__(self, tonic=None):
        # TODO: check quality syntax
        self.tonic = tonic

    def number_to_int(self, number):
        if number[0:3] == 'v7/':
            number = number[3:]
            return ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii'].index(number.lower()) + 6
        else:
            number = self._sanitize_seventh(number)
            return ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii'].index(number.lower()) + 1

    def note(self, number):
        if isinstance(number, str):
            index = self.number_to_int(number)
        elif isinstance(number, int):
            index = number
        else:
            raise ValueError('Int or string are supported')
        note = self.tonic
        while index > 7:
            index -= 7
            note += Interval('P8')

        note += self.note_interval(index)

        return note

    def note_interval(self, index):
        return None

    def diatonic(self, number, include_seventh=False):
        index = self.number_to_int(number)
        if include_seventh:
            return (self.note(index), self.note(index + 2), self.note(index + 4), self.note(index + 6))
        else:
            return (self.note(index), self.note(index + 2), self.note(index + 4))
    
    def secondary_dominant(self, number, extend=0):
        index = self.number_to_int(number)
        base = self.note(index) + Interval('P5')
        for _ in range(extend):
            base += Interval('P5')
        return chord(base.tone + '7', octave=self.tonic.octave)

    def chord_canonical(self, number):
        return Chord.from_notes(self.chord(number))

    def chord(self, number):
        number = number.lower()
        if re.match(r'^(vii|iii|iv|vi|ii|i|v)(7)?$', number):
            base_num, seventh = re.match(r'(vii|iii|iv|vi|ii|i|v)(7)?', number).groups()
            return self.diatonic(base_num, include_seventh=(True if seventh else False))
        elif re.match(r'^v7/(vii|iii|iv|vi|ii|i|v)$', number):
            base_num = re.match(r'v7/(vii|iii|iv|vi|ii|i|v)', number).groups()
            return self.secondary_dominant(number)
        else:
            raise ValueError('No matching chord like "{}"'.format(number))

    def available_tension_note_primary(self, number):
        return None
    
    def available_tension_note_secondary(self, number):
        return None

    def available_tension_note(self, number):
        return self.available_tension_note_primary(number) + self.available_tension_note_secondary(number)

    def possible_numbers(self):
        return None
    
    def possible_cadences(self):
        return None
    
    def _sanitize_seventh(self, c):
        if c[-1] == '7':
            return c[:-1]
        return c

    def is_transitable(self, a, b):
        a = self._sanitize_seventh(a)
        b = self._sanitize_seventh(b)
        if a[:3] == 'v7/':
            return a[3:] == b or a == b
        elif b[:3] == 'v7/':
            return b[3:] in self.transitions[a]
        else:
            return b in self.transitions[a]
        

class MajorScale(Scale):

    transitions = {
        'i': ['i', 'iii',  'vi', 'ii', 'iv', 'v'],
        'ii': ['ii', 'iii', 'v'],
        'iii': ['iii', 'vi','ii', 'iv'],
        'iv': ['iv', 'i', 'iii',  'ii', 'v'],
        'v': ['v', 'i', 'iii',  'vi'],
        'vi': ['vi', 'iii', 'ii', 'iv'],
    }

    def note_interval(self, index):
        return {
            1: Interval('P1'),
            2: Interval('M2'),
            3: Interval('M3'),
            4: Interval('P4'),
            5: Interval('P5'),
            6: Interval('M6'),
            7: Interval('M7'),
        }[index]

    def available_tension_note_primary(self, number):
        number = number.lower()
        if number[-1] == '7':
            number = number[:-1]
        intervals_map = {
            'i': [Interval('M9'), Interval('M13')],
            'ii': [Interval('M9'), Interval('P11')],
            'iii': [Interval('P11')],
            'iv': [Interval('M9'), Interval('A11'), Interval('M13')],
            'v': [Interval('M9'), Interval('M13')],
            'vi': [Interval('M9'), Interval('P11')],
            'vii': [Interval('P11'), Interval('m13')],
            'v7/ii': [Interval('m9'), Interval('M9'), Interval('A9'), Interval('m13')],
            'v7/iii': [Interval('m9'), Interval('A9'), Interval('m13')],
            'v7/iv': [Interval('M9'), Interval('M13')],
            'v7/v': [Interval('M9'), Interval('M13')],
            'v7/vi': [Interval('m9'), Interval('A9'), Interval('m13')],
        }
        base = self.note(number)
        return [base + intv for intv in intervals_map[number]]
    
    def available_tension_note_secondary(self, number):
        number = number.lower()
        if number[-1] == '7':
            number = number[:-1]
        intervals_map = {
            'i': [Interval('A11')],
            'ii': [],
            'iii': [Interval('M9')],
            'iv': [],
            'v': [Interval('m9'), Interval('A9'), Interval('A11'), Interval('m13')],
            'vi': [Interval('M13')],
            'vii': [],
            'v7/ii': [Interval('A11'), Interval('M13')],
            'v7/iii': [Interval('A11')],
            'v7/iv': [Interval('m9'), Interval('A9'), Interval('A11'), Interval('m13')],
            'v7/v': [Interval('m9'), Interval('A9'), Interval('A11'), Interval('m13')],
            'v7/vi': [Interval('M9'), Interval('A11')],
        }
        base = self.note(number)
        return [base + intv for intv in intervals_map[number]]
    
    def possible_numbers(self):
        return ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'v7/ii', 'v7/iii', 'v7/iv', 'v7/v', 'v7/vi']
    
    def possible_cadences(self):
        return ['i', 'v']


class SimpleMajorScale(MajorScale):

    transitions = {
        'i': ['i', 'iv', 'v'],
        'iv': ['i', 'iv', 'v'],
        'v': ['i', 'iv', 'v'],
    }

    def possible_numbers(self):
        return ['i', 'iv', 'v']


class NaturalMinorScale(Scale):

    transitions = {
        'i': ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii'],
        'ii': ['ii', 'iii', 'v'],
        'iii': ['i', 'ii', 'iii', 'iv', 'vi'],
        'iv': ['i', 'ii', 'iv', 'v', 'vii'],
        'v': ['i', 'iii', 'v', 'vi'],
        'vi': ['ii', 'iv', 'v', 'vi', 'vii'],
        'vii': ['i', 'iii', 'v', 'vi', 'vii']
    }

    def note_interval(self, index):
        return {
            1: Interval('P1'),
            2: Interval('M2'),
            3: Interval('m3'),
            4: Interval('P4'),
            5: Interval('P5'),
            6: Interval('m6'),
            7: Interval('m7'),
        }[index]

    def diatonic(self, number, include_seventh=False):
        if number == 'v':
            return (self.note(5), self.note(7).sharp(), self.note(9))
        else:
            return super(NaturalMinorScale, self).diatonic(number, include_seventh=include_seventh)

    def available_tension_note_primary(self, number):
        number = number.lower()
        intervals_map = {
            'i': [Interval('M9'), Interval('P11')],
            'ii': [Interval('P11'), Interval('m13')],
            'iii': [Interval('M9'), Interval('M13')],
            'iv': [Interval('M9'), Interval('P11'), Interval('M13')],
            'v': [Interval('m9'), Interval('A9'), Interval('m13')],
            'vi': [Interval('M9'), Interval('A9'), Interval('M13')],
            'vii': [Interval('M9'), Interval('M13')],
            'v7/iii': [Interval('M9'), Interval('M13')],
            'v7/iv': [Interval('m9'), Interval('M9'), Interval('A9'), Interval('m13')],
            'v7/v': [Interval('m9'), Interval('A9'), Interval('m13')],
            'v7/vi': [Interval('M9'), Interval('M13')],
            'v7/vii': [Interval('M9'), Interval('A9'), Interval('M13')],
        }
        base = self.note(number)
        return [base + intv for intv in intervals_map[number]]
    
    def available_tension_note_secondary(self, number):
        number = number.lower()
        intervals_map = {
            'i': [Interval('M13')],
            'ii': [],
            'iii': [Interval('A11')],
            'iv': [],
            'v': [Interval('M9'), Interval('A11')],
            'vi': [],
            'vii': [],
            'v7/iii': [Interval('m9'), Interval('A11'), Interval('m13')],
            'v7/iv': [Interval('A11'), Interval('M13')],
            'v7/v': [Interval('A11')],
            'v7/vi': [Interval('m9'), Interval('A11'), Interval('m13')],
            'v7/vii': [Interval('m9'), Interval('A9'), Interval('m13')],
        }
        base = self.note(number)
        return [base + intv for intv in intervals_map[number]]
    
    def possible_numbers(self):
        return ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'v7/iii', 'v7/iv', 'v7/v', 'v7/vi', 'v7/vii']
    
    def possible_cadences(self):
        return ['i', 'v']

    
if __name__ == '__main__':
    import unittest

    class TestNoteClass(unittest.TestCase):

        def test_equality(self):
            cases = [
                ('C#5', 'Db5', True),
                ('D#5', 'Eb5', True),
                ('C5', 'C6', False),
                ('C#5', 'C5', False),
            ]
            for a, b, truth in cases:
                if truth:
                    self.assertEqual(Note(a), Note(b))
                else:
                    self.assertNotEqual(Note(a), Note(b))

        def test_parse(self):
            cases = ['Bb4', 'C#5', 'C#x5', 'Ex5', 'Fbb4', 'Abbb0']
            for note in cases:
                self.assertEqual(str(Note(note)), note)

        def test_sub(self):
            cases = [
                ('D5', 'Bb4', 'M3'),
                ('D#6', 'F5', 'A6'),
                ('D6', 'E5', 'm7'),
                ('Fb5', 'Ab4', 'm6'),
                ('G6', 'A#5', 'd7'),
                ('Ab5', 'D#5', 'dd5'),
            ]
            for top, base, interval in cases:
                self.assertEqual(str(Note(top) - Note(base)), interval)
        
        def test_add(self):
            cases = [
                ('D5', 'Bb4', 'M3'),
                ('D#6', 'F5', 'A6'),
                ('D6', 'E5', 'm7'),
                ('Fb5', 'Ab4', 'm6'),
                ('G6', 'A#5', 'd7'),
                ('Ab5', 'D#5', 'dd5'),
            ]
            for top, base, interval in cases:
                self.assertEqual(str(Note(base) + Interval(interval)), str(Note(top)))
    

    class TestChordFunction(unittest.TestCase):

        def test_chord(self):
            cases = [
                ('C', 5, (Note('C5'), Note('E5'), Note('G5'))),
                ('Cmaj', 5, (Note('C5'), Note('E5'), Note('G5'))),
                ('Cm', 5, (Note('C5'), Note('Eb5'), Note('G5'))),
                ('C-', 5, (Note('C5'), Note('Eb5'), Note('G5'))),
                ('Caug', 5, (Note('C5'), Note('E5'), Note('G#5'))),
                ('C+', 5, (Note('C5'), Note('E5'), Note('G#5'))),
                ('Cdim', 5, (Note('C5'), Note('Eb5'), Note('Gb5'))),
                ('Co', 5, (Note('C5'), Note('Eb5'), Note('Gb5'))),
                ('C7', 5, (Note('C5'), Note('E5'), Note('G5'), Note('Bb5'))),
                ('Cdom', 5, (Note('C5'), Note('E5'), Note('G5'), Note('Bb5'))),
                ('CM7', 5, (Note('C5'), Note('E5'), Note('G5'), Note('B5'))),
                ('Csus2', 5, (Note('C5'), Note('D5'), Note('G5'))),
                ('Csus4', 5, (Note('C5'), Note('F5'), Note('G5'))),
                ('Cdim7', 5, (Note('C5'), Note('Eb5'), Note('Gb5'), Note('Bb5'))),
                ('Cdimsus4M7', 5, (Note('C5'), Note('F5'), Note('Gb5'), Note('B5'))),
            ]
            for c, octave, notes in cases:
                self.assertEqual(chord(c, octave=octave), notes)


    unittest.main()
