"""Module for generating hex LUTs"""

import sys
from decimal import Decimal
from assembler.machine import MachineCode, machine_code
from assembler.formatter import format_bytes
from assembler.assembler import Visitor


def decimal_to_segments(value: 'int|None') -> 'int':
    if value is None:
        return 0

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


def gen_output(**_) -> 'list[int]':

    output = [0 for _ in range(1024)]

    for i in range(256):
        dec = Decimal(i)
        digits = dec.as_tuple().digits
        digits = [None for _ in range(4 - len(digits))] + list(digits)

        for place, digit in enumerate(digits):
            address = (place << 8) | i
            output[address] = decimal_to_segments(digit)

    return output


def gen_instructions(**_) -> 'list[int]':

    instruction_dict = {}

    for instruction in machine_code:
        instruction_dict.update(instruction.fill_addresses())

    return [instruction_dict[i] for i in range(2**MachineCode.total_bits())]


def gen_program(**kwargs) -> 'list[int]':
    path = kwargs.pop('path')

    visitor = Visitor()
    visitor.parse(path, 16)
    return visitor.program


def gen_lut(generator: 'callable', width: 'int') -> 'str':
    return format_bytes(generator(), width)


lut_methods = {
    'instructions': (gen_instructions, 2),
    'output': (gen_output, 1),
    'program': (gen_program, 1),
}

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='hex LUT generation tool')
    parser.add_argument('LUT', type=str, help='LUT type', choices=['instructions', 'output', 'program'])
    parser.add_argument('-o', type=str, help='output file')
    parser.add_argument('-p', '--program', type=str, help='assembly file for program LUT generation')

    args = parser.parse_args()

    lut_tuple = lut_methods[args.LUT]
    lut = format_bytes(lut_tuple[0](path=args.program), lut_tuple[1])

    if args.o:
        with open(args.o, 'w') as file:
            file.write(lut + '\n')
    else:
        print(lut)
