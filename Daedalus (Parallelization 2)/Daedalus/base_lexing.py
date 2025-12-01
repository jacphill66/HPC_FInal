import lexing, errors

class BaseLexer:
    def __init__(self, text):
        self.pos = 0
        self.text = text
        self.line = 1
        self.symbols = ("+", "-", "*", "/", "%", "^", "!", ";", ",", "(", ")", "{|", "|}", "{", "}", "[", "]", "&&", "||", "<", ">", "==", "<=", ">=", "<|", "|>", "_", "#", "?", "'", "~", "`", "@", "$")
        self.error = None
        self.tokens = []
        
    def add_token(self, tok, pos, line):
        self.line = line
        self.pos = pos
        self.tokens.append(tok)
    
    def lex_base_token(self):
        if self.text[self.pos] == "\"":
            tok, pos, line = lexing.lex_string(self.text, self.pos, "\"", self.line)
            return self.add_token(tok, pos, line)
        elif lexing.match(self.text, self.pos, "null"):
            return self.add_token(lexing.Token(lexing.TokenType.KEYWORD, "null", self.line), self.pos+4, self.line)
        elif lexing.match(self.text, self.pos, "true"):
            return self.add_token(lexing.Token(lexing.TokenType.KEYWORD, "true", self.line), self.pos+4, self.line)   
        elif lexing.match(self.text, self.pos, "false"):
            return self.add_token(lexing.Token(lexing.TokenType.KEYWORD, "false", self.line), self.pos+5, self.line)   
        elif lexing.match(self.text, self.pos, "if"):
            return self.add_token(lexing.Token(lexing.TokenType.KEYWORD, "if", self.line), self.pos+2, self.line)   
        elif lexing.match(self.text, self.pos, "else"):
            return self.add_token(lexing.Token(lexing.TokenType.KEYWORD, "else", self.line), self.pos+4, self.line)   
        elif lexing.match(self.text, self.pos, "while"):
            return self.add_token(lexing.Token(lexing.TokenType.KEYWORD, "while", self.line), self.pos+5, self.line)   
        elif lexing.match(self.text, self.pos, "def"):
            return self.add_token(lexing.Token(lexing.TokenType.KEYWORD, "def", self.line), self.pos+3, self.line)   
        elif lexing.match(self.text, self.pos, "repeat"):
            return self.add_token(lexing.Token(lexing.TokenType.KEYWORD, "repeat", self.line), self.pos+6, self.line)   
        elif lexing.match(self.text, self.pos, "return"):
            return self.add_token(lexing.Token(lexing.TokenType.KEYWORD, "return", self.line), self.pos+6, self.line)   
        elif lexing.match(self.text, self.pos, "str*"):
            return self.add_token(lexing.Token(lexing.TokenType.KEYWORD, "str*", self.line), self.pos+4, self.line)   
        elif lexing.match(self.text, self.pos, "//"):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "//", self.line), self.pos+2, self.line)
        elif lexing.match(self.text, self.pos, "+="):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "+=", self.line), self.pos+2, self.line)
        elif lexing.match(self.text, self.pos, "-="):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "-=", self.line), self.pos+2, self.line)
        elif lexing.match(self.text, self.pos, "*="):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "*=", self.line), self.pos+2, self.line)
        elif lexing.match(self.text, self.pos, "/="):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "/=", self.line), self.pos+2, self.line)
        elif lexing.match(self.text, self.pos, "%="):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "%=", self.line), self.pos+2, self.line)
        elif lexing.match(self.text, self.pos, "+"):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "+", self.line), self.pos+1, self.line)
        elif lexing.match(self.text, self.pos, "-"):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "-", self.line), self.pos+1, self.line)
        elif lexing.match(self.text, self.pos, "*"):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "*", self.line), self.pos+1, self.line)      
        elif lexing.match(self.text, self.pos, "/"):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "/", self.line), self.pos+1, self.line)
        elif lexing.match(self.text, self.pos, "_"):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "_", self.line), self.pos+1, self.line)
        elif lexing.match(self.text, self.pos, "%"):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "%", self.line), self.pos+1, self.line)
        elif lexing.match(self.text, self.pos, "=="):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "==", self.line), self.pos+2, self.line)
        elif lexing.match(self.text, self.pos, "="):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "=", self.line), self.pos+1, self.line)
        elif lexing.match(self.text, self.pos, "?"):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "?", self.line), self.pos+1, self.line)
        elif lexing.match(self.text, self.pos, "#"):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "#", self.line), self.pos+1, self.line)
        elif lexing.match(self.text, self.pos, "~"):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "~", self.line), self.pos+1, self.line)
        elif lexing.match(self.text, self.pos, "^"):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "^", self.line), self.pos+1, self.line)
        elif lexing.match(self.text, self.pos, "$"):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "$", self.line), self.pos+1, self.line)
        elif lexing.match(self.text, self.pos, "!!"):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "!!", self.line), self.pos+2, self.line)
        elif lexing.match(self.text, self.pos, "!"):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "!", self.line), self.pos+1, self.line)
        elif lexing.match(self.text, self.pos, ":"):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, ":", self.line), self.pos+1, self.line)
        elif lexing.match(self.text, self.pos, ";"):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, ";", self.line), self.pos+1, self.line)
        elif lexing.match(self.text, self.pos, ","):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, ",", self.line), self.pos+1, self.line)
        elif lexing.match(self.text, self.pos, "("):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "(", self.line), self.pos+1, self.line)
        elif lexing.match(self.text, self.pos, ")"):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, ")", self.line), self.pos+1, self.line)
        elif lexing.match(self.text, self.pos, "'"):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "'", self.line), self.pos+1, self.line)
        elif lexing.match(self.text, self.pos, "`"):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "`", self.line), self.pos+1, self.line)
        elif lexing.match(self.text, self.pos, "@"):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "@", self.line), self.pos+1, self.line)
        elif lexing.match(self.text, self.pos, "["):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "[", self.line), self.pos+1, self.line)
        elif lexing.match(self.text, self.pos, "]"):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "]", self.line), self.pos+1, self.line)
        elif lexing.match(self.text, self.pos, "{|"):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "{|", self.line), self.pos+2, self.line)
        elif lexing.match(self.text, self.pos, "|}"):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "|}", self.line), self.pos+2, self.line)
        elif lexing.match(self.text, self.pos, "{"):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "{", self.line), self.pos+1, self.line)
        elif lexing.match(self.text, self.pos, "}"):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "}", self.line), self.pos+1, self.line)
        elif lexing.match(self.text, self.pos, "<|"):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "<|", self.line), self.pos+2, self.line)
        elif lexing.match(self.text, self.pos, "|>"):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "|>", self.line), self.pos+2, self.line)
        elif lexing.match(self.text, self.pos, "|"):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "|", self.line), self.pos+1, self.line)
        elif lexing.match(self.text, self.pos, "&&"):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "&&", self.line), self.pos+2, self.line)
        elif lexing.match(self.text, self.pos, "||"):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "||", self.line), self.pos+2, self.line)
        elif lexing.match(self.text, self.pos, "<="):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "<=", self.line), self.pos+2, self.line)
        elif lexing.match(self.text, self.pos, ">="):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, ">=", self.line), self.pos+2, self.line)
        elif lexing.match(self.text, self.pos, "<<"):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "<<", self.line), self.pos+2, self.line)
        elif lexing.match(self.text, self.pos, ">>"):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, ">>", self.line), self.pos+2, self.line)
        elif lexing.match(self.text, self.pos, "<"):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, "<", self.line), self.pos+1, self.line)
        elif lexing.match(self.text, self.pos, ">"):
            return self.add_token(lexing.Token(lexing.TokenType.SYMBOL, ">", self.line), self.pos+1, self.line)
        elif self.text[self.pos] in lexing.ALPHA:
            tok, pos = lexing.lex_id(self.text, self.pos, self.line)
            return self.add_token(tok, pos, self.line)
        elif self.text[self.pos] in lexing.DIGITS:
            tok, pos = lexing.lex_number(self.text, self.pos, self.line)
            return self.add_token(tok, pos, self.line)
        else:
            print(self.text[self.pos])
            exit()
            raise Exception(f"Invalid Token at Position:{self.pos}", self.line)
            
    def lex_base(self):
        while self.pos < len(self.text):
            if self.text[self.pos] in lexing.WHITESPACE:
                self.pos = lexing.skip_whitespace(self.text, self.pos)
                continue
            elif self.text[self.pos] == "\n":
                self.line += 1
                self.pos += 1
                continue
            else:
                self.lex_base_token()
        return self.tokens
