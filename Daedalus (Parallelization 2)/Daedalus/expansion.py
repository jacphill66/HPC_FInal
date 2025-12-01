import base_ast_objects, quasi_quoting, interpreter

def quasi_quoted(ast):
    return type(ast) == base_ast_objects.BaseASTQuoted and ast.quote_type == "`"

def is_macro_call(ast):
    return type(ast) == base_ast_objects.BaseASTCallable and ast.quote_type == "macro"

def expandable(ast):
    return is_macro_call(ast)

def expand(ast, expander):
    res = ast.accept(expander)
    while expandable(res):
        res = ast.accept(expander)
    return res

class Expander:    
    def __init__(self):
        self.interpreter = interpreter.Interpreter()
        self.quasi_quoter = quasi_quoting.QuasiQuoter(self.interpreter)
        self.macros = {}
        
    def add_callable(self, id, definition):        
        if type(id) != base_ast_objects.BaseASTString:
            raise Exception("Callables Must Use String Identifiers!")
        
        id = id.value
        
        if type(definition) != base_ast_objects.BaseASTCallable:
            raise Exception("Invalid Callable!")
        
        if definition.call_type == "macro":
            self.interpreter.macros[id] = definition
        elif definition.call_type == "func":
            self.interpreter.functions[id] = definition
        elif definition.call_type == "method":
            pass
        else:
            raise Exception("Invalid Callable Type")
    
    def expand(self, ast):
        i = 0
        while i < len(ast):
            ast[i] = ast[i].accept(self)
            i += 1
        return ast

    def visit_BaseASTInt(self, i):
        return i
        
    def visit_BaseASTFloat(self, f):
        return f

    def visit_BaseASTBool(self, b):
        return b

    def visit_BaseASTNull(self, n):
        return n

    def visit_BaseASTString(self, s):       
        return s
    
    def visit_BaseASTBinaryOp(self, expr):
        expr.lhs = expand(expr.lhs, self)
        expr.rhs = expand(expr.rhs, self)
        return expr
        
    def visit_BaseASTUnaryOp(self, expr):
        expr.expr = expand(expr.expr, self)
        return expr
        
    def visit_BaseASTExprStatement(self, expr):
        expr.expr = expand(expr.expr, self)
        return expr
                
    def visit_BaseASTQuoted(self, quoted_s):
        if quasi_quoted(quoted_s):
            return quoted_s
        elif quoted_s.quote_type == "'":
            return quoted_s
        else:
            raise Exception("Expanding Invalid Quote Type")
    
    def visit_BaseASTClass(self, c):
        c.id = expand(c.id, self)
        for m_id in c.methods:
            c.methods[m_id].accept(self)
        return c
    
    def visit_BaseASTCallable(self, definition):    
        definition.id = expand(definition.id, self)

        self.add_callable(definition.id, definition)

        i = 0
        while i < len(definition.params):
            definition.params[i][0] = expand(definition.params[i][0], self)
            if definition.params[i][1] != None:
                definition.params[i][1] = expand(definition.params[i][1], self)
            i += 1
            
        if definition.annotation != None:
            definition.annotation = expand(definition.annotation, self)
    
        definition.body.accept(self)
        
        return definition
        
    def visit_BaseASTCall(self, call):
        call.id = expand(call.id, self)
        i = 0
        while i < len(call.args):
            call.args[i] = expand(call.args[i], self)
            i += 1

        if type(call.id) != base_ast_objects.BaseASTIdentifier:
            raise Exception("Callable Identifiers Must Expand to Valid Identifiers!")
        
        id = call.id.text

        if id in self.macros:
            self.apply_macro(call)

        return call
        
    def visit_BaseASTBlock(self, block):
        i = 0
        while i < len(block.statements):
            block.statements[i].accept(self)
            i += 1
        return block

    def visit_BaseASTWhile(self, w):
        w.cond = expand(w.cond, self)
        w.statement.accept(self)
        return w
    
    def visit_BaseASTIf(self, i):
        i.expr = expand(i.expr, self)
        i.statement.accept(self)
        if i.else_statement:
            i.else_statement.accept(self)
        return i
        
    def visit_BaseASTIdentifier(self, r):
        return r

    def visit_BaseASTVariableDeclaration(self, v):
        v.id = expand(v.id, self)
        if v.annotation != None:
            v.annotation = expand(v.annotation, self)
        v.expr = expand(v.expr, self)
        return v
    
    def visit_BaseASTUpdateStatement(self, up):
        up.ref = expand(up.ref, self)
        up.op = expand(up.op, self)
        up.expr = expand(up.expr1, self)
        return up
    
    def visit_BaseASTStruct(self, s):   
        i = 0
        while i < len(s.keys):
            s.keys[i] = expand(s.keys[i], self)
            if len(s.elements) > 0:
                s.elements[i] = expand(s.elements[i], self)
            i += 1
        return s
    
    def visit_BaseASTStructRef(self, ref):
        ref.struct = expand(ref.struct, self)
        ref.key_or_index = expand(ref.key_or_index, self)
        return ref
    
    def visit_BaseASTStructOp(self, op):
        op.ref = expand(op.ref, self)
        op.key = expand(op.key, self)
        op.op = expand(op.op, self)
        op.val = expand(op.val, self)
        return op

    def visit_BaseASTStructModify(self, mod):
        mod.ref = expand(mod.ref)
        mod.op = expand(mod.op)
        mod.expr = expand(mod.expr)
        return mod

    def visit_BaseASTReturn(self, r):
        r.expr = expand(r.expr, self)
        return r

    def visit_BaseASTRepeat(self, r):
        pass
    
    def visit_BaseASTAnnotatedStatement(self, expr):
        pass

    def visit_BaseASTSequence(self, seq):
        pass