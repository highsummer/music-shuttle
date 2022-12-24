from note import chord
from singable import MultiKey, Key, Enumerate, Parallel, AtChannel, Transpose, Amplify, Arpeggio, Repeat, Reharmonize
from note import Note, Interval, MajorScale, NaturalMinorScale
from songs import crepas_scale as scale
from songs import crepas_song as song


song = Parallel()([
    AtChannel(0)(song),
    AtChannel(1)(
        # Transpose(Interval('-P15'))(progression)
        Arpeggio()(
            (
                Transpose(Interval('-P15'))(
                    Reharmonize(scale)(song)
                ),
                Repeat(16)(
                    Enumerate()([
                        Key(length=1/2, note=Note('C4')),
                        Key(length=1/2, note=Note('C##4')),
                        Key(length=1/2, note=Note('C#4')),
                        Key(length=1/2, note=Note('C##4')),
                        Key(length=1/2, note=Note('C4')),
                        Key(length=1/2, note=Note('C##4')),
                        Key(length=1/2, note=Note('C#4')),
                        Key(length=1/2, note=Note('C##4')),
                    ])
                )
            )
        )
    )
])

from instruments.ensemble import string_ensemble_1
from instruments.piano import acoustic_grand_piano
from instruments.bass import synth_bass_1
from instruments.drum_kits import standard_drum_kit

from singable import to_lilypond

s = to_lilypond(song, clefs={1: 'bass'})
with open('untitled.ly', 'w') as f:
    f.write(s)

import os
os.system('lilypond untitled.ly')

from singable import to_midi

mid = to_midi(song, instruments={ 
    0: acoustic_grand_piano,
    1: acoustic_grand_piano,
    2: synth_bass_1,
    9: standard_drum_kit
})
mid.save('new_song.mid')

import os
import subprocess
FNULL = open(os.devnull, 'w')
subprocess.call(['timidity', 'new_song.mid'], stdout=FNULL, stderr=subprocess.STDOUT)

# import mido
# port = mido.open_output()
# for msg in mid.play():
#     port.send(msg)