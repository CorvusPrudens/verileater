"""Module for generating hex LUTs"""

def format_bytes(data: 'list[int]', width: 'int') -> 'str':

    formatter = f'{{ :0{width * 8}X }}'

    lines = []
    for i in range(0, len(data), 8):
        lines.append(' '.join([formatter.format(v) for v in formatter[i:i+8]]))
    
    return '\n'.join(lines)


def gen_instructions() -> 'list[int]':
    return []


def decimal_to_segments(value: 'int') -> 'int':
    # {P, G, F, E, D, C, B, A}

    dec_to_segs = {
        0: 0b00111111,
        1: 0b00000110,
        2: 0b01011011,
        3: 0b01001111,
        4: 0b01100110,
        5: 0b01011011,
        6: 0b01111101,
        7: 0b00000111,
        8: 0b01111111,
        9: 0b01101111,
    }

    return dec_to_segs[value]


def gen_output() -> 'list[int]':
    return []


def gen_lut(generator: 'callable', width: 'int') -> 'str':
    return format_bytes(generator(), width)


lut_methods = {
    'instructions': gen_lut(gen_instructions, 2),
    'output': gen_lut(gen_output, 1),
}

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser('hex LUT generation tool')
    parser.add_argument('LUT', type=str, help='LUT type', choices=['instructions', 'output'])
    parser.add_argument('-o', type=str, help='Output file')

    args = parser.parse_args()

    lut = lut_methods[args.LUT]()

    if args.o:
        with open(args.o, 'w') as file:
            file.write(lut + '\n')
    else:
        print(lut)
