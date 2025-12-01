class MatchKind:
    def match(self, tokens, position, table, stack, heads):
        pass

class Match:
    def __init__(self, name, tokens, start, end, children=[]):
        self.name = name
        self.tokens = tokens
        self.start = start
        self.end = end
        self.children = children
    
    def __repr__(self):
        return f"Match[name:{self.name}, tokens:{self.tokens}, start:{self.start}, end:{self.end}, children:{self.children}]"
        
class MatchChain(MatchKind):
    def __init__(self, patterns):
        self.patterns = patterns
        
    def match(self, tokens, position, table, stack, heads):
        initial_pos = position
        matches = []
        for p in self.patterns:
            m = p.match(tokens, position, table, stack, heads)
            if m:
                position = m.end
                matches.append(m)
            else:
                return None
        return Match("_Chain", tokens[initial_pos:position], initial_pos, position, matches)
   
    def standardize(self, grammar):
        i = 0
        while i < len(self.patterns):
            self.patterns[i] = self.patterns[i].standardize(grammar)
            i += 1
    
    def __str__(self):
        string = "("
        for pattern in self.patterns:
            string += str(pattern) + " "
        string = string[0:len(string)-1]
        string += ")"
        return string

class MatchUnion(MatchKind):
    def __init__(self, patterns):
        self.patterns = patterns
    
    def match(self, tokens, position, table, stack, heads):
        initial_position = position
        for p in self.patterns:
            m = p.match(tokens, position, table, stack, heads)
            if m:
                return Match("_Union", m.tokens, m.start, m.end, [m])
        return None
        
    def __str__(self):
        string = "("
        for pattern in self.patterns:
            string += str(pattern) + " | "
            
        string = string[0:len(string)-3]
        string += ")"
        return string

    def standardize(self, grammar):
        i = 0
        while i < len(self.patterns):
            self.patterns[i] = self.patterns[i].standardize(grammar)
            i += 1
        
class LR:
    def __init__(self, seed_match, rule, head, next):
        self.seed_match = seed_match
        self.rule = rule
        self.head = head
        self.next = next
    
    def __repr__(self):
        return f"LR({self.seed_match}, {self.rule.name}, {self.head})"

class Head:
    def __init__(self, named_rule):
        self.named_rule = named_rule
        self.involved_set = set()
        self.eval_set = set()
    
    def __repr__(self):
        return f"Head({self.named_rule.name}, {self.involved_set}, {self.eval_set})"

class MemoEntry:
    def __init__(self, ans, pos):
        self.ans = ans
        self.pos = pos
    
    def __repr__(self):
        return f"MemoEntry({self.ans}, {self.pos})"

class MatchNamedRule(MatchKind):
    def __init__(self, name, pattern):
        self.name = name
        self.pattern = pattern
    
    def grow_lr(self, rule, tokens, position, table, stack, heads, entry, head):
        heads[position] = head
        while True:
            head.eval_set = head.involved_set.copy()
            match = rule.pattern.match(tokens, entry.ans.start, table, stack, heads, True) 
            if match == None or match.end <= entry.pos:
                break
            entry.ans = Match(rule.name, match.tokens, match.start, match.end, [match])
            entry.pos = match.end
        heads[position] = None
        return entry.ans
    
    def setup_lr(self, lr, stack):     
        if lr.head == None:
            lr.head = Head(self)
        s = stack
        while s.head != lr.head:    
            s.head = lr.head 
            lr.head.involved_set.add(s.rule)
            s = s.next
    
    def extract_answer(self, rule, tokens, position, table, stack, heads, entry):
        h = entry.ans.head
        if h.named_rule != rule:
            return entry.ans.seed_match
        else:
            entry.ans = entry.ans.seed_match
            if entry.ans == None:
                return None
            else:
                return self.grow_lr(rule, tokens, position, table, stack, heads, entry, h)
        
    def recall(self, tokens, position, table, stack, heads, r):
        m = table[self.name][position]
        h = heads[position]
        
        if h == None:
            return m 
        if m == None and not ((r == h.named_rule) or (r in h.involved_rules)):
            return MemoEntry(None, position) 
        if r in h.eval_set:
            h.eval_set.remove(r)
            match = r.pattern.match(tokens, position, table, stack, heads)
            if match != None:
                m.ans = Match(r.name, match.tokens, match.start, match.end, [match])
                m.pos = match.end 
            else:
                m.ans = match
        return m
    
    def match(self, tokens, position, table, stack, heads):
        if position >= len(tokens): return None
        m = self.recall(tokens, position, table, stack, heads, self)
        if m == None:
            lr = LR(None, self, None, stack)
            stack = lr
            m = MemoEntry(lr, position)
            table[self.name][position] = m
            match = self.pattern.match(tokens, position, table, stack, heads)
            stack = lr.next
            if match != None: 
                match = Match(self.name, match.tokens, match.start, match.end, [match])
                m.pos = match.end
            if lr.head != None: 
                lr.seed_match = match
                return self.extract_answer(self, tokens, position, table, stack, heads, m)
            else:
                m.ans = match
                return match
        else:
            if type(m.ans) is LR:
                self.setup_lr(m.ans, stack)
                return m.ans.seed_match
            return m.ans
    
    def standardize(self, grammar):
        self.pattern = self.pattern.standardize(grammar)
    
    def __str__(self):
        return f"{self.name} = {str(self.pattern)}"
    
class MatchZeroOrOne(MatchKind):
    def __init__(self, pattern):
        self.pattern = pattern
    
    def match(self, tokens, position, table, stack, heads):
        m = self.pattern.match(tokens, position, table, stack, heads)
        if m:
            return Match("_ZeroOrOne", m.tokens, m.start, m.end, [m])
        else:
            return Match("_ZeroOrOne", [], position, position)

    def __str__(self):
        return str(self.pattern) + "?"
    
    def standardize(self, grammar):
        self.pattern = self.pattern.standardize(grammar)
    
class MatchOneOrMore(MatchKind):
    def __init__(self, pattern):
        self.pattern = pattern
    
    def match(self, tokens, position, table, stack, heads):
        matches = []
        initial_pos = position
        m = self.pattern.match(tokens, position, table, stack, heads)
        while m != None:
            matches.append(m)
            pos = m.end
            m = self.pattern.match(tokens, pos, table, stack, heads)
        if len(matches) > 0:
            return Match("_OneOrMore", tokens[initial_pos:pos], initial_pos, pos, matches)
        else:
            return None

    def __str__(self):
        return str(self.pattern) + "+"
    
    def standardize(self, grammar):
        self.pattern = self.pattern.standardize(grammar)

class MatchZeroOrMore(MatchKind):
    def __init__(self, pattern):
        self.pattern = pattern
    
    def match(self, tokens, position, table, stack, heads):
        initial_pos = position
        m = self.pattern.match(tokens, position, table, stack, heads)
        matches = []
        while m != None:
            matches.append(m)
            pos = m.end
            m = self.pattern.match(tokens, pos, table, stack, heads)
        if len(matches) > 0:
            return Match("_ZeroOrMore", tokens[initial_pos:pos], initial_pos, pos, matches)
        else:
            return Match("_ZeroOrMore", [], initial_pos, initial_pos, [])

    def __str__(self):
        return str(self.pattern) + "*"
    
    def standardize(self, grammar):
        self.pattern = self.pattern.standardize(grammar)
        
class MatchText(MatchKind):
    def __init__(self, text):
        self.text = text
    
    def match(self, text, position, table, stack, heads):
        end = position+len(self.text)
        if len(self.text) <= len(text) and text[position:end] == self.text:
            return Match("_Text", text[position:end], position, end, [])
        else:
            return None

    def __str__(self):
        return self.text
    
    def standardize(self, grammar):
        return self
        
class MatchRuleReference(MatchKind):
    def __init__(self, grammar, rule_name, parameter):
        self.grammar = grammar
        self.rule_name = rule_name
        self.parameter = parameter
    
    def match(self, tokens, position, table, stack, heads):
        match = self.grammar.get_rules()[self.rule_name].match(tokens, position, table, stack, heads)
        if match != None:
            return Match(self.rule_name, match.tokens, match.start, match.end, match.children)
        else:
            return match
    
    def __str__(self):
        return self.rule_name

    def standardize(self, grammar):
        return self
            
class MatchEmptyString(MatchKind):
    def __init__(self):
        pass
        
    def match(self, tokens, position, table, stack, heads):
        return Match("_EmtpyString", [], position, position, [])

class MatchString(MatchKind):
    pass

class MatchFloat(MatchKind):
    pass

class MatchInteger(MatchKind):
    pass

class MatchDelimeterText(MatchKind):
    def __init__(self, text):
        self.text = text
    
    def match(self, text, position, table, stack, heads):
        end = position+len(self.text)
        if len(self.text) <= len(text) and text[position:end] == self.text:
            return Match("_DelimeterText", text[position:end], position, end, [])
        else:
            return None
