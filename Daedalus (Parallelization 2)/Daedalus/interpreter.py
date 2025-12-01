import base_ast_objects, quasi_quoting
from mpi4py import MPI

class Result(Exception):
    def __init__(self, result):
        self.result = result
        
def keyed_elements_to_string(keys, elements):
    s = ""
    i = 0
    keys = list(keys)
    elements = list(elements)
    while i < len(elements):
        s += str(keys[i])
        s += ":"
        s += str(elements[i])
        s += ","
        i += 1
    return s

def elements_to_string(elements):
    s = ""
    i = 0
    elements = list(elements)
    while i < len(elements):
        s += str(elements[i])
        s += ","
        i += 1
    return s
    
class Tuple:
    def __init__(self, elements):
        self.elements = elements
    
    def __str__(self):
        return "(" + elements_to_string(self.elements) + ")"
       
class Record:
    def __init__(self, keys, elements):
        self.keys = keys
        self.elements = elements
    
    def __str__(self):
        return "(" + keyed_elements_to_string(self.keys, self.elements) + ")"

class Table:
    def __init__(self, keys, elements):
        self.struct = dict(zip(keys, elements))
    
    def __str__(self):
        return "{" + keyed_elements_to_string(self.struct.keys(), self.struct.values()) + "}"

    def remove_key_or_index(self, key):
        r = self.struct[key]
        del self.struct[key]
        return r
    
    def insert_key(self, key, el):
        self.struct[key] = el

class Struct:
    def __init__(self, keys, elements):
        self.keys = keys
        self.elements = elements
    
    def __str__(self):
        return "[" + keyed_elements_to_string(self.keys, self.elements) + "]"
        
class Array:
    def __init__(self, elements):
        self.elements = elements
    
    def __str__(self):
        return "[" + elements_to_string(self.elements) + "]"
        
class Set:
    def __init__(self, elements):
        self.elements = elements
    
    def __str__(self):
        return "<|" + elements_to_string(self.elements) + "|>"

class PriorityQueue:
    def __init__(self, keys, elements):
        self.keys = keys
        self.elements = elements
    
    def __str__(self):
        return "<|" + keyed_elements_to_string(self.keys, self.elements) + "|>"

class Deque:
    def __init__(self, elements):
        self.elements = elements
    
    def __str__(self):
        return "<|" + elements_to_string(self.elements) + "|>"

class List:
    def __init__(self, elements):
        self.elements = elements
        
    def __str__(self):
        return "{" + elements_to_string(self.elements) + "}"
    
    def get_index(self, index):
        if type(index) != base_ast_objects.BaseASTInt:
            raise Exception("Attempting to Use Invalid Index Type in Interpreter!")
        elif index.value >= len(self.elements):
            raise Exception("Index Out of Bounds Exception!")
        return self.elements[index.value]
        
    def modify_index(self, index, el):
        if type(index) != base_ast_objects.BaseASTInt:
            raise Exception("Attempting to Use Invalid Index Type in Interpreter!")
        elif index.value >= len(self.elements):
            raise Exception("Index Out of Bounds Exception!")
        self.elements[index.value] = el
            
    def append(self, el):
        return self.elements.append(el)
    
    def pop(self):
        if len(self.elements) == 0:
            raise Exception("Attempting to Pop From an Empty List!")
        return self.elements.pop()

class Interpreter:
    def __init__(self):
        self.quasi_quoter = quasi_quoting.QuasiQuoter(self)
        self.macros = {}
        self.functions = {}
        self.classes = {}
        self.scopes = [{}]
        self.scope_depth = 0
        
    def expand(self, raw_ast):  
        res = None
        if len(raw_ast.children) == 0 and raw_ast.tokens != "":
            res = self.apply_expand(raw_ast.name, [base_ast_objects.BaseASTString(raw_ast.tokens, -1, "IMMUTABLE")])
        else:            
            comm = MPI.COMM_WORLD
            rank = comm.Get_rank()
            size = comm.Get_size()
            name = MPI.Get_processor_name()   
            res = None
            
            if size > len(raw_ast.children):
                for i in range(0, len(raw_ast.children)):
                    raw_ast.children[i] = self.expand(raw_ast.children[i])
                return self.apply_expand(raw_ast.name, raw_ast.children)
            else:
                rem = len(raw_ast.children) % size
                step = len(raw_ast.children) // size
                start = rank*step
                end = start + step
                if rem > 0 and end + rem == len(raw_ast.children):
                    end += rem
                
                result_ast = [None] * (end-start)
                for i in range(start, end):
                    result_ast[i-start] = self.expand(raw_ast.children[i]) 
                    
                # Gather the results into result_ast
                result_ast = comm.gather(result_ast, root=0)
                if rank == 0:
                    lst = []

                    # Gather produces a list of lists, turn them into one list
                    for l in result_ast:
                        for s in l:
                            lst.append(s)
                    result_ast = lst
                    res = self.apply_expand(raw_ast.name, result_ast)
        return res
    
    def add_function(self, func):
        if func.call_type == "func":
            self.functions[func.id.text] = func
        else:
            raise Exception("Attempting to Add Invalid Function!")
    
    def add_class(self, class_def):
        self.classes[class_def.id.value] = class_def    
    
    def add_function(self, func_def):
        self.functions[func_def.id.value] = func_def
    
    def handle_var_args(self, func, args, eval_args=True):
        new_args = []
        if len(args) < len(func.params):
            raise Exception("Number of Args Must Match or Exceed the Number of Params in a VarArgs Call!")
        i = 0
        while i < len(func.params)-1:
            if eval_args:
                new_args.append(args[i].accept(self))
            else:
                l.append(args[i])
            i += 1
        l = List([])
        while i < len(args):
            if eval_args:
                l.append(args[i].accept(self))
            else:
                l.append(args[i])
            i += 1
        new_args.append(l)
        return new_args
    
    def apply_expand(self, id, args):
        if not (id in self.classes):
            raise Exception("Expansion Class Isn't Defined")
        c = self.classes[id]
        m = c.methods["expand"]
        if m.var_args:
            args = self.handle_var_args(m, args, False)
        return self.apply_call(m, args, id)

    def new_scope(self):
        self.scopes.append({})
        self.scope_depth += 1
    
    def add_to_scope(self, id, arg):
        self.scopes[self.scope_depth][id] = arg
    
    def search_scopes(self, id):
        i = self.scope_depth
        while i >= 0:
            if id in self.scopes[i]:
                return self.scopes[i][id]
            i -= 1
    
    def modify_scope(self, id, arg):
        i = self.scope_depth
        while i >= 0:
            if id in self.scopes[i]:
                self.scopes[i][id] = arg
                return 
            i -= 1
        raise Exception(f"Attempting to Modify a Variable: {id} That Doesn't Exist!")
            
    def close_scope(self):
        self.scopes.pop()
        self.scope_depth -= 1
        
    def less_than(self, lhs, rhs):
        lhs_val = lhs.accept(self).value
        rhs_val = rhs.accept(self).value
        return base_ast_objects.BaseASTBool(lhs_val < rhs_val, lhs.line)
    
    def greater_than(self, lhs, rhs):
        lhs_val = lhs.accept(self).value
        rhs_val = rhs.accept(self).value
        return base_ast_objects.BaseASTBool(lhs_val > rhs_val, lhs.line)
    
    def less_than_or_equal(self, lhs, rhs):
        lhs_val = lhs.accept(self).value
        rhs_val = rhs.accept(self).value
        return base_ast_objects.BaseASTBool(lhs_val <= rhs_val, lhs.line)
    
    def greater_than_or_equal(self, lhs, rhs):
        lhs_val = lhs.accept(self).value
        rhs_val = rhs.accept(self).value
        return base_ast_objects.BaseASTBool(lhs_val >= rhs_val, lhs.line)
    
    def equal(self, lhs, rhs):
        lhs_val = lhs.accept(self).value
        rhs_val = rhs.accept(self).value
        
        return base_ast_objects.BaseASTBool(lhs_val == rhs_val, lhs.line)
    
    def keyed_remove(self, struct, key_or_index):
        return struct.remove_key_or_index(key_or_index.value)

    def struct_pop(self, struct):
        return struct.pop()
    
    def struct_size(self, struct):
        raise Exception("Not Implemented Yet!")
               
    def visit_BaseASTInt(self, i):
        return base_ast_objects.BaseASTInt(i.value, i.line)
        
    def visit_BaseASTFloat(self, f):
        return base_ast_objects.BaseASTFloat(f.value, f.line)

    def visit_BaseASTBool(self, b):
        return base_ast_objects.BaseASTBool(b.value, b.line)

    def visit_BaseASTNull(self, n):
        return base_ast_objects.BaseASTNull(n.line)

    def visit_BaseASTString(self, s):
        return base_ast_objects.BaseASTString(s.value, s.line, s.str_type)
    
    def num_op(self, val, line):
        if type(val) == int:
            return base_ast_objects.BaseASTInt(val, line)
        elif type(val) == float:
            return base_ast_objects.BaseASTFloat(val, line)
        else:
            raise Exception("Invalid Operation Encountered When Expanding Binary Operation")
    
    def binary_boolean_op(self, res):
        if type(res) != bool:
            raise Exception("Invalid Binary Boolean Operation in Expansion!")
        return base_ast_objects.BaseASTBoolean(res)
    
    def visit_BaseASTBinaryOp(self, expr):
        lhs = expr.lhs.accept(self)
        rhs = expr.rhs.accept(self)
        op = expr.op
        if type(op) == base_ast_objects.BaseASTString:
            op = op.value
            
        if op == "+":
            return self.num_op(lhs.value + rhs.value, lhs.line)
        elif op == "-":
            return self.num_op(lhs.value - rhs.value, lhs.line)
        elif op == "*":
            return self.num_op(lhs.value * rhs.value, lhs.line)
        elif op == "/":
            return self.num_op(lhs.value / rhs.value, lhs.line)
        elif op == "%":
            return self.num_op(lhs.value % rhs.value, lhs.line)
        elif op == "<":
            return self.less_than(lhs, rhs)
        elif op == ">":
            return self.greater_than(lhs, rhs)
        elif op == "<=":
            return self.less_than_or_equal(lhs, rhs)
        elif op == ">=":
            return self.greater_than_or_equal(lhs, rhs)
        elif op == "==":
            return self.equal(lhs, rhs)
        elif op == "&&":
            return self.boolean_op(lhs.value and rhs.value)
        elif op == "||":
            return self.boolean_op(lhs.value or rhs.value)
        elif op == "^":
            return self.num(lhs.value ** rhs.value, lhs.line)
        elif op == "!!":
            return self.keyed_remove(lhs, rhs)
        else:
            raise Exception(f"Attempting to Interpret Invalid Binary Operation: {op}", expr.line)
        
    def visit_BaseASTUnaryOp(self, expr):
        opperand = expr.expr.accept(self)
        op = expr.op
        if expr.prefix and op == "-":
            return self.num_op(-opperand.value)
        elif expr.prefix and op == "!":
            return self.boolean_op(-opperand.value)
        elif not expr.prefix and op == "!":
            return self.struct_pop(lhs)
        elif not expr.prefix and op == "#":
            return self.struct_size(opperand)
        else:
            raise Exception(f"Attempting to Compile Invalid Unary Operation: {op}", expr.line)
    
    def visit_BaseASTExprStatement(self, expr):
        e = expr.expr.accept(self)
        
    def visit_BaseASTQuoted(self, quoted_s):
        quote_type = quoted_s.quote_type
        if quote_type == "'":
            return quoted_s.expr
        elif quote_type == "`":
            return quoted_s.expr.accept(self.quasi_quoter)
        elif quote_type == "~":
            raise Exception("Invalid Unquote")

    def visit_BaseASTEmptyElement(self, el):
        return "_"

    def visit_BaseASTStruct(self, s):   
        keys = []
        elements = []
        for k in s.keys:
            keys.append(k.accept(self).value)
        for el in s.elements:
            elements.append(el.accept(self))
        if s.open_bracket == "{":            
            if elements == []:
                return List(keys)
            return Table(keys, elements)
        elif s.open_bracket == "[":
            if elements == []:
                return Array(keys)
            return Struct(keys, elements)
        elif s.open_bracket == "<|":
            if elements == []:
                return Deque(keys)
            elif elements[0] == "_":
                return Set(keys)
            return PriorityQueue(keys, elements)
        elif s.open_bracket == "(":
            if elements == []:
                return Tuple(keys)
            return Record(keys, elements)
        else:
            raise Exception("Attempting to Compile Invalid Structure", s.line)    
    
    def visit_BaseASTCallable(self, definition):
        if definition.call_type == "macro":
            self.macros[definition.id.text] = definition 
        elif definition.call_type == "func":
            self.functions[definition.id.text] = definition
        return definition

    def apply_macro(self, call):
        m = self.macros[call.id.id]
        self.new_scope()
        for p in m.params:
            if self.params[0] != base_ast_objects.BaseASTIdentifier:
                raise Exception("Invalid Param in Expansion!")
            self.add_to_scope(p[0].id, call.args[0].accept(self.interpreter))


    def apply_call(self, func, args, class_name=None):
        if len(func.params) != len(args) and not func.var_args:
            raise Exception("Number of Args Must Match Number of Params!")
        scope_depth = self.scope_depth
        self.new_scope()
        i = 0
        for arg in args:
            self.add_to_scope(func.params[i][0].value, args[i])
            i += 1
        try:
            res = func.body.accept(self)
        except Result as result:
            while self.scope_depth != scope_depth:
                self.close_scope()
            return result.result
        self.close_scope()
         
    def visit_BaseASTCall(self, call):
        if type(call.id) == base_ast_objects.BaseASTIdentifier and call.id.text == "print":
            print(call.args[0].accept(self))
        elif type(call.id) == base_ast_objects.BaseASTIdentifier and call.id.text == "eval":
            pass
        elif type(call.id) == base_ast_objects.BaseASTIdentifier and call.id.text == "unpack":
            statements = call.args[0].accept(self).elements
            return base_ast_objects.BaseASTSequence(statements, -1)            
        elif type(call.id) == base_ast_objects.BaseASTIdentifier and call.id.text == "int":
            return base_ast_objects.BaseASTInt(int(call.args[0].accept(self).value), -1)
        elif type(call.id) == base_ast_objects.BaseASTIdentifier and call.id.text == "bool":
            return base_ast_objects.BaseASTInt(bool(call.args[0].accept(self).value), -1)
        elif type(call.id) ==  base_ast_objects.BaseASTIdentifier and call.id.text == "ID":
            return base_ast_objects.BaseASTIdentifier(call.args[0].accept(self).value, -1)
        else:
            if call.id.text in self.functions:
                func = self.functions[call.id.text]
                args = []
                if func.var_args:
                    args = self.handle_var_args(call.args, func)
                else:   
                    for arg in call.args:
                        args.append(arg.accept(self))
                return self.apply_call(func, args)
            else:
                raise Exception("Invalid Callable Called in Interpreter!")

    def visit_BaseASTSequence(self, seq):
        for s in seq.statements:
            s.accept(self)
    
    def visit_BaseASTBlock(self, block):
        self.new_scope()
        for s in block.statements:
            s.accept(self)
        self.close_scope()

    def visit_BaseASTWhile(self, w):
        expr = w.cond.accept(self)
        while expr.value == True:
            w.statement.accept(self)
            expr = w.cond.accept(self)       
    
    def visit_BaseASTIf(self, i):
        expr = i.expr.accept(self)
        if expr.value == True:
            i.statement.accept(self)
        else:
            if i.else_statement != None:
                i.else_statement.accept(self)
            
    def visit_BaseASTIdentifier(self, r):
        return self.search_scopes(r.text)

    def visit_BaseASTVariableDeclaration(self, v):
        self.add_to_scope(v.id.value, v.expr.accept(self))   
    
    def visit_BaseASTStructRef(self, acc):
        struct = acc.struct.accept(self)
        index_or_key = acc.key_or_index.accept(self)
        return struct.get_index(index_or_key)
        
    def visit_BaseASTUpdateStatement(self, update):
        if type(update.ref) == base_ast_objects.BaseASTIdentifier and update.op.value == "=":
            self.modify_scope(update.ref.text, update.expr1.accept(self))
        elif update.op.value == "<<":
            struct = update.ref.accept(self)
            struct.append(update.expr1.accept(self))
        elif type(update.ref) == base_ast_objects.BaseASTStructRef and update.op.value == "=":
            struct = update.ref.struct.accept(self)
            index_or_key = update.ref.key_or_index.accept(self)
            expr = update.expr1.accept(self)
            struct.modify_index(index_or_key, expr)
        
    def visit_BaseASTReturn(self, r):
        raise Result(r.expr.accept(self))

    def visit_BaseASTRepeat(self, r):
        pass

    def visit_BaseASTAnnotatedStatement(self, expr):
        pass