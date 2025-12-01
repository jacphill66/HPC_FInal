INDENTATION_DEPTH = 0

def indentation():
    return "    " * INDENTATION_DEPTH


class BaseASTClass:
    def __init__(self, id, methods, line):
        self.id = id
        self.methods = methods
        self.line = line
    
    def __str__(self):
        m_str = ""
        for m in self.methods:
            m_str += str(self.methods[m])
        return f"class {self.id} {{\n {m}  \n}}"
    
    def accept(self, visitor):
        return visitor.visit_BaseASTClass(self)

class BaseASTAnnotatedExpression:
    def __init__(self, annotation, expr, line):
        self.annotation = annotation
        self.expr = expr
        self.line = line
    
    def __str__(self):
        return f"@{str(self.annotation)} {str(self.expr)}"

    def accept(self, visitor):
        return visitor.visit_BaseASTAnnotatedExpression(self)
        
class BaseASTAnnotatedStatement:
    def __init__(self, annotation, statement, line):
        self.annotation = annotation
        self.statement = statement
        self.line = line
    
    def __str__(self):
        return f"@{str(self.annotation)} {str(self.statement)}"

    def accept(self, visitor):
        return visitor.visit_BaseASTAnnotatedStatement(self)

class BaseASTQuoted:
    def __init__(self, quote_type, expr, line):
        self.quote_type = quote_type
        self.expr = expr
        self.line = line
    
    def __str__(self):
        return f"{self.quote_type}({str(self.expr)})"

    def accept(self, visitor):
        return visitor.visit_BaseASTQuoted(self)

class BaseASTReturn:
    def __init__(self, expr):
        self.expr = expr
        
    def __str__(self):
        return f"return {str(self.expr)};"

    def accept(self, visitor):
        return visitor.visit_BaseASTReturn(self)

class BaseASTCallable:
    def __init__(self, id, params, annotation, body, call_type, var_args, line):
        self.id = id
        self.params = params
        self.annotation = annotation
        self.body = body
        self.call_type = call_type
        self.var_args = var_args
        self.line = line
    
    def __str__(self):
        f_str = ""
        if self.call_type == "macro":
            f_str += f"macro {self.id}"
        else:
            f_str += f"def {self.id}"
        f_str += "("
        for param in self.params:
            if param[1] != None:
                f_str += str(param[0]) + ":" + str(param[1]) + ","
            else:
                f_str += str(param[0]) + ","
        if len(self.params) > 0:
            f_str = f_str[:-1]
        if self.var_args:
            f_str += "*"
        f_str += ")"
        if self.annotation != None:
            f_str += "->" + str(self.annotation)
        f_str += str(self.body)
        return f_str
    
    def accept(self, visitor):
        return visitor.visit_BaseASTCallable(self)

class BaseASTEmtpyElement:
    def __init__(self):
        pass
    
    def __str__(self):
        return "_"
    
    def accept(self, visitor):
        return visitor.visit_BaseASTEmptyElement(self)

class BaseASTError:
    def __init__(self, msg, line):
        self.msg = msg
        self.line = line
    
    def __str__(self):
        return f"Error[{self.msg}] on line: {self.line}"
    
    def accept(self, visitor):
        raise Exception("Internal Error: Attempting to Visit Base AST Error Node!")

class BaseASTInt:
    def __init__(self, value, line):
        self.value = value
        self.type = None
        self.line = line
    
    def accept(self, visitor):
        return visitor.visit_BaseASTInt(self)
    
    def __str__(self):
        return str(self.value)
    
class BaseASTFloat:
    def __init__(self, value, line):
        self.value = value
        self.type = None
        self.line = line
    
    def accept(self, visitor):
        return visitor.visit_BaseASTFloat(self)    
    
    def __str__(self):
        return str(self.value)

class BaseASTNull:
    def __init__(self, line):
        self.line = line
        self.type = None
        
    def accept(self, visitor):
        return visitor.visit_BaseASTNull(self)
    
    def __str__(self):
        return "null"

class BaseASTString:
    def __init__(self, value, line, str_type):
        self.value = value
        self.line = line
        self.type = None
        self.str_type = str_type
        
    def accept(self, visitor):
        return visitor.visit_BaseASTString(self)    

    def __str__(self):
        return "\"" + self.value + "\""

class BaseASTBool:
    def __init__(self, value, line):
        self.value = value
        self.line = line
        self.type = None
        
    def accept(self, visitor):
        return visitor.visit_BaseASTBool(self)    
    
    def __str__(self):
        if self.value:
            return "true"
        else:
            return "false"

class BaseASTBinaryOp:
    def __init__(self, lhs, op, rhs, line):
        self.lhs = lhs
        self.op = op
        self.rhs = rhs
        self.type = None
        self.line = line
    
    def accept(self, visitor):
        return visitor.visit_BaseASTBinaryOp(self)
    
    def __str__(self):
        return f"({str(self.lhs)} {self.op} {str(self.rhs)})"

class BaseASTUnaryOp:
    def __init__(self, expr, op, prefix, line):
        self.expr = expr
        self.op = op
        self.prefix = prefix
        self.type = None
        self.line = line
    
    def accept(self, visitor):
        return visitor.visit_BaseASTUnaryOp(self)
    
    def __str__(self):
        if self.prefix:
            return f"({self.op}{str(self.expr)})"
        else:
            return f"({str(self.expr)}{self.op})"

class BaseASTExprStatement:
    def __init__(self, expr, line):
        self.expr = expr
        self.type = None
        self.line = line
    
    def accept(self, visitor):
        return visitor.visit_BaseASTExprStatement(self)    
    
    def __str__(self):
        return str(self.expr) + ";"

class BaseASTSequence:
    def __init__(self, statements, line):
        self.statements = statements
        self.line = line
        self.type = None
        
    def accept(self, visitor):
        return visitor.visit_BaseASTSequence(self)         
        
    def __str__(self):
        prog = indentation() + "{|\n"
        global INDENTATION_DEPTH
        INDENTATION_DEPTH += 1
        for s in self.statements:
            prog += indentation() + str(s) + "\n"
        INDENTATION_DEPTH -= 1
        return prog + indentation() + "\n|}"
        
class BaseASTBlock:
    def __init__(self, statements, line):
        self.statements = statements
        self.type = None
        self.line = line
        
    def accept(self, visitor):
        return visitor.visit_BaseASTBlock(self)     
    
    def __str__(self):
        if len(self.statements) == 0:
            return "{}"
        prog = indentation() + "{\n"
        global INDENTATION_DEPTH
        INDENTATION_DEPTH += 1
        for s in self.statements:
            prog += indentation() + str(s) + "\n"
        INDENTATION_DEPTH -= 1
        return prog + indentation() + "}"

class BaseASTLoop:
    def __init__(self, statement, line):
        self.statement = statement
        self.line = line
        self.type = None
        
    def __str__(self):
        return "loop " + str(self.statement)

class BaseASTWhile:
    def __init__(self, cond, statement, line):
        self.cond = cond
        self.statement = statement
        self.line = line
        self.type = None
    
    def accept(self, visitor):
        return visitor.visit_BaseASTWhile(self)         
    
    def __str__(self):
        return "while " + str(self.cond) + " " + str(self.statement)

class BaseASTRepeat:
    def __init__(self, expr, statement, line):
        self.expr = expr
        self.statement = statement
        self.line = line
        self.type = None
    
    def accept(self, visitor):
        return visitor.visit_BaseASTRepeat(self)       
    
    def __str__(self):
        return "repeat " + str(self.expr) + str(self.statement)

class BaseASTIf:
    def __init__(self, expr, statement, else_statement, line):
        self.expr = expr
        self.statement = statement
        self.else_statement = else_statement
        self.line = line
        self.type = None
    
    def accept(self, visitor):
        return visitor.visit_BaseASTIf(self) 
    
    def __str__(self):
        if self.else_statement != None:
            return "if " + str(self.expr) + " " + str(self.statement) + " else " + str(self.else_statement)
        return "if " + str(self.expr) + " " + str(self.statement)
        
class BaseASTCall:
    def __init__(self, id, args, line):
        self.id = id
        self.args = args
        self.line = line
        self.type = None
    
    def accept(self, visitor):
        return visitor.visit_BaseASTCall(self)    
    
    def __str__(self):
        call = str(self.id)
        call += "("
        if len(self.args) > 0:
            for arg in self.args[:len(self.args)-1]:
                call += str(arg)
                call += ","
            call += str(self.args[len(self.args)-1])
        call += ")"
        return call

class BaseASTVariableDeclaration:
    def __init__(self, id, annotation, op, expr, line):
        self.id = id
        self.annotation = annotation
        self.op = op
        self.expr = expr
        self.line = line
        self.type = None

    def accept(self, visitor):
        return visitor.visit_BaseASTVariableDeclaration(self)
    
    def __str__(self):
        if self.annotation != None:
            return f"var {self.id}:{self.annotation} {self.op} {str(self.expr)};"
        else:
            return f"var {self.id} {self.op} {str(self.expr)};" 


class BaseASTIdentifier:
    def __init__(self, text, line):
        self.text = text
        self.line = line
        self.type = None
    
    def accept(self, visitor):
        return visitor.visit_BaseASTIdentifier(self)
    
    def __str__(self):
        return f"Identifier[{self.text}]"

class BaseASTUpdateStatement:
    def __init__(self, ref, op, expr1, expr2, line):
        self.ref = ref
        self.op = op
        self.expr1 = expr1
        self.expr2 = expr2
        self.type = None
        self.line = line
        
    def accept(self, visitor):
        return visitor.visit_BaseASTUpdateStatement(self)
    
    def __str__(self):
        if self.expr2 == None:
            return f"{str(self.ref)} {str(self.op)} {str(self.expr1)};"
        return f"{str(self.ref)} {str(self.op)} {str(self.expr1)}:{str(self.expr2)};"

class BaseASTStructRef:
    def __init__(self, struct, key_or_index, line):
        self.struct = struct
        self.key_or_index = key_or_index
        self.type = None
        self.line = line
    
    def accept(self, visitor):
        return visitor.visit_BaseASTStructRef(self)
    
    def __str__(self):
        return str(self.struct) + "[" + str(self.key_or_index) + "]"

class BaseASTStruct:
    def __init__(self, keys, elements, open_bracket, closed_bracket, line):
        self.keys = keys
        self.elements = elements
        self.open_bracket = open_bracket
        self.closed_bracket = closed_bracket
        self.key_type = None
        self.el_type = None
        self.line = line
        self.homogenous = False
        
    def accept(self, visitor):
        return visitor.visit_BaseASTStruct(self)
    
    def __str__(self):
        s = self.open_bracket
        if len(self.elements) > 0:
            i = 0
            j = 0
            while i < len(self.keys) and j < len(self.elements):
                s += str(self.keys[i]) + ":"
                s += str(self.elements[j])
                s += ","
                i += 1
                j += 1
        else:
            i = 0
            while i < len(self.keys):
                s += str(self.keys[i]) + ","
                i += 1
        s += self.closed_bracket
        return s


class ASTClassDefinition:
    pass