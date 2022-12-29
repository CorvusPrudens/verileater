from math import log2


class Control:
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


class MachineCode:

    OPCODE_BITS = 4
    UINSTR_BITS = 3

    LITERAL = 0
    ADDRESS = 1

    FETCH_CYCLE: 'list[int]' = [
        Control.CO | Control.MI,
        Control.RO | Control.II | Control.CE,
    ]

    class Flag:
        FLAG_BITS = 2
        def __init__(self, flag: 'int'):
            if flag <= 0 or (flag > MachineCode.Flag.FLAG_BITS or int(log2(flag)) != log2(flag)):
                raise ValueError(f'Flag (provided {flag}) must be a power of 2 that fits within {MachineCode.Flag.FLAG_BITS} bits')
            self.flag = flag
        
        def __eq__(self, other: 'MachineCode.Flag') -> 'bool':
            return self.flag == other.flag

    @classmethod
    def total_bits(cls):
        return cls.OPCODE_BITS + cls.UINSTR_BITS + cls.Flag.FLAG_BITS

    def __init__(self, opcode: 'int', uinstructions: 'list[int]|None'=None, flag: 'MachineCode.Flag | None'=None, invert_flag: 'bool'=False, mnemonic: 'str|None'=None, arg_type: 'list[int]|None'=None, arg_bits: 'list[int]|None'=None):
        if opcode >= 2**MachineCode.OPCODE_BITS:
            raise ValueError(f'Opcode must be less than {2**MachineCode.OPCODE_BITS}')

        if uinstructions is None:
            uinstructions = []
        
        len_fetch = len(MachineCode.FETCH_CYCLE)
        if len(uinstructions) >= 2**MachineCode.UINSTR_BITS - len_fetch:
            raise ValueError(
                f'Too many micro-instructions (expected < {2**MachineCode.UINSTR_BITS - len_fetch}, got {len(uinstructions)})')
        
        self.opcode = opcode
        self.uinstructions = uinstructions + [0 for _ in range(2**MachineCode.UINSTR_BITS - len(uinstructions))]
        self.flag = flag
        self.invert_flag = invert_flag
        self.mnemonic = mnemonic
        if arg_type is not None and arg_type not in [MachineCode.LITERAL, MachineCode.ADDRESS]:
            for t in arg_type:
                if t not in [MachineCode.LITERAL, MachineCode.ADDRESS]:
                    raise ValueError(f'Expected and arg_type of 0 or 1, not {arg_type} for {self.mnemonic}')
        self.arg_type = arg_type
        self.arg_bits = arg_bits

    def fill_addresses(self):
        addresses = {}
        for f in range(2**MachineCode.Flag.FLAG_BITS):
            op_offset = MachineCode.UINSTR_BITS
            flag_offset = MachineCode.UINSTR_BITS + MachineCode.OPCODE_BITS

            # Every instruction will include the fetch cycle
            fetch_addr = (f << flag_offset) | (self.opcode << op_offset) | 0b000
            for i, ucode in enumerate(MachineCode.FETCH_CYCLE):
                addresses[fetch_addr + i] = ucode

            len_fetch = len(MachineCode.FETCH_CYCLE)

            for step in range(2**MachineCode.UINSTR_BITS - len_fetch):
                address = (f << flag_offset) | (self.opcode << op_offset) | (step + len_fetch)
                if self.flag is None:
                    addresses[address] = self.uinstructions[step]
                else:
                    # NOP when condition is not met
                    try:
                        condition = (self.flag.flag & f) == 0 if self.invert_flag else (self.flag.flag & f) > 0
                        addresses[address] = self.uinstructions[step] if condition else 0
                    except ValueError:
                        addresses[address] = 0
        return addresses


machine_code = [
    MachineCode(0, flag=None, mnemonic='NOP', arg_type=None, arg_bits=None, uinstructions=[]),
    MachineCode(1, flag=None, mnemonic='LDA', arg_type=[MachineCode.ADDRESS], arg_bits=4, uinstructions=[
        Control.IO | Control.MI,
        Control.RO | Control.AI,
    ]),
    MachineCode(2, flag=None, mnemonic='STA', arg_type=[MachineCode.ADDRESS], arg_bits=4, uinstructions=[
        Control.IO | Control.MI,
        Control.RI | Control.AO,
    ]),
    MachineCode(3, flag=None, mnemonic='LDB', arg_type=[MachineCode.ADDRESS], arg_bits=4, uinstructions=[
        Control.IO | Control.MI,
        Control.RO | Control.BI,
    ]),
    MachineCode(4, flag=None, mnemonic='ADI', arg_type=[MachineCode.LITERAL], arg_bits=4, uinstructions=[
        Control.IO | Control.BI,
        Control.EO | Control.AI | Control.FI,
    ]),
    MachineCode(5, flag=None, mnemonic='SBI', arg_type=[MachineCode.LITERAL], arg_bits=4, uinstructions=[
        Control.IO | Control.BI,
        Control.EO | Control.AI | Control.SU | Control.FI,
    ]),
    MachineCode(6, flag=None, mnemonic='ADD', arg_type=[MachineCode.ADDRESS], arg_bits=4, uinstructions=[
        Control.IO | Control.MI,
        Control.RO | Control.BI,
        Control.EO | Control.AI | Control.FI,
    ]),
    MachineCode(7, flag=None, mnemonic='SUB', arg_type=[MachineCode.ADDRESS], arg_bits=4, uinstructions=[
        Control.IO | Control.MI,
        Control.RO | Control.BI,
        Control.EO | Control.AI | Control.SU | Control.FI,
    ]),
    MachineCode(8, flag=None, mnemonic='OUT', arg_type=None, arg_bits=None, uinstructions=[
        Control.AO | Control.OI,
    ]),
    MachineCode(9, flag=None, mnemonic='LDI', arg_type=[MachineCode.LITERAL], arg_bits=4, uinstructions=[
        Control.IO | Control.AI,
    ]),
    MachineCode(10, flag=None, mnemonic='J', arg_type=[MachineCode.ADDRESS], arg_bits=4, uinstructions=[
        Control.IO | Control.J
    ]),
    MachineCode(11, flag=MachineCode.Flag(0b01), mnemonic='JC', arg_type=[MachineCode.ADDRESS], arg_bits=4, uinstructions=[
        Control.IO | Control.J
    ]),
    MachineCode(12, flag=MachineCode.Flag(0b10), mnemonic='JZ', arg_type=[MachineCode.ADDRESS], arg_bits=4, uinstructions=[
        Control.IO | Control.J
    ]),
    MachineCode(13, flag=MachineCode.Flag(0b01), invert_flag=True, mnemonic='JNC', arg_type=[MachineCode.ADDRESS], arg_bits=4, uinstructions=[
        Control.IO | Control.J
    ]),
    MachineCode(14, flag=MachineCode.Flag(0b10), invert_flag=True, mnemonic='JNZ', arg_type=[MachineCode.ADDRESS], arg_bits=4, uinstructions=[
        Control.IO | Control.J
    ]),
    MachineCode(15, flag=None, mnemonic='HLT', arg_type=None, arg_bits=None, uinstructions=[
        Control.HLT
    ]),
]

machine_dict = {mc.mnemonic: mc for mc in machine_code}
