grammar eater;

// Parsing

parse       : statement* EOF;

statement   : variable NEWLINE
            | instruction NEWLINE
            | label NEWLINE
            | NEWLINE
            ;

let         : 'let' IDENTIFIER ('=' number)?;
constVar    : 'const' IDENTIFIER '=' number;

variable    : let
            | constVar
            ;

numberBin   : BIN;
numberHex   : HEX;
numberDec   : DEC;

number      : numberBin
            | numberHex
            | numberDec
            ;

instruction : IDENTIFIER                          # instrNoargs
            | IDENTIFIER argument (',' argument)* # instrArgs
            ;

argument    : number         # argNumber
            | IDENTIFIER     # argIdentifier
            | '&' IDENTIFIER # argAddress
            ;

label       : IDENTIFIER ':';

// Lexing

STRING: '"' (~["\r\n] | '\\"')* '"';

COMMENT: '//' ~[\r\n]* [\n\r] -> skip;
COMMENT_BLOCK: '/*' .*? '*/' -> skip;

BIN: '0b' [01][01_]*;
HEX: '0x' [A-Fa-f0-9][A-Fa-f0-9_]*;
DEC: '0' | [1-9][0-9_]*;

IDENTIFIER: [A-Za-z_][A-Za-z_0-9]*;
WHITESPACE: [ \t\r] -> skip;

NEWLINE: '\n';