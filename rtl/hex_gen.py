"""Module for generating hex LUTs"""

from math import log2
from decimal import Decimal

def format_bytes(data: 'list[int]', width: 'int') -> 'str':

    formatter = f'{{:0{width * 2}X}}'

    lines = []
    for i in range(0, len(data), 8):
        lines.append(' '.join([formatter.format(v) for v in data[i:i+8]]))
    
    return '\n'.join(lines)


AO = 1 << 0
AI = 1 << 1
II = 1 << 2
IO = 1 << 3
RO = 1 << 4
RI = 1 << 5
MI = 1 << 6
HLT = 1 << 7
FI = 1 << 8
J = 1 << 9
CO = 1 << 10
CE = 1 << 11
OI = 1 << 12
BI = 1 << 13
SU = 1 << 14
EO = 1 << 15

class Instruction:

    OPCODE_BITS = 4
    UINSTR_BITS = 3

    class Flag:
        FLAG_BITS = 2
        def __init__(self, flag: 'int'):
            if flag <= 0 or (flag > Instruction.Flag.FLAG_BITS or int(log2(flag)) != log2(flag)):
                raise ValueError(f'Flag (provided {flag}) must be a power of 2 that fits within {Instruction.Flag.FLAG_BITS} bits')
            self.flag = flag
        
        def __eq__(self, other: 'Instruction.Flag') -> 'bool':
            return self.flag == other.flag

    @classmethod
    def total_bits(cls):
        return cls.OPCODE_BITS + cls.UINSTR_BITS + cls.Flag.FLAG_BITS

    def __init__(self, opcode: 'int', uinstructions: 'list[int]|None'=None, flag: 'Instruction.Flag | None'=None, mnemonic: 'str|None'=None):
        if opcode >= 2**Instruction.OPCODE_BITS:
            raise ValueError(f'Opcode must be less than {2**Instruction.OPCODE_BITS}')

        if uinstructions is None:
            uinstructions = []
        
        if len(uinstructions) >= 2**Instruction.UINSTR_BITS - 2:
            raise ValueError(
                f'Too many micro-instructions (expected < {2**Instruction.UINSTR_BITS - 2}, got {len(uinstructions)})')
        
        self.opcode = opcode
        self.uinstructions = uinstructions + [0 for _ in range(2**Instruction.UINSTR_BITS - len(uinstructions))]
        self.flag = flag
        self.mnemonic = mnemonic

    def fill_addresses(self):
        addresses = {}
        for f in range(2**Instruction.Flag.FLAG_BITS):
            op_offset = Instruction.UINSTR_BITS
            flag_offset = Instruction.UINSTR_BITS + Instruction.OPCODE_BITS

            # Every instruction will include the fetch cycle
            fetch_addr = (f << flag_offset) | (self.opcode << op_offset) | 0b000
            addresses[fetch_addr] = CO | MI
            fetch_addr += 1
            addresses[fetch_addr] = RO | II | CE

            for ui in range(2, 2**Instruction.UINSTR_BITS):
                address = (f << flag_offset) | (self.opcode << op_offset) | ui
                if self.flag is None:
                    addresses[address] = self.uinstructions[ui-2]
                else:
                    # NOP when condition is not met
                    try:
                        addresses[address] = self.uinstructions[ui-2] if (self.flag.flag & f) > 0 else 0
                    except ValueError:
                        addresses[address] = 0
        return addresses


def gen_instructions() -> 'list[int]':

    instructions = [
        Instruction(0, flag=None, mnemonic='NOP', uinstructions=[]),
        Instruction(1, flag=None, mnemonic='LDA', uinstructions=[
            IO | MI,
            RO | AI,
        ]),
        Instruction(2, flag=None, mnemonic='STA', uinstructions=[
            IO | MI,
            RI | AO,
        ]),
        Instruction(3, flag=None, mnemonic='LDB', uinstructions=[
            IO | MI,
            RO | BI,
        ]),
        Instruction(4, flag=None, mnemonic='ADI', uinstructions=[
            IO | BI,
            EO | AI,
        ]),
        Instruction(5, flag=None, mnemonic='SBI', uinstructions=[
            IO | BI,
            EO | AI | SU,
        ]),
        Instruction(6, flag=None, mnemonic='ADD', uinstructions=[
            IO | MI,
            RO | BI,
            EO | AI,
        ]),
        Instruction(7, flag=None, mnemonic='SUB', uinstructions=[
            IO | MI,
            RO | BI,
            EO | AI | SU,
        ]),
        Instruction(8, flag=None, mnemonic='OUT', uinstructions=[
            AO | OI,
        ]),
        Instruction(9),
        Instruction(10),
        Instruction(11),
        Instruction(12, flag=None, mnemonic='J', uinstructions=[
            IO | J
        ]),
        Instruction(13, flag=Instruction.Flag(0b01), mnemonic='JC', uinstructions=[
            IO | J
        ]),
        Instruction(14, flag=Instruction.Flag(0b10), mnemonic='JZ', uinstructions=[
            IO | J
        ]),
        Instruction(15, flag=None, mnemonic='HLT', uinstructions=[
            HLT
        ]),
    ]

    instruction_dict = {}

    for instruction in instructions:
        instruction_dict.update(instruction.fill_addresses())

    return [instruction_dict[i] for i in range(2**Instruction.total_bits())]


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


def gen_output() -> 'list[int]':

    output = [0 for _ in range(1024)]

    for i in range(256):
        dec = Decimal(i)
        digits = dec.as_tuple().digits
        digits = [None for _ in range(4 - len(digits))] + list(digits)

        for place, digit in enumerate(digits):
            address = (place << 8) | i
            output[address] = decimal_to_segments(digit)

    return output


def gen_lut(generator: 'callable', width: 'int') -> 'str':
    return format_bytes(generator(), width)


lut_methods = {
    'instructions': gen_lut(gen_instructions, 2),
    'output': gen_lut(gen_output, 1),
}

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='hex LUT generation tool')
    parser.add_argument('LUT', type=str, help='LUT type', choices=['instructions', 'output'])
    parser.add_argument('-o', type=str, help='output file')

    args = parser.parse_args()

    lut = lut_methods[args.LUT]

    if args.o:
        with open(args.o, 'w') as file:
            file.write(lut + '\n')
    else:
        print(lut)
