from reharmonize import reharmonize
from shlex import split
from note import Note
from singable import Key, Enumerate
from collections import defaultdict

class state:
    melody = [
        Key(length=1, note=Note('B4')),
        Key(length=1, note=Note('G4')),
        Key(length=1, note=Note('E4')),
        Key(length=1, note=Note('B4')),
        Key(length=1/2, note=Note('C5')),
        Key(length=1/2, note=Note('C5')),
        Key(length=1/2, note=Note('C5')),
        Key(length=1/2, note=Note('B4')),
        Key(length=2, note=Note('A4')),
        Key(length=1, note=Note('A4')),
        Key(length=1, note=Note('F#4')),
        Key(length=1, note=Note('D4')),
        Key(length=1, note=Note('A4')),
        Key(length=1/2, note=Note('B4')),
        Key(length=1/2, note=Note('B4')),
        Key(length=1/2, note=Note('B4')),
        Key(length=1/2, note=Note('A4')),
        Key(length=2, note=Note('G4')),
        Key(length=1, note=Note('B4')),
        Key(length=1, note=Note('G4')),
        Key(length=1, note=Note('E4')),
        Key(length=1, note=Note('B4')),
        Key(length=1/2, note=Note('C5')),
        Key(length=1/2, note=Note('C5')),
        Key(length=1/2, note=Note('C5')),
        Key(length=1/2, note=Note('B4')),
        Key(length=2, note=Note('A4')),
        Key(length=1/2, note=Note('B4')),
        Key(length=1/2, note=Note('E5')),
        Key(length=1/2, note=Note('G5')),
        Key(length=1/2, note=Note('E5')),
        Key(length=1/2, note=Note('D#5')),
        Key(length=1, note=Note('D#5')),
        Key(length=1/2, note=Note('D#5')),
        Key(length=1, note=Note('E5')),
        Key(length=1, note=Note('D#5')),
        Key(length=1, note=Note('E5')),
        Key(length=1/2, note=Note('E5')),
        Key(length=1/2, note=Note('D5')),
        Key(length=2, note=Note('C5')),
        Key(length=1/2, note=Note('C5')),
        Key(length=1/2, note=Note('C5')),
        Key(length=1/2, note=Note('C5')),
        Key(length=1/2, note=Note('B4')),
        Key(length=3, note=Note('A4')),
        Key(length=1/2, note=Note('A4')),
        Key(length=1/2, note=Note('A4')),
        Key(length=3/2, note=Note('D5')),
        Key(length=1/2, note=Note('E5')),
        Key(length=3/2, note=Note('D5')),
        Key(length=1/2, note=Note('C5')),
        Key(length=1/2, note=Note('B4')),
        Key(length=1/2, note=Note('B4')),
        Key(length=1/2, note=Note('B4')),
        Key(length=1/2, note=Note('A4')),
        Key(length=1, note=Note('B4')),
        Key(length=1/2, note=Note('E5')),
        Key(length=1/2, note=Note('D5')),
        Key(length=3/2, note=Note('C5')),
        Key(length=1/2, note=Note('C5')),
        Key(length=1/2, note=None),
        Key(length=1/2, note=Note('C5')),
        Key(length=1/2, note=Note('C5')),
        Key(length=1/2, note=Note('B4')),
        Key(length=4, note=Note('A4')),
        Key(length=1/2, note=Note('B4')),
        Key(length=1/2, note=Note('E5')),
        Key(length=1/2, note=Note('G5')),
        Key(length=1/2, note=Note('E5')),
        Key(length=1/2, note=Note('D#5')),
        Key(length=1/2, note=Note('E5')),
        Key(length=1/2, note=Note('F#5')),
        Key(length=1/2, note=Note('D#5')),
        Key(length=1, note=Note('E5')),
        Key(length=1, note=Note('D#5')),
        Key(length=1, note=Note('E5')),
        Key(length=1, note=None),
    ]
    chord = []

def display_state(state, beat_unit=1/2, bar=4, rows_per_line=4):
    units_per_bar = int(bar / beat_unit)
    rows = defaultdict(lambda: [''] * units_per_bar)
    for key in Enumerate()(state.melody).sing():
        col = int((key.start % bar) / beat_unit)
        row = int(key.start / bar)
        if key.note:
            rows[row][col] = str(key.note)
    row_max = max(rows.keys())
    rows_str = [''.join(['{:4}'.format(rep) for rep in rows[row]]) for row in range(row_max + 1)]
    total_str = ''
    for i, row_str in enumerate(rows_str):
        total_str += row_str + '|'
        if (i + 1) % rows_per_line == 0:
            total_str += '\n'
    print(total_str)

while True:
    try:
        command = input('>> ')
        args = split(command)
        if not args:
            continue
        if args[0] == 'display':
            display_state(state)
        elif args[0] == 'append':
            if args[1][0] == 'R':
                note = None
            else:
                note = Note(args[1])
            state.melody.append(Key(length=int(args[2]), note=note))
            display_state(state)
        elif args[0] == 'pop':
            state.melody.pop()

    except Exception as e:
        raise e