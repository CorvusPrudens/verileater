from antlr4 import FileStream, CommonTokenStream

try:
    from build.eaterLexer import eaterLexer
    from build.eaterParser import eaterParser
    from build.eaterVisitor import eaterVisitor
    from machine import MachineCode, machine_dict
except ModuleNotFoundError:
    from assembler.build.eaterLexer import eaterLexer
    from assembler.build.eaterParser import eaterParser
    from assembler.build.eaterVisitor import eaterVisitor
    from assembler.machine import MachineCode, machine_dict


class Variable:

    def __init__(self, identifier: 'str', initializer: 'int', const: 'bool'=False):
        self.identifier = identifier
        self.initializer = initializer
        self.const = const

        self.address = None
    
    def setAddress(self, address: 'int'):
        self.address = address

    def getAddress(self):
        return self.address

    def getSize(self):
        """Return the number of bytes this variable occupies"""
        return 1

    def __str__(self):
        const = 'const ' if self.const else ''
        return f'{const}{self.identifier} @ {self.address}'


class Label:

    def __init__(self, identifier: 'str'):
        self.identifier = identifier

        self.address = None
    
    def setAddress(self, address: 'int'):
        self.address = address

    def getAddress(self):
        return self.address

    def getSize(self):
        return 0


class Argument:

    def __init__(self, identifier: 'str|None'=None, number: 'int|None'=None, address: 'bool'=False):
        self.identifier = identifier
        self.number = number
        self.address = address

    def getConst(self, variables: 'dict[str: Variable]') -> 'bool':
        """Determine whether this argument has a constant value"""
        const_var = self.identifier in variables and variables[self.identifier].const
        return self.number or const_var

    def getValue(self, variables: 'dict[str: Variable]'):
        if self.getConst(variables):
            if self.number:
                return self.number
            
            if self.identifier in variables and variables[self.identifier].const:
                return variables[self.identifier].initializer
        
        raise ValueError(f'Argument "{self}" does not have const compile time value')

    def getAddress(self, variables: 'dict[str: Variable]', labels: 'dict[str: Label]'):
        if self.getConst(variables):
            raise ValueError(f'Argument "{self}" does not have an address in RAM')
        
        if self.identifier in labels:
            return labels[self.identifier].getAddress()
        
        if self.identifier in variables:
            return variables[self.identifier].getAddress()
        
        raise ValueError(f'Argument "{self}" does not an address in RAM')

    def __str__(self):
        if self.address and self.identifier:
            return f'& {self.identifier}'
        elif self.identifier:
            return f'{self.identifier}'
        elif self.number:
            return str(self.number)
        else:
            return '??'


class Instruction:

    def __init__(self, mnemonic: 'str', args: 'list[Argument]'):
        self.mnemonic = mnemonic
        self.args = args

        self.address = None

    def getSize(self):
        """Return the number of bytes this instruction occupies"""
        return 1
    
    def setAddress(self, address: 'int'):
        self.address = address


class Error:

    def __init__(self):
        pass


def assemble_machine(instruction: 'Instruction', labels: 'dict[str: Label]', variables: 'dict[str: Variable]') -> 'list[int]':
    try:
        machine = machine_dict[instruction.mnemonic.upper()]

        machine_bytes = [(machine.opcode & (2**MachineCode.OPCODE_BITS - 1)) << 4]

        if instruction.args:
            if machine.arg_type is not None and len(instruction.args) != len(machine.arg_type):
                raise ValueError(f'Instruction "{instruction.mnemonic}" does not match expected arguments')

            args = []
            
            for arg, arg_type in zip(instruction.args, machine.arg_type):
                if arg_type == MachineCode.LITERAL:
                    try:
                        value = arg.getValue(variables)
                        args.append(value)
                    except ValueError as e:
                        raise e
                elif arg_type == MachineCode.ADDRESS:
                    try:
                        address = arg.getAddress(variables, labels)
                        args.append(address)
                    except ValueError as e:
                        raise e

            machine_bytes[0] |= args[0] & 0xF

            for arg in args[1:]:
                machine_bytes.append(arg & 0xFF)
        
        return machine_bytes
    except KeyError:
        raise ValueError(f'Unkown mnemonic "{instruction.mnemonic}"')


class Visitor(eaterVisitor):

    def parse(self, path, ram_size: 'int'):

        self.statements: 'list[Instruction|Label]' = []
        self.variables: 'dict[str: Variable]' = {}
        self.labels: 'dict[str: Label]' = {}

        self.statements_bytes = 0
        self.variables_bytes = 0

        input_stream = FileStream(path)
        lexer = eaterLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = eaterParser(stream)
        tree = parser.parse()
        
        self.visitParse(tree)
        self.resolveIdentifiers()
        self.assignAddresses(ram_size)
        self.program = self.assemble(ram_size)

    def assignVariableAddresses(self, ram_size):
        address = ram_size
        self.variables_bytes = 0
        for _, var in self.variables.items():
            self.variables_bytes += var.getSize()
            address -= var.getSize()
            var.setAddress(address)

        if address < 0:
            raise IndexError(f'Variables overflow RAM ({ram_size} bytes) with {self.variables_bytes} bytes')

    def assignStatementAddresses(self, ram_size):
        address = 0
        for statement in self.statements:
            statement.setAddress(address)
            address += statement.getSize()

        self.statements_bytes = address

        if address > ram_size:
            raise IndexError(f'Instructions overflow RAM ({ram_size} bytes) with {address} bytes')

    def assignAddresses(self, ram_size):
        self.assignVariableAddresses(ram_size)
        self.assignStatementAddresses(ram_size)

        total_size = self.statements_bytes + self.variables_bytes

        if total_size > ram_size:
            raise IndexError(f'Instructions and variables overflow RAM ({ram_size} bytes) with {total_size} bytes')

    def resolveIdentifiers(self):

        label_set = set(self.labels.keys())
        variable_set = set(self.variables.keys())

        intersection = label_set.intersection(variable_set)

        clashing_identifiers = list(intersection)
        if clashing_identifiers:
            s = "s" if len(clashing_identifiers) > 1 else ""
            raise NameError(f'{clashing_identifiers} identifier{s} cannot be both variable{s} and label{s}')

    def assemble(self, ram_size):
        ram = [0 for _ in range(ram_size)]
        address = 0

        for statement in filter(lambda s: type(s) == Instruction, self.statements):
            machine_bytes = assemble_machine(statement, self.labels, self.variables)
            for byte in machine_bytes:
                ram[address] = byte
                address += 1

        for variable in filter(lambda v: not v.const, self.variables.values()):
            ram[variable.getAddress()] = variable.initializer if variable.initializer is not None else 0

        return ram

    def visitConstVar(self, ctx: eaterParser.ConstVarContext):
        var = Variable(str(ctx.IDENTIFIER()), self.visitNumber(ctx), const=True)
        if var.identifier in self.variables:
            raise KeyError(f'Variable "{var.identifier}" appears more than once')
        self.variables[var.identifier] = var
    
    def visitLet(self, ctx: eaterParser.LetContext):
        var = Variable(str(ctx.IDENTIFIER()), self.visitNumber(ctx), const=False)
        if var.identifier in self.variables:
            raise KeyError(f'Variable "{var.identifier}" appears more than once')
        self.variables[var.identifier] = var

    def visitNumberBin(self, ctx: eaterParser.NumberBinContext):
        return int(str(ctx.BIN()).replace('_', ''), 2)
    
    def visitNumberHex(self, ctx: eaterParser.NumberHexContext):
        return int(str(ctx.HEX()).replace('_', ''), 16)

    def visitNumberDec(self, ctx: eaterParser.NumberDecContext):
        return int(str(ctx.DEC()), 10)
    
    def visitInstrNoargs(self, ctx: eaterParser.InstrNoargsContext):
        instr = Instruction(str(ctx.MNEMONIC_NOARGS()), [])
        self.statements.append(instr)
    
    def visitInstrArgs(self, ctx: eaterParser.InstrArgsContext):
        args = self.visitChildren(ctx)
        if type(args) != list:
            args = [args]
        instr = Instruction(str(ctx.MNEMONIC_ARGS()), args)
        self.statements.append(instr)

    def visitArgNumber(self, ctx: eaterParser.ArgNumberContext):
        return Argument(number=self.visitChildren(ctx))

    def visitArgIdentifier(self, ctx: eaterParser.ArgIdentifierContext):
        return Argument(identifier=str(ctx.IDENTIFIER()))

    def visitArgAddress(self, ctx: eaterParser.ArgAddressContext):
        return Argument(identifier=str(ctx.IDENTIFIER()), address=True)

    def visitLabel(self, ctx: eaterParser.LabelContext):
        label = Label(str(ctx.IDENTIFIER()))
        if label.identifier in self.labels:
            raise KeyError(f'Label "{label.identifier}" appears more than once')
        self.labels[label.identifier] = label
        self.statements.append(label)

if __name__ == '__main__':
    import argparse
    from formatter import format_bytes

    parser = argparse.ArgumentParser(description='Simple Eater 8-bit Assembler')
    parser.add_argument('file', type=str, help='input file')
    parser.add_argument('-o', type=str, help='output hex file')
    parser.add_argument('-b', '--binary', action='store_true', help='format data in binary')
    parser.add_argument('-a', '--addresses', action='store_true', help='display addresses for each byte')

    args = parser.parse_args()

    visitor = Visitor()
    visitor.parse(args.file, 16)

    formatted_program = format_bytes(visitor.program, 1, binary=args.binary, addresses=args.addresses)

    if args.o:
        if args.binary or args.addresses:
            raise ValueError('--binary or --addresses are mutually exclusive with -o')
        with open(args.o, 'w') as file:
            file.write(formatted_program)
    else:
        print(formatted_program)
