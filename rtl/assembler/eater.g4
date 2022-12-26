grammar eater;

// Parsing

parse       : statement* EOF;

statement   : variable
            | instruction
            | label
            ;

let         : 'let' IDENTIFIER ('=' number)?;
const_var   : 'const' IDENTIFIER '=' number;

variable    : let
            | const_var
            ;

number      : BIN # numBin
            | HEX # numHex
            | DEC # numDec
            ;

argument    : number         # argNumber
            | IDENTIFIER     # argVariable
            | '&' IDENTIFIER # argAddress
            ;

instruction : MNEMONIC_NOARGS                        # instrNoargs
            | MNEMONIC_ARGS argument (',' argument)* # instrArgs
            ;

label       : IDENTIFIER ':';

// Lexing

STRING: '"' (~["\r\n] | '\\"')* '"';

COMMENT: '//' ~[\r\n]* [\n\r] -> skip;
COMMENT_BLOCK: '/*' .*? '*/' -> skip;

MNEMONIC_NOARGS
    : 'NOP' | 'nop'
    | 'OUT' | 'out'
    | 'HLT' | 'hlt'
    ;

MNEMONIC_ARGS
    : 'LDA' | 'lda'
    | 'STA' | 'sta'
    | 'LDB' | 'ldb'
    | 'ADI' | 'adi'
    | 'SBI' | 'sbi'
    | 'ADD' | 'add'
    | 'SUB' | 'sub'
    | 'J'   | 'j'
    | 'JC'  | 'jc'
    | 'JZ'  | 'jz'
    ;

BIN: '0b' [01][01_]*;
HEX: '0x' [A-Fa-f0-9][A-Fa-f0-9_]*;
DEC: '0' | [1-9][0-9_]*;

IDENTIFIER: [A-Za-z_][A-Za-z_0-9]*;
WHITESPACE: [ \t\n\r] -> skip;