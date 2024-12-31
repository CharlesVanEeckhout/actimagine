
class VLC:
    def __init__(self, bits, codes):
        self.bit_strings = []
        
        for (b, c) in zip(bits, codes, strict=True):
            bit_string = ("{:0" + str(b) + "b}").format(c)
            if len(bit_string) != b:
                bit_string = bit_string[len(bit_string)-b:]
            self.bit_strings.append(bit_string)
    
    def find_bit_string(self, bit_string):
        return [bs for bs in enumerate(self.bit_strings) if bs[1].startswith(bit_string)]


coeff_token_len = [
    [
         1, 0, 0, 0,
         6, 2, 0, 0,     8, 6, 3, 0,     9, 8, 7, 5,    10, 9, 8, 6,
        11,10, 9, 7,    13,11,10, 8,    13,13,11, 9,    13,13,13,10,
        14,14,13,11,    14,14,14,13,    15,15,14,14,    15,15,15,14,
        16,15,15,15,    16,16,16,15,    16,16,16,16,    16,16,16,16
    ],
    [
         2, 0, 0, 0,
         6, 2, 0, 0,     6, 5, 3, 0,     7, 6, 6, 4,     8, 6, 6, 4,
         8, 7, 7, 5,     9, 8, 8, 6,    11, 9, 9, 6,    11,11,11, 7,
        12,11,11, 9,    12,12,12,11,    12,12,12,11,    13,13,13,12,
        13,13,13,13,    13,14,13,13,    14,14,14,13,    14,14,14,14,
    ],
    [
         4, 0, 0, 0,
         6, 4, 0, 0,     6, 5, 4, 0,     6, 5, 5, 4,     7, 5, 5, 4,
         7, 5, 5, 4,     7, 6, 6, 4,     7, 6, 6, 4,     8, 7, 7, 5,
         8, 8, 7, 6,     9, 8, 8, 7,     9, 9, 8, 8,     9, 9, 9, 8,
        10, 9, 9, 9,    10,10,10,10,    10,10,10,10,    10,10,10,10,
    ],
    [
         6, 0, 0, 0,
         6, 6, 0, 0,     6, 6, 6, 0,     6, 6, 6, 6,     6, 6, 6, 6,
         6, 6, 6, 6,     6, 6, 6, 6,     6, 6, 6, 6,     6, 6, 6, 6,
         6, 6, 6, 6,     6, 6, 6, 6,     6, 6, 6, 6,     6, 6, 6, 6,
         6, 6, 6, 6,     6, 6, 6, 6,     6, 6, 6, 6,     6, 6, 6, 6,
    ]
]

coeff_token_bits = [
    [
         1, 0, 0, 0,
         5, 1, 0, 0,     7, 4, 1, 0,     7, 6, 5, 3,     7, 6, 5, 3,
         7, 6, 5, 4,    15, 6, 5, 4,    11,14, 5, 4,     8,10,13, 4,
        15,14, 9, 4,    11,10,13,12,    15,14, 9,12,    11,10,13, 8,
        15, 1, 9,12,    11,14,13, 8,     7,10, 9,12,     4, 6, 5, 8,
    ],
    [
         3, 0, 0, 0,
        11, 2, 0, 0,     7, 7, 3, 0,     7,10, 9, 5,     7, 6, 5, 4,
         4, 6, 5, 6,     7, 6, 5, 8,    15, 6, 5, 4,    11,14,13, 4,
        15,10, 9, 4,    11,14,13,12,     8,10, 9, 8,    15,14,13,12,
        11,10, 9,12,     7,11, 6, 8,     9, 8,10, 1,     7, 6, 5, 4,
    ],
    [
        15, 0, 0, 0,
        15,14, 0, 0,    11,15,13, 0,     8,12,14,12,    15,10,11,11,
        11, 8, 9,10,     9,14,13, 9,     8,10, 9, 8,    15,14,13,13,
        11,14,10,12,    15,10,13,12,    11,14, 9,12,     8,10,13, 8,
        13, 7, 9,12,     9,12,11,10,     5, 8, 7, 6,     1, 4, 3, 2,
    ],
    [
         3, 0, 0, 0,
         0, 1, 0, 0,     4, 5, 6, 0,     8, 9,10,11,    12,13,14,15,
        16,17,18,19,    20,21,22,23,    24,25,26,27,    28,29,30,31,
        32,33,34,35,    36,37,38,39,    40,41,42,43,    44,45,46,47,
        48,49,50,51,    52,53,54,55,    56,57,58,59,    60,61,62,63,
    ]
]

coeff_token_vlc = []
for (l, b) in zip(coeff_token_len, coeff_token_bits, strict=True):
    coeff_token_vlc.append(VLC(l, b))


total_zeros_len = [
    [1,3,3,4,4,5,5,6,6,7,7,8,8,9,9,9],
    [3,3,3,3,3,4,4,4,4,5,5,6,6,6,6],
    [4,3,3,3,4,4,3,3,4,5,5,6,5,6],
    [5,3,4,4,3,3,3,4,3,4,5,5,5],
    [4,4,4,3,3,3,3,3,4,5,4,5],
    [6,5,3,3,3,3,3,3,4,3,6],
    [6,5,3,3,3,2,3,4,3,6],
    [6,4,5,3,2,2,3,3,6],
    [6,6,4,2,2,3,2,5],
    [5,5,3,2,2,2,4],
    [4,4,3,3,1,3],
    [4,4,2,1,3],
    [3,3,1,2],
    [2,2,1],
    [1,1]
]

total_zeros_bits = [
    [1,3,2,3,2,3,2,3,2,3,2,3,2,3,2,1],
    [7,6,5,4,3,5,4,3,2,3,2,3,2,1,0],
    [5,7,6,5,4,3,4,3,2,3,2,1,1,0],
    [3,7,5,4,6,5,4,3,3,2,2,1,0],
    [5,4,3,7,6,5,4,3,2,1,1,0],
    [1,1,7,6,5,4,3,2,1,1,0],
    [1,1,5,4,3,3,2,1,1,0],
    [1,1,1,3,3,2,2,1,0],
    [1,0,1,3,2,1,1,1],
    [1,0,1,3,2,1,1],
    [0,1,1,2,1,3],
    [0,1,1,1,1],
    [0,1,1,1],
    [0,1,1],
    [0,1]
]

total_zeros_vlc = []
for (l, b) in zip(total_zeros_len, total_zeros_bits, strict=True):
    total_zeros_vlc.append(VLC(l, b))


run_len = [
    [1,1],
    [1,2,2],
    [2,2,2,2],
    [2,2,2,3,3],
    [2,2,3,3,3,3],
    [2,3,3,3,3,3,3]
]
run7_len = [3,3,3,3,3,3,3,4,5,6,7,8,9,10,11]

run_bits = [
    [1,0],
    [1,1,0],
    [3,2,1,0],
    [3,2,1,1,0],
    [3,2,3,2,1,0],
    [3,0,1,3,2,5,4]
]
run7_bits = [7,6,5,4,3,2,1,1,1,1,1,1,1,1,1]


run_vlc = []
for (l, b) in zip(run_len, run_bits, strict=True):
    run_vlc.append(VLC(l, b))
run7_vlc = VLC(run7_len, run7_bits)

