
import lexing, analyzing, base_ast_objects

def match_value(tokens, pos, val):
    return pos < len(tokens) and tokens[pos].value == val

def expect_token(tokens, pos, val):
    if match_value(tokens, pos, val):
        return tokens[pos], pos + 1
    if pos < len(tokens):
        raise Exception(f"Expected Token Value: {val}, but got: {tokens[pos].value} at:{pos}", tokens[pos].line)
    else:
        raise Exception(f"Expected Token Value: {val} at:{pos}, but ran out of tokens.", tokens[len(tokens)-1].line) 

def next_token(tokens, pos):
    if pos >= len(tokens):
        raise Exception(f"Ran out of tokens", tokens[len(tokens)-1].line) 
    return tokens[pos], pos+1

def peek_next_token(tokens, pos):
    if pos + 1 < len(tokens):
        return tokens[pos+1]
    return None

def curr_tok_val(tokens, pos):
    if pos < len(tokens):
        if tokens[pos].value != None:
            return tokens[pos].value
    return ""

def curr_tok_type(tokens, pos):
    if pos < len(tokens):
        if tokens[pos].value != None:
            return tokens[pos].type
    return ""
    
def parse_overwatch(tokens, pos):
    pass

def parse_analysis(tokens, pos):
    pass

def parse_grammar(tokens, pos):
    pass

def parse_model(tokens, pos):
    pass