import base_ast_objects, expansion

def unquoted(ast):
    return type(ast) == base_ast_objects.BaseASTQuoted and ast.quote_type == "~"

def resolve_unquote(ast, interpreter):
    if unquoted(ast):
        return ast.expr.accept(interpreter)
    return ast

class QuasiQuoter:
    def __init__(self, interpreter):
        self.interpreter = interpreter

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
        lhs = resolve_unquote(expr.lhs, self.interpreter)
        rhs = resolve_unquote(expr.rhs, self.interpreter)
        op = resolve_unquote(expr.op, self.interpreter)
        return base_ast_objects.BaseASTBinaryOp(lhs, op, rhs, expr.line)
        
    def visit_BaseASTUnaryOp(self, expr):
        return resolve_unquote(expr.expr, self.interpreter)
        
    def visit_BaseASTExprStatement(self, expr):
        return base_ast_objects.BaseASTExprStatement(resolve_unquote(expr.expr, self.interpreter), expr.line)
    
    def visit_BaseASTQuoted(self, quoted_s):
        quote_type = quoted_s.quote_type
        if quote_type == "'":
            return quoted_s.expr
        elif quote_type == "`":
            return quoted_s.expr
        elif quote_type == "~":
            return quoted_s.expr.accept(self.interpreter)
            
    def visit_BaseASTCallable(self, statement):
        id = resolve_unquote(definition.id)

        self.interpreter.add_callable(definition.id, definition)

        i = 0
        params = []
        while i < len(definition.params):
            params.append([None, None])
            i += 1
            
        i = 0
        while i < len(definition.params):
            params[i][0] = resolve_unquote(definition.params[i][0])
            params[i][1] = resolve_unquote(definition.params[i][1])
            i += 1
            
        if definition.annotation != None:
            annotation = resolve_unquote(definition.annotation)
    
        body = definition.body.accept(self)
        
        return base_ast_objects.BaseASTCallable(id, params, annotation, body, definition.call_type, definition.var_args, definition.line)
        
    def visit_BaseASTBlock(self, block):
        i = 0
        statements = []
        while i < len(block.statements):
            statements.append(block.statements[i].accept(self))
            i += 1
        return base_ast_objects.BaseASTBlock(statements, block.line)
        
    def visit_BaseASTWhile(self, w):       
        return base_ast_objects.BaseASTWhile(resolve_unquote(w.cond, self.interpreter), w.statement.accept(self), w.line)
        
    def visit_BaseASTIf(self, i):
        else_statement = None
        if i.else_statement:
            else_statement = i.else_statement.accept(self)
        return base_ast_objects.BaseASTIf(resolve_unquote(i.expr, self.interpreter), i.statement.accept(self), else_statement, i.line)


    def visit_BaseASTReference(self, r):
        return r

    def visit_BaseASTUpdateStatement(self, u_s):
        return base_ast_objects.BaseASTUpdateStatement(resolve_unquote(u_s.ref, self.interpreter), u_s.op, resolve_unquote(u_s.expr1, self.interpreter), None, u_s.line)
        
    def visit_BaseASTVariableDeclaration(self, v):
        if v.annotation != None:
            return base_ast_objects.BaseASTVariableDeclaration(resolve_unquote(v.id, self.interpreter), resolve_unquote(v.annotation, self.interpreter), v.op, resolve_unquote(v.expr, self.interpreter), v.line)
        else:
            return base_ast_objects.BaseASTVariableDeclaration(resolve_unquote(v.id, self.interpreter), None, v.op, resolve_unquote(v.expr, self.interpreter), v.line)
                
    def visit_BaseASTStruct(self, s):            
        i = 0
        keys = []
        elements = []
        while i < len(s.keys):
            keys.append(resolve_unquote(s.keys[i], self.interpreter))
            elements.append(resolve_unquote(s.elements[i], self.interpreter))
            i += 1
        return base_ast_objects.BaseASTStruct(keys, elements, s.open_bracket, s.closed_bracket, s.line)
    
    def visit_BaseASTStructRef(self, acc):
        return base_ast_objects.BaseASTStructRef(resolve_unquote(acc.struct, self.interpreter), resolve_unquote(acc.key_or_index, self.interpreter))
    
    
    def visit_BaseASTReturn(self, r):
        return base_ast_objects.BaseASTReturn(resolve_unquote(r.expr, self.interpreter), r.line)

    def visit_BaseASTCall(self, call):
        args = []
        i = 0
        while i < len(call.args):
            args.append(resolve_unquote(call.args[i], self.interpreter))
            i += 1
        return base_ast_objects.BaseASTCall(resolve_unquote(call.id, self.interpreter), args, call.line)


        
    def visit_BaseASTRepeat(self, r):
        pass

    def visit_BaseASTAnnotatedStatement(self, statement):
        pass

    def visit_BaseASTSequence(self, seq):
        i = 0
        statements = []
        while i < len(seq.statements):
            statements.append(seq.statements[i].accept(self))
            i += 1
        return base_ast_objects.BaseASTBlock(statements, seq.line)