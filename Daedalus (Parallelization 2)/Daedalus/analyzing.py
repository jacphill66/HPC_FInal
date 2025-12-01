import base_ast_objects
from enum import Enum

class BaseType:
    pass

class BaseSimpleType(Enum):
    I32_TYPE = 0
    F32_TYPE = 1
    BOOL_TYPE = 2
    IMUTABLE_STR_TYPE = 3
    NULL_TYPE = 4
    MUTABLE_STR_TYPE = 5
    INT_TYPE = 6
    ERROR_TYPE = 7
    VOID_TYPE = 8
    ANY_TYPE = 9
    EMTPY_EL_TYPE = 10

def string_to_simple_type(str_type, analyzer):
    if str_type == "i32":
        return BaseSimpleType.I32_TYPE
    elif str_type == "f32":
        return BaseSimpleType.F32_TYPE
    elif str_type == "bool":
        return BaseSimpleType.BOOL_TYPE
    elif str_type == "str":
        return BaseSimpleType.IMUTABLE_STR_TYPE
    elif str_type == "int":
        return BaseSimpleType.INT_TYPE
    elif str_type == "any":
        return BaseSimpleType.ANY_TYPE
    elif str_type == "_":
        return BaseSimpleType.EMTPY_EL_TYPE
    else:
        raise Exception("Invalid Simple Type")

def elements_to_type(elements, analyzer):
    el_type = BaseSimpleType.ANY_TYPE
    if len(elements) > 0:
        el_type = annotation_to_type(elements[0], analyzer)
    i = 1
    while i < len(elements):
        if annotation_to_type(el, analyzer) != el_type:
            el_type = BaseSimpleType.ANY_TYPE
        i += 1
    return el_type
    
def keys_and_elements_to_types(keys, elements, analyzer):
    key_type = BaseSimpleType.ANY_TYPE
    el_type = BaseSimpleType.ANY_TYPE
    if len(elements) > 0:
        key_type = annotation_to_type(keys[0], analyzer)
        el_type = annotation_to_type(elements[0], analyzer)
    i = 1
    while i < len(keys):
        if annotation_to_type(keys[i], analyzer) != key_type:
            key_type = BaseSimpleType.ANY_TYPE
        if annotation_to_type(elements[i], analyzer) != el_type:
            el_type = BaseSimpleType.ANY_TYPE
        i += 1
    return key_type, el_type

def curly_struct_to_type(struct, analyzer):
    if len(struct.elements) == 0:
        return ListStructType(elements_to_type(struct.elements, analyzer))
    else:
        key_type, el_type = keys_and_elements_to_types(struct.keys, struct.elements, analyzer)
        return TableStructType(key_type, el_type)

def keys_and_elements_to_type_lists(keys, elements, analyzer):
    key_types = []
    el_types = []
    i = 0
    while i < len(keys):
        key_types.append(annotation_to_type(keys[i], analyzer))
        el_types.append(annotation_to_type(elements[i], analyzer))
        i += 1
    return key_types, el_types

def elements_to_type_list(elements, analyzer):
    el_types = []
    i = 0
    while i < len(keys):
        el_types.append(annotation_to_type(elements[i], analyzer))
        i += 1
    return el_types
    
def square_struct_to_type(struct, analyzer):
    if len(elements) == 0:
        return ArrayStructType(elements_to_type_list(struct.elements, analyzer))
    else:
        key_types, el_types = keys_and_elements_to_type_lists(keys, elements, analyzer)
        return StructStructType(key_types, el_types)

def paren_struct_to_type(struct, analyzer):
    if len(elements) == 0:
        return TupleStructType(elements_to_type_list(struct.elements, analyzer))
    else:
        key_types, el_types = keys_and_elements_to_type_lists(keys, elements, analyzer)
        return RecordStructType(key_types, el_types)

def angle_struct_to_type(struct, analyzer):
    if len(elements) == 0:
        return DequeStructType(elements_to_type(struct.elements, analyzer))
    else:
        key_type, el_type = keys_and_elements_to_types(keys, elements, analyzer)
        
        if el_type == BaseSimpleType.EMPTY_EL_TYPE:
            return SetStructType(key_type)       
        return PriorityQueueType(key_types, el_types)

def struct_to_type(struct, analyzer):
    if struct.open_bracket == "{":
        return curly_struct_to_type(struct, analyzer)
    elif struct.open_bracket == "[":
        return square_struct_to_type(struct, analyzer)
    elif struct.open_bracket == "<|":
        return angle_struct_to_type(struct, analyzer)
    elif struct.open_bracket == "(":
        return paren_struct_to_type(struct, analyzer)
    else:
        raise Exception("Internal Error: Invalid Structure Annotation")

def annotation_to_type(annotation, analyzer):
    if type(annotation) is base_ast_objects.BaseASTQuoted:
        analyzer.errors.append(BaseTypeError("Annotation Quoting Must be Resolved Before Compile-Time!"), annotation.line)
        return BaseSimpleType.ANY_TYPE
    elif type(annotation) is base_ast_objects.BaseASTIdentifier:
        return string_to_simple_type(annotation.text, analyzer)
    elif type(annotation) is base_ast_objects.BaseASTStruct:
        return struct_to_type(annotation, analyzer)
    else:
        raise Exception("Invalid Annotaton")
        
class StaticStringType:
    def __init__(self, string):
        self.string = string

class TableStructType:
    def __init__(self, key_type, el_type):
        self.key_type = key_type
        self.el_type = el_type
    
    def __str__(self):
        return "{" + str(self.key_type) + ":" + str(self.el_type) + "}"
    
    def resolve(self):
        if type(self.key_type) == str:
            self.key_type = self.string_to_simple_type(self.key_type)
        else:
            self.key_type = self.key_type.resolve(self.key_type)
        if type(self.el_type) == str:
            self.el_type == self.string_to_simple_type(self.el_type)
        else:
            self.el_type = self.el_type.resolve(self.el_type)    
    
class ListStructType:
    def __init__(self, el_type):
        self.el_type = el_type
    
    def __str__(self):
        return "{" + str(self.el_type) + "}"

class StructStructType:
    def __init__(self, key_types, el_types):
        self.key_types = key_types
        self.el_types = el_types
    
    def __str__(self):
        struct = "["
        i = 0 
        while i < len(self.key_types):
            struct += str(self.key_types[i])
            struct += ":"
            struct += str(self.el_types[i])
            struct += ","
            i += 1
        return struct + "]"
        
class ArrayStructType:
    def __init__(self, el_types):
        self.el_types = el_types
    
    def __str__(self):
        arr = "["
        i = 0 
        while i < len(self.el_types):
            arr += str(self.el_types[i])
            arr += ","
            i += 1
        return arr + "]"

class TupleStructType:
    def __init__(self, el_types):
        self.el_types = el_types

    def __str__(self):
        tup = "("
        i = 0 
        while i < len(self.el_types):
            tup += str(self.el_types[i])
            tup += ","
            i += 1
        return tup + ")"

class RecordStructType:
    def __init__(self, key_types, el_types):
        self.key_types = key_types
        self.el_types = el_types
    
    def __str__(self):
        rec = "("
        i = 0 
        while i < len(self.key_types):
            rec += str(self.key_types[i])
            rec += ":"
            rec += str(self.el_types[i])
            rec += ","
            i += 1
        return rec + ")"

class DequeStructType:
    def __init__(self, el_type):
        self.el_type = el_type
    
    def __str__(self):
        return "<|" + str(self.el_type) + "|>"

class SetStructType:
    def __init__(self, key_type):
        self.key_type = key_type
    
    def __str__(self):
        return "<|" + str(self.key_type) + ":_" + "|>"
    
class PriorityQueueStructType:
    def __init__(self, key_type, el_type):
        self.key_type = key_type
        self.el_type = el_type

    def __str__(self):
        return "<|" + str(self.key_type) + ":" + str(self.el_type) + "|>"
    

NUMBER_TYPES = (BaseSimpleType.ANY_TYPE, BaseSimpleType.F32_TYPE, BaseSimpleType.I32_TYPE) 

INTEGER_TYPES = (BaseSimpleType.ANY_TYPE, BaseSimpleType.I32_TYPE)
ORDERED_TYPES = (BaseSimpleType.ANY_TYPE, BaseSimpleType.F32_TYPE, BaseSimpleType.I32_TYPE) 

BOOLEAN_TYPES = (BaseSimpleType.ANY_TYPE, BaseSimpleType.BOOL_TYPE,)

STRING_TYPES = (BaseSimpleType.ANY_TYPE, BaseSimpleType.IMUTABLE_STR_TYPE,)

STRUCT_TYPES = (TableStructType, ListStructType, StructStructType, ArrayStructType, TupleStructType, RecordStructType, DequeStructType, SetStructType, PriorityQueueStructType, BaseSimpleType.ANY_TYPE)

IMMUTABLE_TYPES = None
 
class BaseTypeError:
    def __init__(self, msg, line):
        self.msg = msg
    
    def __str__(self):
        return "TypeError: " + self.msg
        
class BaseASTAnalyzer:
    def __init__(self, ast):
        self.ast = ast
        self.type_checker = BaseTypeChecker(ast)
        self.type_errors = None
        
    def type_check(self):
        self.type_checker.type_check()
        self.type_errors = self.type_checker.errors
    
    def print_type_errors(self):
        for error in self.type_errors:
            print(str(error))
          
class BaseTypeChecker:
    def __init__(self, ast):
        self.ast = ast
        self.errors = []
        self.scopes = [{}]
        self.scope_depth = 0
        
    def add_id(self, id, type):
        if id == None:
            return
        self.scopes[self.scope_depth][id] = type
    
    def resolve_id(self, id):
        i = self.scope_depth
        while i >= 0:
            if id in self.scopes[i]:
                return self.scopes[i][id]
            i -= 1
        return None
        
    def new_scope(self):
        self.scope_depth += 1
        self.scopes.append({})
    
    def close_scope(self):
        self.scopes.pop()
        self.scope_depth -= 1
    
    def type_check(self):
        for s in self.ast:
            s.accept(self)

    def compatible_types(self, t1, t2):
        if t1 == BaseSimpleType.ANY_TYPE:
            return True
        return self.compare_types(t1, t2)
    
    def check_type(self, goal_types, actual_type, line):
        if not (actual_type in goal_types):
            e = BaseTypeError(f"Expected a type in: {goal_types}, but got {actual_type} on line: {line}.", line)
            self.errors.append(e)
    
    def adjust_unary_op_for_any(self, t, res_type):
        if t == BaseSimpleType.ANY_TYPE:
            return t
        return res_type
    
    def visit_BaseASTInt(self, i):
        return BaseSimpleType.I32_TYPE
        
    def visit_BaseASTFloat(self, f):
        return BaseSimpleType.F32_TYPE

    def visit_BaseASTBool(self, b):
        return BaseSimpleType.BOOL_TYPE

    def visit_BaseASTNull(self, n):
        return BaseSimpleType.NULL_TYPE

    def visit_BaseASTString(self, s):
        if s.str_type == "IMMUTABLE":
            return BaseSimpleType.IMUTABLE_STR_TYPE
        else:
            print(s.str_type)
            raise Exception("Static Strings Are Not Implemented Yet!")
            return BaseSimpleType.STATIC_STR_TYPE
            
    def up_cast_number_binary_op(self, t1, t2):
        if t1 == t2:
            return t1
        elif t1 == BaseSimpleType.ANY_TYPE or t2 == BaseSimpleType.ANY_TYPE:
            return BaseSimpleType.ANY_TYPE 
        elif t1 == BaseSimpleType.F32_TYPE or t2 == BaseSimpleType.F32_TYPE:
            return BaseSimpleType.F32_TYPE
        elif t1 == BaseSimpleType.INT_TYPE or t2 == BaseSimpleType.INT_TYPE:
            return BaseSimpleType.INT_TYPE
        return BaseSimpleType.I32_TYPE
    
    def adjust_binary_op_for_any(self, t1, t2, res_type):
        if t1 == BaseSimpleType.ANY_TYPE or t2 == BaseSimpleType.ANY_TYPE:
            return BaseSimpleType.ANY_TYPE
        else:
            return res_type
    
    def compare_type_lists(self, lst_1, lst_2):
        if len(lst_1) != len(lst_2):
            return False
        
        i = 0
        while i < len(lst_1):
            if not self.compare_types(lst_1[i], lst_2[i]):
                return False
            i += 1
        return True
    
    def compare_types(self, t1, t2):
        if t1 == t2:
            return True
        elif type(t1) != type(t2):
            return False
        elif type(t1) == BaseSimpleType:
            return t1 == t2
        else:
            if type(t1) == TableStructType:
                return self.compare_types(t1.key_type, t2.key_type) and self.compare_types(t1.el_type, t2.el_type)
            elif type(t1) == ListStructType:
                return self.compare_types(t1.el_type, t2.el_type)
            elif type(t1) == StructStructType:
                return self.compare_type_lists(t1.key_types, t2.key_types) and self.compare_type_lists(t1.el_types, t2.el_types)
            elif type(t1) == ArrayStructType:
                return compare_type_lists(t1.el_types, t2.el_types)
            elif type(t1) == TupleStructType:
                return compare_type_lists(t1.el_types, t2.el_types)
            elif type(t1) == RecordStructType:
                return self.compare_type_lists(t1.key_types, t2.key_types) and self.compare_type_lists(t1.el_types, t2.el_types)
            elif type(t1) == DequeStructType:
                return self.compare_types(t1.el_type, t2.el_type)
            elif type(t1) == PriorityQueueStructType:
                return self.compare_types(t1.key_type, t2.key_type) and self.compare_types(t1.el_type, t2.el_type)
            elif type(t1) == SetStructType:
                return self.compare_types(t1.key_type, t2.key_type)
            else:
                raise Exception("Comparing Invalid Types!")
    
    def any_upcast(self, t1, t2):
        if t1 != t2:
            return BaseSimpleType.ANY_TYPE
        else:
            return t1
    
    def merge_struct_types(self, t1, t2):
        if type(t1) != type(t2):
            raise Exception(f"Internal Error: Attempting to Merge Incompatible Struct Types: {str(t1)} and {str(t2)}")
        if type(t1) == TableStructType:
            return TableStructType(self.any_upcast(t1.key_type, t2.key_type), self.any_upcast(t1.el_type, t2.el_type))
        elif type(t1) == ListStructType:
            return ListStructType(self.any_upcast(t1.el_type, t2.el_type))
        elif type(t1) == ArrayStructType:
            return ArrayStructType(t1.el_types + t2.el_types)
        elif type(t1) == StructStructType:
            return StructStructType(t1.key_types + t2.key_types, t1.el_types + t2.el_types)
        elif type(t1) == DequeStructType:
            return DequeStructType(self.any_upcast(t1.el_type, t2.el_type))
        elif type(t1) == PriorityQueueStructType:
            return DequeStructType(self.any_upcast(t1.key_type, t2.key_type), self.any_upcast(t1.el_type, t2.el_type))
        elif type(t1) == SetStructType:
            return SetStructType(self.any_upcast(t1.key_type, t2.key_type))
        elif type(t1) == TupleStructType:
            return TupleStructType(t1.el_types + t2.el_types)
        elif type(t1) == RecordStructType:
            return RecordStructType(t1.key_types + t2.key_types, t1.el_types + t2.el_types)
        else:
            raise Exception(f"Internal Error: Attempting to Merge Invalid Struct Types: {str(t1)} and {str(t2)}")
            
    def check_merge_struct(self, t1, t2):       
        if type(t1) != type(t2):
            errors.append(BaseTypeError(f"Attempting to Merge Struct: {str(t1)} with Incompatible Type: {str(t2)}", expr.line))
            return t1
        return self.merge_struct_types(t1, t2)     
    
    def visit_BaseASTBinaryOp(self, expr):
        t1 = expr.rhs.accept(self)
        t2 = expr.lhs.accept(self)

        if type(expr.op) == base_ast_objects.BaseASTString:
            expr.op = expr.op.value

        op = expr.op
        
        if op == "+":
            if type(t1) == BaseSimpleType.ANY_TYPE:
                expr.type = BaseSimpleType.ANY_TYPE
            if t1 in NUMBER_TYPES:
                self.check_type(NUMBER_TYPES, t2, expr.line)
                expr.type = self.up_cast_number_binary_op(t1, t2)
            elif t1 in STRING_TYPES:
                self.check_type(STRING_TYPES, t2, expr.line)
                expr.type = self.up_cast_number_binary_op(t1, t2)
            elif type(t1) in STRUCT_TYPES:
                expr.type = self.check_merge_struct(t1, t2)
            else:
                raise Exception("Internal Error: Invalid Type")
            
        elif op in ("-", "*", "/", "^"):
            self.check_type(NUMBER_TYPES, t1, expr.line)
            self.check_type(NUMBER_TYPES, t2, expr.line)
            expr.type = self.up_cast_number_binary_op(t1, t2)
            
        elif op == "%":
            self.check_type(INTEGER_TYPES, t1, expr.line)
            self.check_type(INTEGER_TYPES, t2, expr.line)
            expr.type = self.up_cast_number_binary_op(t1, t2)
            
        elif op in ("<", ">"):
            self.check_type(ORDERED_TYPES, t1, expr.line)
            self.check_type(ORDERED_TYPES, t2, expr.line)
            expr.type = self.adjust_binary_op_for_any(t1, t2, BaseSimpleType.BOOL_TYPE)
        
        elif op in ("==", "<=", ">="):
            expr.type = self.adjust_binary_op_for_any(t1, t2, BaseSimpleType.BOOL_TYPE)
        
        elif op in ("&&", "||"):
            self.check_type(BOOLEAN_TYPES, t1, expr.line)
            self.check_type(BOOLEAN_TYPES, t2, expr.line)
            expr.type = self.adjust_binary_op_for_any(t1, t2, BaseSimpleType.BOOL_TYPE)
        
        elif op == "!!":
            adjusted_t2 = type(t2)
            if adjusted_t2 == TableStructType:
                self.check_type((t2.key_type,), t1, expr.line)
                expr.type = self.adjust_binary_op_for_any(t2, t1, t2.el_type)
            elif adjusted_t2 == PriorityQueueStructType:
                self.check_type((t2.key_type,), t1, expr.line)
                expr.type = self.adjust_binary_op_for_any(t2, t1, t2.el_type)
            elif adjusted_t2 == SetStructType:
                self.check_type((t2.key_type,), t1, expr.line)
                expr.type = BaseSimpleType.ANY_TYPE
            elif t2 == BaseSimpleType.ANY_TYPE:
                expr.type = BaseSimpleType.ANY_TYPE
            else:
                expr.type = BaseSimpleType.ANY_TYPE
                self.errors.append(BaseTypeError(f"Attempting to Remove From an Invalid or Incompatible Struct:{str(t1)}", expr.line))
                
        elif op in ("?", "~"):
            adjusted_t1 = type(t1)
            adjusted_t2 = type(t2)
            if adjusted_t1 in STRUCT_TYPES and adjusted_t2 in STRUCT_TYPES:
                self.check_type(STRUCT_TYPES, adjusted_t1, expr.line)
                self.check_type(STRUCT_TYPES, adjusted_t2, expr.line)
            else:
                self.check_type(STRUCT_TYPES, t1, expr.line)
                self.check_type(STRUCT_TYPES, t2, expr.line)
            expr.type = self.adjust_binary_op_for_any(t1, t2, BaseSimpleType.BOOL_TYPE)
        
        else:
            self.errors.append(BaseTypeError(f"Invalid Operator: {op}", expr.line))
            expr.type = BaseSimpleType.ANY_TYPE
        return expr.type
        
    def visit_BaseASTUnaryOp(self, expr):
        t = expr.expr.accept(self)
        op = expr.op
        if expr.prefix and op == "-":
            self.check_type(NUMBER_TYPES, t, expr.line)
            expr.type = self.adjust_unary_op_for_any(t, BaseSimpleType.I32_TYPE)
        elif expr.prefix and op == "~":
            self.check_type(BOOLEAN_TYPES, t, expr.line)
            expr.type = self.adjust_unary_op_for_any(t, BaseSimpleType.BOOL_TYPE)
        elif expr.prefix and op == "!":
            if type(t) == DequeStructType:
                expr.type = t.el_type
            elif t == BaseSimpleType.ANY_TYPE:
                expr.type = BaseSimpleType.ANY_TYPE
            else:
                self.errors.append(BaseTypeError(f"Attempting to Pop Front of an Incompatible Structure: {str(t)}", expr.line))
            
        elif not expr.prefix and op == "!":
            if type(t) in (DequeStructType, PriorityQueueStructType, ListStructType):
                expr.type = t.el_type
            elif t == BaseSimpleType.ANY_TYPE:
                expr.type = BaseSimpleType.ANY_TYPE
            else:
                self.errors.append(BaseTypeError(f"Attempting to Pop Back of an Incompatible Structure: {str(t)}", expr.line))
        elif not expr.prefix and op == "#":
            if type(t) in STRUCT_TYPES:
                expr.type = BaseSimpleType.I32_TYPE
            elif t == BaseSimpleType.ANY_TYPE:
                expr.type = BaseSimpleType.ANY_TYPE
        else:
            raise Exception("Internal Exception: Invalid Prefix Op")
        return expr.type 
    
    def visit_BaseASTExprStatement(self, expr):
        return expr.expr.accept(self)
    
    def visit_BaseASTSequence(self, seq):
        for s in seq.statements:
            s.accept(self)
        return BaseSimpleType.VOID_TYPE
    
    def visit_BaseASTBlock(self, block):
        self.new_scope()
        for s in block.statements:
            s.accept(self)
        self.close_scope()
        return BaseSimpleType.VOID_TYPE
        
    def visit_BaseASTWhile(self, w):
        cond_type = w.cond.accept(self)
        state_type = w.statement.accept(self)
        self.check_type(BOOLEAN_TYPES, cond_type, w.line)
        return BaseSimpleType.VOID_TYPE
        
    def visit_BaseASTIf(self, i):
        cond_type = i.expr.accept(self)
        state_type = i.statement.accept(self)
        self.check_type(BOOLEAN_TYPES, cond_type, i.line)
        
        if i.else_statement != None:
            i.elseStatement.accept(self)
        
        return BaseSimpleType.VOID_TYPE
        
    def visit_BaseASTQuoted(self, q):
        if not q.quote_type == "'":
            self.errors.append(TypeError(f"Invalid Use of Quote", q.line))
        return BaseSimpleType.ANY_TYPE
            
    def visit_BaseASTVariableDeclaration(self, v):
        expr_type = v.expr.accept(self)
        
        id = None
        if type(v.id) == base_ast_objects.BaseASTString:
            id = v.id.value
        else:
            self.errors.append(BaseTypeError("Variables Must Use Valid Identifiers!", v.line))


        if v.annotation != None:
            v.annotation = annotation_to_type(v.annotation, self)
            self.add_id(id, v.annotation)
            if v.annotation != BaseSimpleType.ANY_TYPE and not self.compare_types(v.annotation, expr_type):
                self.errors.append(BaseTypeError(f"Type of Expr doesn't Match the Variable {v.id}'s Annotation! Expected: {v.annotation}, but got: {expr_type}", v.line))
        else:
            self.add_id(id, expr_type)
        return BaseSimpleType.VOID_TYPE
        
    def visit_BaseASTIdentifier(self, id):
        t = self.resolve_id(id.text)
        if t == None:
            self.errors.append(TypeError(f"Attempting to Reference Undeclared Variable:{id.text}", id.line))
            return BaseSimpleType.ANY_TYPE
        return t
    
    def type_check_homog_struct(self, keys, elements, open_bracket):
        key_type = None
        el_type = None
        if len(elements) != 0:
            key_type = keys[0].accept(self)
            el_type = elements[0].accept(self)
            i = 1
            while i < len(keys):
                k = keys[i].accept(self)
                el = elements[i].accept(self)
                if k != key_type:
                    key_type = BaseSimpleType.ANY_TYPE
                if el != el_type:
                    el_type = BaseSimpleType.ANY_TYPE
                    
                if el == BaseSimpleType.EMPTY_EL_TYPE and el_type != BaseSimpleType.EMPTY_EL_TYPE:
                    self.errors.append("Empty Elements are Only Allowed in Sets, and Empty Elements are the Only Elements Allowed in Sets!")
                    return BaseSimpleType.ANY_TYPE
                    
                i += 1
                
            if open_bracket == "{":
                return TableStructType(key_type, el_type)
            elif open_bracket == "<|":
                if el_type == BaseSimpleType.EMPTY_EL_TYPE:
                    return SetStructType(key_type)
                else:
                    return PriorityQueueStructType(key_type, el_type)

            raise Exception("Invalid Bracket")
        else:
            key_type = keys[0].accept(self)
            i = 1
            while i < len(keys):
                k = keys[i].accept(self)
                if k != key_type:
                    key_type = BaseSimpleType.ANY_TYPE
                i += 1
            if open_bracket == "{":
                return ListStructType(key_type)
            elif open_bracket == "<|":
                return DequeStructType(key_type)
            raise Exception("Invalid Bracket")
    
    def type_check_hetero_struct(self, keys, elements, open_bracket):
        key_types = keys
        el_types = elements
        if len(elements) != 0:
            i = 0
            while i < len(keys):
                key_types[i] = keys[i].accept(self)
                el_types[i] = elements[i].accept(self)
                i += 1
                
            if open_bracket == "[":
                return StructStructType(key_types, el_types)
            elif open_bracket == "(":
                return RecordStructType(key_types, el_types)
            raise Exception("Invalid Bracket")
        else:
            key_types = keys
            i = 0
            while i < len(keys):
                key_types[i] = keys[i].accept(self)
                i += 1
            if open_bracket == "[":
                return ArrayStructType(key_types)
            elif open_bracket == "(":
                return TupleStructType(key_types)
            raise Exception("Invalid Bracket")
    
    def visit_BaseASTStruct(self, s):
        if s.open_bracket in ("{", "<|"):
            return self.type_check_homog_struct(s.keys, s.elements, s.open_bracket)
        elif s.open_bracket in ("[", "("):
            return self.type_check_hetero_struct(s.keys, s.elements, s.open_bracket)
        raise Exception("Invalid Bracket!")
            
    def type_check_struct_ref(self, ref, struct_index_type, res_type):
        key_type = ref.key_or_index.accept(self)
                       
        if not self.compatible_types(struct_index_type, key_type):
            self.errors.append(BaseTypeError(f"Attempting to Access Invalid Structure of Key Type: {struct_index_type} using an Invalid Key Type: {key_type}!", ref.line))
                
        
        return res_type
    
    def type_check_fixed_keyed_struct_ref(self, ref, struct_type):
        key_type = ref.key_or_index.accept(self)
        i = 0
        while i < len(struct_type.key_types):
            if self.compatible_types(struct_type.key_types[i], key_type):
                return BaseSimpleType.ANY_TYPE
            i += 1
        
        self.errors.append(BaseTypeError(f"Attempting to Access Structure:{str(struct_type)} using an Invalid Key Type: {str(key_type)}!", ref.line))

        return BaseSimpleType.ANY_TYPE
        
    def visit_BaseASTStructRef(self, ref):
        s_type = ref.struct.accept(self)
        if type(s_type) in (TableStructType, PriorityQueueStructType):
            return self.type_check_struct_ref(ref, s_type.key_type, s_type.el_type)
        elif type(s_type) == ListStructType:
            return self.type_check_struct_ref(ref, BaseSimpleType.I32_TYPE, s_type.el_type)
        elif type(s_type) in (TupleStructType, ArrayStructType):
            return self.type_check_struct_ref(ref, BaseSimpleType.I32_TYPE, BaseSimpleType.ANY_TYPE)
        elif type(s_type) in (StructStructType, RecordStructType):
            return self.type_check_fixed_keyed_struct_ref(ref, s_type)
        elif s_type == BaseSimpleType.ANY_TYPE:
            return BaseSimpleType.ANY_TYPE
        else:
            self.errors.append(BaseTypeError(f"Attempting to Reference an Invalid Structure! Expected a Structure Type, got: {str(s_type)}", ref.line))
            return BaseSimpleType.ANY_TYPE
    
    def type_check_angle_or_curly_mod(self, struct_type, update):
        val_type = update.expr1.accept(self)
        key_type = update.ref.key_or_index.accept(self)
        
        struct_key_type = BaseSimpleType.I32_TYPE
        
        if type(struct_type) in (TableStructType, PriorityQueueStructType):
            struct_key_type = struct_type.key_type
            
        struct_el_type = struct_type.el_type
        
        if not self.compatible_types(struct_key_type, key_type):
            self.errors.append(BaseTypeError(f"Attempting to Update a Curly or Angle Struct with an Incompatible Key! Expected: {str(struct_key_type)}, but got: {str(key_type)}", update.line))
        if not self.compatible_types(struct_el_type, val_type):
            self.errors.append(BaseTypeError(f"Attempting to Update a Curly or Angle Struct with an Incompatible Element! Expected: {str(struct_el_type)}, but got: {str(val_type)}", update.line))
        
        return BaseSimpleType.VOID_TYPE
    
    def check_compatible_key_value_types(self, key_types, el_types, key_type, value_type):
        if len(key_types) != len(el_types):
            raise Exception("Internal Error: Attempting to Test Compatibility of Key Value Pair on Invalid Type Lists")
        i = 0
        while i < len(key_types):
            if self.compatible_types(key_types[i], key_type):
                if self.compatible_types(el_types[i], value_type):
                    return True
            i += 1
        return False
        
    def type_check_square_mod(self, struct_type, update):
        val_type = update.expr1.accept(self)
        key_type = update.ref.key_or_index.accept(self)
        
        key_types = [BaseSimpleType.I32_TYPE] * len(struct_type.el_types)

        if type(struct_type) == StructStructType:
            key_types = struct_type.key_types
        
        el_types = struct_type.el_types
        
        if not self.check_compatible_key_value_types(key_types, el_types, key_type, val_type):
            self.errors.append(BaseTypeError(f"Attempting to Modify Struct:{struct_type} with Invalid Key:Value Types: {key_type}:{val_type}", update.line))
              
        return BaseSimpleType.VOID_TYPE

    def type_check_append(self, update):
        s_type = update.ref.accept(self)
        expr1_type = update.expr1.accept(self)
        expr2_type = None
        if s_type in (TableStructType, PriorityQueueStructType):
            struct_key_type = s_type.key_type
            struct_el_type = s_type.el_type
            if update.expr2 == None:
                self.errors.append(BaseTypeError(f"Attempting to Update a Curly or Angle Struct with an Incompatible Key! Expected a {str(s_type.key_type)}:{str(s_type.el_type)}, but got {str(expr1_type)}", update.line))
            else:
                expr2_type = update.expr2.accept(self)
            if not self.compatible_types(struct_key_type, expr1_type):
                self.errors.append(BaseTypeError(f"Attempting to Update a Curly or Angle Struct with an Incompatible Key! Expected: {str(struct_key_type)}, but got: {str(key_type)}", update.line))
            if not self.compatible_types(struct_el_type, expr2_type):
                self.errors.append(BaseTypeError(f"Attempting to Update a Curly or Angle Struct with an Incompatible Element! Expected: {str(struct_el_type)}, but got: {str(val_type)}", update.line))                
        elif s_type == ListStructType:
                if expr2 != None:
                    self.errors.append(BaseTypeError(f"Attempting to Push a Key:Value Pair to the Back of a List. Expected: {str(s_type.expr1_type)}, but got {str(s_type.expr1_type)}:{str(s_type.el_type)}", update.line))
                if not self.compatible_types(struct_el_type, expr1_type):
                    self.errors.append(BaseTypeError(f"Attempting to Push an Invalid Element to a List! Expected: {str(struct_el_type)}, but got: {str(expr1_type)}", update.line))
        elif s_type == BaseSimpleType.ANY_TYPE:
            pass
        else:
            self.errors.append(BaseTypeError(f"Invalid Use of <<, Expected a: Table, Priority Queue, or a List, but got: {s_type}", update.line))      
            return BaseSimpleType.VOID_TYPE        

    def type_check_struct_modify(self, update):
        s_type = update.ref.struct.accept(self)
        if type(s_type) in (TableStructType, ListStructType, PriorityQueueStructType):
            return self.type_check_angle_or_curly_mod(s_type, update)
        elif type(s_type) in (StructStructType, ArrayStructType):
            return self.type_check_square_mod(s_type, update)
        elif s_type == BaseSimpleType.ANY_TYPE:
            mod.value.accept(self)
            return BaseSimpleType.VOID_TYPE
        else:
            if type(s_type) in STRUCT_TYPES:
                self.errors.append(BaseTypeError(f"Structure of Type: {str(s_type)} doesn't Support Modification!", mod.line))
            else:
                self.errors.append(BaseTypeError(f"Attempting to Modify an Invalid Structure! Expected a Structure Type, got: {str(s_type)}", mod.line))
                return BaseSimpleType.VOID_TYPE

    def type_check_struct_prepend(self, update):
        pass

    def visit_BaseASTUpdateStatement(self, update):
        ASSIGNMENT_OPS = ("=", "+=", "-=", "*=", "/=", "%=")
        if type(update.ref) == base_ast_objects.BaseASTIdentifier and update.op.value in ASSIGNMENT_OPS:
            t = update.ref.accept(self)
            expr_t = update.expr1.accept(self)
            self.check_type((t,), expr_t, update.line)
            return BaseSimpleType.VOID_TYPE 
        elif type(update.ref) == base_ast_objects.BaseASTStructRef and update.op.value in ASSIGNMENT_OPS:
            return self.type_check_struct_modify(update)
        elif type(update.op) == base_ast_objects.BaseASTIdentifier and update.op.value == "<<":
            return self.type_check_append(update)
        elif type(update.op) == base_ast_objects.BaseASTIdentifier and update.op.text == ">>":
            return self.type_check_struct_prepend(update)
        else:
            self.errors.append(BaseTypeError(f"Invalid Update Statement", update.line))      
            return BaseSimpleType.VOID_TYPE
        
    def visit_BaseASTRepeat(self, r):
        pass
    
    def visit_BaseASTReturn(self, ret):
        return None
    
    def visit_BaseASTCallable(self, callable):
        return_type = None
        
        self.new_scope()
        
        for p in callable.params:
            if params[1] != None:
                self.add_id(id, params[1])
            else:
                self.add_id(id, BaseSimpleType.ANY_TYPE)

        for s in callable.statements:
            s.accept(self)
            if type(s) == base_ast_objects.BaseASTReturn:
                ret_type = s.expr.accept(self)
                if return_type == None:
                    return_type = ret_type
                elif return_type != BaseSimpleType.ANY_TYPE and return_type != ret_type:
                    self.errors.append("")
        
        self.close_scope()
        
        if callable.annotation != None and return_type != callable.annotation:
            self.errors.append("")
        
        return BaseSimpleType.VOID_TYPE

    def visit_BaseASTCall(self, call):
        if call.id.text != "print":
            raise Exception("Invalid Call")
        call.args[0].accept(self)

    def visit_BaseASTFunction(self, func):
        return None
   