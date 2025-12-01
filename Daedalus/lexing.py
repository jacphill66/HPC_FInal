
from enum import Enum

ALPHA = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_"
DIGITS = "0123456789"
WHITESPACE = (" ", "    ", "\t")

class TokenType(Enum):
    ERROR = 0
    IDENTIFIER = 1
    INTEGER = 2
    FLOAT = 3
    STRING = 4
    STRING_B = 5
    KEYWORD = 6
    SYMBOL = 7
    
class Token:
    def __init__(self, type, value, line):
        self.type = type
        self.value = value
        self.line = line
        
    def __str__(self):
        return f"{self.type}:{self.value}"
   
    def __repr__(self):
        return str(self)
        
def skip_whitespace(text, pos):
    while pos < len(text) and text[pos] in WHITESPACE:
        pos += 1
    return pos

def match_alnum(text, pos):
    rest = ""
    while pos < len(text) and (text[pos] in DIGITS or text[pos] in ALPHA):
        rest += text[pos]
        pos += 1
    return rest, pos

def match(text, pos, word):
    return pos < len(text) and text[pos:pos+len(word)] == word

def lex_id(text, pos, line):
    id = ""
    if pos < len(text) and text[pos] in ALPHA:
        id += text[pos]
        rest, pos = match_alnum(text, pos+1)
        return Token(TokenType.IDENTIFIER, id + rest, line), pos
    raise Exception("Invalid ID Token", line)

def lex_number(text, pos, line):
    num = ""
    while pos < len(text) and text[pos] in DIGITS:
        num += text[pos]
        pos += 1
    if len(num) == 0:
        raise Exception("Invalid Number Token", line)
    elif pos < len(text) and text[pos] == ".":
        num += text[pos]
        pos += 1
        while pos < len(text) and text[pos] in DIGITS:
            num += text[pos]
            pos += 1
        return Token(TokenType.FLOAT, float(num), line), pos
    else:
        return Token(TokenType.INTEGER, int(num), line), pos
        
def lex_string(text, pos, delimeter, line):
    str = ""
    if pos < len(text):
        if text[pos] == delimeter:
            pos += 1
            while pos < len(text) and text[pos] != delimeter:
                str += text[pos]
                if text[pos] == '\n':
                    line += 1
                pos += 1
            if pos < len(text) and text[pos] == delimeter:
                pos += 1
                if delimeter == "\"":
                    return Token(TokenType.STRING, str, line), pos, line 
                else:
                    return Token(TokenType.STRING_B, str, line), pos, line
    raise Exception("Invalid String Token", line)

def lex_overwatch(text, pos):
    pass

def lex_analysis(text, pos):
    pass

def lex_grammar(text, pos):
    pass

def lex_model(text, pos):
    pass