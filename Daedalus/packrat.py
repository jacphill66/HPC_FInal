STRING = 0
INTEGER = 1
FLOAT = 2
KEYWORD = 3
IDENTIFIER = 4
SYMBOL = 5


def token_type_to_str(tokenType):
    if tokenType == STRING:
        return "String"
    elif tokenType == INTEGER:
        return "Integer"
    elif tokenType == FLOAT:
        return "Float"
    elif tokenType == KEYWORD:
        return "Keyword"
    elif tokenType == IDENTIFIER:
        return "Identifier"
    elif tokenType == SYMBOL:
        return "Symbol"
    else:
        return "Invalid Token Type"
        
class Token:
    def __init__(self, type, value=None):
        self.type = type
        self.value = value
    
    def __repr__(self):            
        return f"Token[{token_type_to_str(self.type)}:{self.value}]" if self.value else f"Token[{token_type_to_str(self.type)}]" 

class Match:
    def __init__(self, name, tokens, start, end, keep, keep_tokens, keep_id, children=[]):
        self.name = name
        self.tokens = tokens
        self.start = start
        self.end = end
        self.keep = keep
        self.keep_tokens = keep_tokens
        self.keep_id = keep_id
        self.children = children
    
    def expand(self):
        for c in self.children:
            c.expand()
        print(self.name)
            
    def __repr__(self):
        if len(self.tokens) == 0:
            return f"({self.name} children:{self.children})"
        else:
            return f"({self.name} tokens:{self.tokens} children:{self.children})"

class MatchKind:
    def match(self, tokens, position, table):
        pass
   
class MatchChain(MatchKind):
    def __init__(self, patterns):
        self.patterns = patterns

    def match(self, tokens, position, table, keep, keep_tokens, keep_id):
        initial_pos = position
        matches = []
        for p in self.patterns:
            m = p.match(tokens, position, table, False, False, "")
            if m:
                if m.keep:
                    matches.append(m)
                else:
                    matches += m.children
                
                position = m.end
            else:
                return None
        return Match("_Chain", tokens, initial_pos, position, False, False, "", matches)

class MatchUnion(MatchKind):
    def __init__(self, patterns):
        self.patterns = patterns

    def match(self, tokens, position, table, keep, keep_tokens, keep_id):
        initial_position = position
        for p in self.patterns:
            m = p.match(tokens, position, table, False, False, "")
            if m:
                if m.keep:
                    return Match("_Union", m.tokens, m.start, m.end, False, False, "", [m])
                else:
                    return Match("_Union", m.tokens, m.start, m.end, False, False, "", m.children)
        return None

class MatchNamedRule(MatchKind):
    def __init__(self, name, pattern):
        self.name = name
        self.pattern = pattern
                       
    def match(self, tokens, position, table, keep, keep_tokens, keep_id):
        if position < len(tokens):
            if table[self.name][position] == None:
                table[self.name][position] = "fail"
                m = self.pattern.match(tokens, position, table, False, False, "")
                if m != None:
                    tokens = ""

                    if keep_tokens:
                        tokens = m.tokens
                
                    if m.keep:
                        m = Match(f"{self.name}", tokens, m.start, m.end, keep, keep_id, "", [m])
                    else:
                        m = Match(f"{self.name}", tokens, m.start, m.end, keep, keep_id, "", m.children)
                    
                    table[self.name][position] = m
                return m
                
            elif table[self.name][position] == "fail":
                return None
            else:
                return table[self.name][position]
        else:
            return None
        
class MatchZeroOrOne(MatchKind):
    def __init__(self, pattern):
        self.pattern = pattern
        
    def match(self, tokens, position, table, keep, keep_tokens, keep_id):
        m = self.pattern.match(tokens, position, table, False, False, "")
        if m:
            if m.keep:
                return Match("_ZeroOrOne", m.tokens, m.start, m.end, False, False, "", m.children)
            else:
                return Match("_ZeroOrOne", m.tokens, m.start, m.end, False, False, "", [m])
        else:
            return Match("_ZeroOrOne", [], position, position, False, False, "", [m])
    
class MatchOneOrMore(MatchKind):
    def __init__(self, pattern):
        self.pattern = pattern
        
    def match(self, tokens, position, table, keep, keep_tokens, keep_id):
        matches = []
        initial_pos = position
        m = self.pattern.match(tokens, position, table, False, False, "")
        pos = initial_pos
        while m != None:
            if m.keep:
                matches.append(m)
            else:
                matches += m.children
            pos = m.end
            m = self.pattern.match(tokens, pos, table, False, False, "")
        if pos != initial_pos:
            return Match("_OneOrMore", tokens[initial_pos:pos], initial_pos, pos, False, False, "", matches)
        else:
            return None

class MatchZeroOrMore(MatchKind):
    def __init__(self, pattern):
        self.pattern = pattern
    
    def match(self, tokens, position, table, keep, keep_tokens, keep_id):
        initial_pos = position
        m = self.pattern.match(tokens, position, table, False, False, "")
        matches = []
        pos = initial_pos
        while m != None:
            if m.keep:
                matches.append(m)
            else:
                matches += m.children
            pos = m.end
            m = self.pattern.match(tokens, pos, table, False, False, "")
        
        if pos != initial_pos:
            return Match("_ZeroOrMore", tokens[initial_pos:pos], initial_pos, pos, False, False, "", matches)
        else:
            return Match("_ZeroOrMore", [], initial_pos, initial_pos, False, False, "", [])

class MatchText(MatchKind):
    def __init__(self, text):
        self.text = text
    
    def match(self, text, position, table, keep, keep_tokens, keep_id):
        end = position+len(self.text)
        if len(self.text) <= len(text) and text[position:end] == self.text:
            return Match("_Text", text[position:end], position, end, False, False, "", [])
        else:
            return None

class MatchRuleReference(MatchKind):
    def __init__(self, grammar, rule_name, keep, keep_tokens, keep_id):
        self.grammar = grammar
        self.rule_name = rule_name
        self.keep = keep
        self.keep_tokens = keep_tokens
        self.keep_id = keep_id
    
    def match(self, tokens, position, table, keep, keep_tokens, keep_id):
        return self.grammar.get_rules()[self.rule_name].match(tokens, position, table, self.keep, self.keep_tokens, self.keep_id)

class Parser:
    def __init__(self, grammar):
        self.table = {}
        self.grammar = grammar        
        
    def init_table(self, tokens):
        for rule in self.grammar.get_rules():
            self.table[rule] = [None]*len(tokens)
    
    def match(self, tokens, keep, keep_tokens, keep_id):
        self.init_table(tokens)
        return self.grammar.get_start().match(tokens, 0, self.table, False, False, "")

class Grammar:
    def __init__(self):
        self.rules = {}
    
    def get_rules(self):
        return self.rules
    
    def add_rule(self, name, pattern):
        self.rules[name] = MatchNamedRule(name, pattern)
    
    def new_reference_rule(self, name, keep_tokens, keep_id):
        return MatchRuleReference(self, name, keep, keep_tokens, keep_id) 
    
    def get_start(self):
        return self.rules["start"]
