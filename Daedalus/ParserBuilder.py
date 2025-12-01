from packrat import *

class Parser:
    def __init__(self, grammar):
        self.table = {}
        self.grammar = grammar        
        
    def init_table(self, tokens):
        for rule in self.grammar.get_rules():
            self.table[rule] = [None]*len(tokens)
    
    def match(self, tokens):
        self.init_table(tokens)
        stack = None
        heads = [None] * len(tokens)
        return self.grammar.get_start().match(tokens, 0, self.table, True, False, "start")

class Grammar:
    def __init__(self, start_rule):
        self.start_rule = start_rule
        self.rules = {}
    
    def get_rules(self):
        return self.rules
    
    def add_rule(self, name, pattern):
        self.rules[name] = MatchNamedRule(name, pattern)
    
    def new_reference_rule(self, name, keep, keep_tokens, keep_id):
        return MatchRuleReference(self, name, keep, keep_tokens, keep_id) 
    
    def get_start(self):
        return self.rules[self.start_rule]
    
    def __str__(self):
        g = ""
        for r in self.rules:
            g += str(self.rules[r]) + "\n"
        return g

class ExtendedGrammar:
    def __init__(self, rule_table):
        self.rule_table = rule_table

    def build_grammar(self):
        g = Grammar("start")
        g.add_rule(v.name, v.pattern)
        return g
    
    def __str__(self):
        grammar_str = ""
        for t in self.rule_table.keys():
            for r in self.rule_table[t]:
                grammar_str += str(r) + "\n"
        return grammar_str
        
class ParameterNode:
    def __init__(self, type, param_id, param_type=None):
        self.type = type
        self.param_id = param_id
        self.param_type = param_type
    
    def __str__(self):
        if self.param_type != None:
            return f"{self.type}[{self.param_id}:{self.param_type}]"
        else:
            return f"[{self.param_id}]"
    
    def standardize(self, grammar):
        return grammar.new_reference_rule(self.type)
            
class MatchParameter:
    def __init__(self, kind, type):
        self.kind = kind
        self.id = id
        self.type = type
    
    def __str__(self):
        if self.param_type != None:
            return f"[{self.param_id}:{self.param_type}]"
        else:
            return f"[{self.param_id}]"
            
class InnerRule:
    def __init__(self, name, body):
        self.name = name
        self.body = body

    def __str__(self):
        return f"{self.name} = {str(self.body)};"

class Rule:
    def __init__(self, type, name, body):
        self.type = type
        self.name = name
        self.body = body

    def __str__(self):
        if type(self.body) != list:
            return f"{self.type} {self.name} = {str(self.body)}"
        else:
            start = f"{self.type} {self.name}" + "{\n"
            body = ""
            for r in self.body:
                body += "\t"
                body += str(r)
                body += "\n"
            end = "\n}"
            return start + body + end
            
class ParserBuilder:
        
    def build_parser(self, grammar_as_string):
        tokens = self.lex_grammar(grammar_as_string)
        g = Grammar("start")
        pos = 0
        while pos < len(tokens):
            name, pattern, pos = self.parse_rule(g, tokens, pos)
            if self.match(tokens, pos, ";"):
                pos += 1
            else:
                raise Exception("Invalid End of Rule")
            g.add_rule(name, pattern)
        p = Parser(g)
        return p
        
    def parse_rule(self, grammar, tokens, pos):
        name = None
        if self.match(tokens, pos, "ID"):
            pos += 1
            name = tokens[pos]
            pos += 1
        else:
            raise Exception("Invalid Start of Rule")
        if self.match(tokens, pos, "="):
            pos += 1
        else:
            raise Exception("Invalid Start of Rule")
        pattern, pos = self.parse_union(grammar, tokens, pos)
        return name, pattern, pos
    
    def valid_id_char(self, char):
        return char == "_" or char.isalnum()
    
    def match_id(self, text, pos):
        id = ""
        while pos < len(text) and self.valid_id_char(text[pos]):
            id += text[pos]
            pos += 1
        return id, pos
    
    def white_space(self, c):
        return c == " " or c == "   " or c == "\t" or c == "\n"
    
    def lex_grammar(self, rule_string):
        pos = 0
        tokens = []
        while pos < len(rule_string):
            c = rule_string[pos]
            if self.white_space(c):
                pos += 1
            elif self.valid_id_char(c):
                id, pos = self.match_id(rule_string, pos)
                tokens.append("ID")
                tokens.append(id)
            elif c == "\"":
                pos += 1
                string = ""
                while pos < len(rule_string) and rule_string[pos] != "\"":
                    string += rule_string[pos]
                    pos += 1
                if rule_string[pos] != "\"":
                    raise Exception("Invalid String")
                pos += 1
                tokens.append("STR-1")
                tokens.append(string)
            elif c == "\'":
                pos += 1
                string = ""
                while pos < len(rule_string) and rule_string[pos] != "\'":
                    string += rule_string[pos]
                    pos += 1
                if rule_string[pos] != "\'":
                    raise Exception("Invalid Delimeter String")
                pos += 1
                tokens.append("STR-2")
                tokens.append(string)
            elif c in ("|", "*", "?", "+", ";", "(", ")", "=", ";", "[", "]", ":", "$"):
                tokens.append(c)
                pos += 1
            else:
                raise Exception("Invalid Token Specified in Grammar")
        return tokens
    
    def match(self, tokens, pos, expect):
        return pos < len(tokens) and tokens[pos] == expect
    
    def parse_atom(self, grammar, tokens, pos):
        if self.match(tokens, pos, "ID"):
            pos += 1
            rule_name = tokens[pos]
            pos += 1
            keep = False
            keep_tokens = False
            keep_id = ""
            if self.match(tokens, pos, "["):
                keep = True
                pos += 2
                keep_id = tokens[pos]
                pos += 1
                if self.match(tokens, pos, "$"):
                    keep_tokens = True
                    pos += 1
                pos += 1
            return grammar.new_reference_rule(rule_name, keep, keep_tokens, keep_id), pos
        elif self.match(tokens, pos, "("):
            pos += 1
            atom, pos = self.parse_union(grammar, tokens, pos)
            if self.match(tokens, pos, ")"):
                return atom, pos+1
            else:
                raise Exception("Unmatched (")
        elif self.match(tokens, pos, "STR-1"):
            pos += 1
            return MatchText(tokens[pos]), pos+1
        elif self.match(tokens, pos, "STR-2"):
            pos += 1
            return MatchDelimeterText(tokens[pos]), pos+1
        else:
            raise Exception("Invalid Atom")
    
    def parse_product(self, grammar, tokens, pos):
        atoms = []       
        count = 0
        while pos < len(tokens) and not (tokens[pos] in (")", "|", ";")):
            atom, pos = self.parse_atom(grammar, tokens, pos)
            
            if self.match(tokens, pos, "*"):
                atom = MatchZeroOrMore(atom)
                pos += 1
            elif self.match(tokens, pos, "+"):
                atom = MatchOneOrMore(atom)
                pos += 1
            elif self.match(tokens, pos, "?"):
                atom = MatchZeroOrOne(atom)
                pos += 1

            count += 1

            atoms.append(atom)    
            
        if count > 1:
            return MatchChain(atoms), pos
        else:
            return atoms[0], pos
           
    def parse_union(self, grammar, tokens, pos):
        atoms = []
        count = 0
        while pos < len(tokens) and not (tokens[pos] in (")", "|", ";")):
            prod, pos = self.parse_product(grammar, tokens, pos)
            atoms.append(prod)            
            count += 1
            
            if self.match(tokens, pos, "|"):
                pos += 1
            
        if count > 1:
            return MatchUnion(atoms), pos
        else:
            return atoms[0], pos    