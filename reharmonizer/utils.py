def length_notation(length):
    # TODO: allow non-ordinary lengths
    return {
        0.125: '32',
        0.25: '16',
        0.375: '16.',
        0.5: '8',
        0.75: '8.',
        0.875: '8..',
        1: '4',
        1.5: '4.',
        1.75: '4..',
        2: '2',
        3: '2.',
        3.5: '2..',
        4: '1',
    }[length]