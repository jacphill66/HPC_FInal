import parsing, base_ast_objects, Values, op_codes

class Local:
    def __init__(self, offset, func_id, func_index):
        self.offset = offset
        self.func_id = func_id
        self.func_index = func_index
        self.is_up_value = False

class UpValue:
    def __init__(self, id, index, is_local):
        self.id = id
        self.index = index
        self.is_local = is_local
    
    def __str__(self):
        return f"UpValue[{self.id}, {self.index}, {self.is_local}]"

class Function:
    def __init__(self, id):
        self.id = id
        self.up_values = {}
        self.up_value_count = 0
        
    def add_up_value(self, local_id, offset_or_index, is_local):
        if local_id in self.up_values:
            raise Exception("Up Value Already Exisits!")
        self.up_values[local_id] = (UpValue(local_id, offset_or_index, is_local), self.up_value_count)
        self.up_value_count += 1
        return self.up_value_count - 1
        
    def get_up_value_index(self, local_id):
        return self.up_values[local_id][1]
    
    def __str__(self):
        up_vals = "["
        for v_id in self.up_values:
            v, index = self.up_values[v_id]
            
            up_vals += f"{str(v)} at: {index}, "
        up_vals += "]"
        return f"Func[{self.id}, UpValues:{up_vals}]"
    
class BaseCompiler:
    def __init__(self, ast):
        self.ast = ast
        self.error = None
        
        self.op_addr = 0
        self.op_code_size = 64
        self.op_codes = bytearray(64)
        
        self.consts = []
        self.const_index = 0
        
        self.static_objs = []
        self.static_obj_index = 0
        
        self.local_offset = 0
        self.scope_depth = -1
        self.scopes = []
        self.function_depth = 0
        self.function_stack = ["*main"]
        self.function_map = {}
        
        self.static_globals = {}
        self.static_global_addr = 0
        
        self.EXPRESSION_NODE_TYPES = (base_ast_objects.BaseASTIdentifier, base_ast_objects.BaseASTInt, base_ast_objects.BaseASTFloat, base_ast_objects.BaseASTBool, base_ast_objects.BaseASTNull, base_ast_objects.BaseASTString, base_ast_objects.BaseASTBinaryOp, base_ast_objects.BaseASTUnaryOp, base_ast_objects.BaseASTCall)
    
    def outer_func(self):
        if self.function_depth < 1:
            return "*main"
        else:
            return self.function_stack[self.function_depth-1]
            
    def curr_func(self):
        if self.function_depth == -1:
            return "*main"
        else:
            return self.function_stack[self.function_depth]

    def resolve_up_value(self, local_id, local):
        i = local.func_index
        i += 1
        curr_func = self.function_stack[i]
        
        index = None
        
        if not local_id in self.function_map[curr_func].up_values:
            index = self.function_map[curr_func].add_up_value(local_id, local.offset, True) 
        else:
            index = self.function_map[curr_func].up_values[local_id][1]      
                       
        i += 1
        
        while i <= self.function_depth:
            curr_func = self.function_stack[i]
            
            if not local_id in self.function_map[curr_func].up_values:
                index = self.function_map[curr_func].add_up_value(local_id, index, False)
            else:
                index = self.function_map[curr_func].up_values[local_id][1]
                    
            i += 1
            
        return index        
    
    def resolve_reference(self, id, line):
        local = self.resolve_local(id)
        if type(local) == Local:        
            curr_func = self.curr_func()
            if curr_func == "*main" or curr_func == local.func_id:
                return "local", local.offset
            else:
                index = None
                if not id in self.function_map[curr_func].up_values:
                    local.is_up_value = True
                    index = self.resolve_up_value(id, local)
                else:
                    index = self.function_map[curr_func].get_up_value_index(id)
                return "up_value", index
        else:
            if id in self.static_globals:
                return "global", self.static_globals[id]      
            else:
                raise Exception("Invalid Variable", line)
                
    def emit_op(self, op):
        if self.op_addr + 1 == self.op_code_size:
            self.op_codes += b"\x00" * (self.op_code_size)
            
        if type(op) == op_codes.OpCode:
            self.op_codes[self.op_addr:self.op_addr+1] = (op.value).to_bytes(1, byteorder="little")
            self.op_addr += 1
            return self.op_addr-1
        else:
            self.op_codes[self.op_addr:self.op_addr+8] = Values.python_repr_to_value(op)
            self.op_addr += 8
            return self.op_addr - 8 
    
    def emit_const(self, const):
        self.emit_op(op_codes.OpCode.CONST)
        self.emit_op(self.const_index)
        self.const_index += 1
        self.consts.append(const)

    def emit_static_obj(self, obj, op):
        self.emit_op(op) 
        self.emit_op(self.static_obj_index)
        self.static_objs.append(obj)
        self.static_obj_index += 1
        
    def new_scope(self):
        self.scope_depth += 1
        self.scopes.append({})
    
    def close_scope(self):
        self.scope_depth -= 1
        return self.scopes.pop()
    
    def clear_scope(self):
        scope = self.close_scope()
        sorted_scope = dict(sorted(scope.items(), key=lambda item: item[1].offset, reverse=True))
        for id in sorted_scope:
            if scope[id].is_up_value:
                self.emit_op(op_codes.OpCode.CLOSE_UP_VALUE)
            else:
                self.emit_op(op_codes.OpCode.POP)
            self.local_offset -= 8

    def visit_BaseASTIdentifier(self, id):
        op_type, index = self.resolve_reference(id.text, id.line)
        if op_type == "local":
            self.emit_op(op_codes.OpCode.GET_LOCAL)
        elif op_type == "global":
            self.emit_op(op_codes.OpCode.GET_STATIC_GLOBAL)
        elif op_type == "up_value":
            self.emit_op(op_codes.OpCode.GET_UP_VALUE)
        else:
            raise Exception("Invalid Reference Type!")
        self.emit_op(index)
           
    def visit_BaseASTInt(self, i):
        self.emit_const(Values.python_repr_to_value(i.value))
        
    def visit_BaseASTFloat(self, f):
        self.emit_const(Values.python_repr_to_value(f.value))

    def visit_BaseASTBool(self, b):
        self.emit_const(Values.python_repr_to_value(b.value))

    def visit_BaseASTNull(self, n):
        self.emit_op(op_codes.OpCode.NULL)

    def emit_static_string(self, s):
        obj = bytearray(8 + len(s))
        obj[0] = Values.StaticObjectType.STATIC_STRING.value
        obj[4:8] = len(s).to_bytes(4, byteorder='little')
        obj[8:] = s.encode('utf-8')
        self.emit_static_obj(obj, op_codes.OpCode.STATIC_STR)

    def visit_BaseASTString(self, s):       
        self.emit_static_string(s.value)
        
    def visit_BaseASTBinaryOp(self, expr):
        expr.rhs.accept(self)
        expr.lhs.accept(self)
        
        op = expr.op
        if op == "+":
            self.emit_op(op_codes.OpCode.SUM)
        elif op == "-":
            self.emit_op(op_codes.OpCode.SUB)
        elif op == "*":
            self.emit_op(op_codes.OpCode.MULT)
        elif op == "/":
            self.emit_op(op_codes.OpCode.DIV)
        elif op == "%":
            self.emit_op(op_codes.OpCode.MOD)
        elif op == "<":
            self.emit_op(op_codes.OpCode.LESS_THAN)
        elif op == ">":
            self.emit_op(op_codes.OpCode.GREATER_THAN)
        elif op == "<=":
            self.emit_op(op_codes.OpCode.LESS_THAN_EQ)
        elif op == ">=":
            self.emit_op(op_codes.OpCode.GREATER_THAN_EQ)   
        elif op == "==":
            self.emit_op(op_codes.OpCode.EQUAL)  
        elif op == "&&":
            self.emit_op(op_codes.OpCode.AND)
        elif op == "||":
            self.emit_op(op_codes.OpCode.OR)
        elif op == "^":
            self.emit_op(op_codes.OpCode.EXPONENT)
        elif op == "!!":
            self.emit_op(op_codes.OpCode.POP_KEY_STRUCT)
        else:
            raise Exception(f"Attempting to Compile Invalid Binary Operation: {op}", expr.line)
    
    def visit_BaseASTUnaryOp(self, expr):
        expr.expr.accept(self)
        
        op = expr.op
        if expr.prefix and op == "-":
            self.emit_op(op_codes.OpCode.NEGATIVE)
        elif expr.prefix and op == "!":
            self.emit_op(op_codes.OpCode.NEGATE)
        elif not expr.prefix and op == "!":
            self.emit_op(op_codes.OpCode.POP_BACK)
        elif not expr.prefix and op == "#":
            self.emit_op(op_codes.OpCode.STRUCT_SIZE)
        else:
            raise Exception(f"Attempting to Compile Invalid Unary Operation: {op}", expr.line)
    
    def visit_BaseASTExprStatement(self, expr):
        expr.expr.accept(self)
        if type(expr.expr) in self.EXPRESSION_NODE_TYPES:
            self.emit_op(op_codes.OpCode.POP)
        
    def visit_BaseASTBlock(self, block):
        self.new_scope()
        for s in block.statements:
            s = s.accept(self)
        self.clear_scope()

    def visit_BaseASTCall(self, call):
        if type(call.id) == base_ast_objects.BaseASTIdentifier and call.id.text == "print":
            call.args[0].accept(self)
            self.emit_op(op_codes.OpCode.OUT)
        else:
            i = 0
            for arg in call.args:
                arg.accept(self)
                i += 1
            call.id.accept(self)
            self.emit_op(op_codes.OpCode.CALL)
            self.emit_op(i)

    def visit_BaseASTWhile(self, w):
        start = self.op_addr
        w.cond.accept(self)
        self.emit_op(op_codes.OpCode.FALSE_JUMP)
        fill1 = self.emit_op(-1)
        w.statement.accept(self)
        self.emit_op(op_codes.OpCode.JUMP_BACK)
        self.emit_op(self.op_addr - start)
        self.op_codes[fill1:fill1+8] = Values.python_repr_to_value(self.op_addr - fill1)
    
    def visit_BaseASTIf(self, i):
        i.expr.accept(self)
        self.emit_op(op_codes.OpCode.FALSE_JUMP)
        fill1 = self.emit_op(-1)
        i.statement.accept(self)
        if i.else_statement != None:
            self.emit_op(op_codes.OpCode.JUMP) 
            fill2 = self.emit_op(-1)
        self.op_codes[fill1:fill1+8] = Values.python_repr_to_value(self.op_addr - fill1)
        if i.else_statement != None:
            i.else_statement.accept(self)
            self.op_codes[fill2:fill2+8] = Values.python_repr_to_value(self.op_addr - fill2)

    def emit_local(self, id):
        self.scopes[self.scope_depth].update({id:Local(self.local_offset, self.function_stack[self.function_depth], self.function_depth)}) 
        self.local_offset += 8

    def resolve_local(self, id):
        depth = self.scope_depth
        while depth >= 0:
            if id in self.scopes[depth]:
                return self.scopes[depth][id]
            depth -= 1
        return None

    def compile_up_values(self, f_id):
        up_values = self.function_map[f_id].up_values
        for v_id in up_values:
            v = up_values[v_id][0]
            self.emit_op(v.index)
            self.emit_op(v.is_local)
        return len(up_values)

    def compile_function_object(self, f):
        og_op_addr = self.op_addr
        og_op_code_size = self.op_code_size 
        og_op_codes = self.op_codes 

        self.op_addr = 8
        self.op_code_size = 64
        self.op_codes = bytearray(64)

        self.op_codes[0] = Values.StaticObjectType.STATIC_FUNC.value
  
        self.emit_op(len(f.params))
        old_offset = self.compile_params(f.params)

        f.body.accept(self)
        
        self.op_codes[4:8] = self.op_addr.to_bytes(4, byteorder='little')
        
        self.static_objs.append(self.op_codes)
        self.static_obj_index += 1
        
        self.op_addr = og_op_addr
        self.op_code_size = og_op_code_size
        self.op_codes = og_op_codes
        
        static_ref = bytearray(8)
        static_ref[0] = Values.ValueType.STATIC_OBJ.value
        static_ref[4:8] = (self.static_obj_index-1).to_bytes(4, byteorder="little")

        self.emit_const(static_ref)
       
        return old_offset

    def visit_BaseASTCallable(self, f):    
        """
        Compiles a new function object stored on the heap
        """       
        self.emit_const(Values.python_repr_to_value(None))
        
        if type(f.id) != base_ast_objects.BaseASTIdentifier:
            raise Exception("Function Name Must be an Identifier!")
        
        self.emit_variable(f.id.text) 
                
        self.function_depth += 1
        self.function_map.update({f.id.text:Function(f.id.text)})
        self.function_stack.append(f.id.text)
                        
        old_offset = self.compile_function_object(f)
        
        if len(self.function_map[f.id.text].up_values) > 0:
            self.emit_static_string(f.id.text)
            self.emit_op(op_codes.OpCode.NEW_CLOSURE)
            self.emit_op(len(self.function_map[f.id.text].up_values))
            self.emit_op(True)
            self.compile_up_values(f.id.text)  
            
        self.close_scope()
        self.function_stack.pop()
        self.function_depth -= 1
        self.local_offset = old_offset  
         
        self.update_variable(f.id.text, f.line)

    def update_variable(self, id, line):
        op_type, index = self.resolve_reference(id, line)
        if op_type == "local":
            self.emit_op(op_codes.OpCode.SET_LOCAL)
            self.emit_op(index)
        elif op_type == "up_value":
            self.emit_op(op_codes.OpCode.SET_UP_VALUE)
            self.emit_op(index)
        elif op_type == "global":
            self.emit_op(op_codes.OpCode.SET_STATIC_GLOBAL)
            self.emit_op(index)
        else:
            raise Exception("Invalid Variable Assignment!")

    def emit_static_global(self, id):
        self.emit_op(op_codes.OpCode.SET_STATIC_GLOBAL)
        self.emit_op(self.static_global_addr)
        self.static_globals.update({id:self.static_global_addr})
        self.static_global_addr += 8         
    
    def emit_variable(self, id):
        if self.scope_depth == -1:
            self.emit_static_global(id)
        else:
            self.emit_local(id)
    
    def visit_BaseASTVariableDeclaration(self, v):
        v.expr.accept(self)
        self.emit_variable(v.id.value)
        
    def rewrite_assignment(self, update):
        if update.op.value == "=":
            return update
        elif update.op.value[0] in ("+", "-", "*", "/", "%"):
            update.expr1 = base_ast_objects.BaseASTBinaryOp(update.ref, update.op.value[0], update.expr1, update.line) 
            return update
        else:
            raise Exception("Attempting to Rewrite Invalid Assignment Operator!", update.line)
    
    def visit_BaseASTStructOp(self, insert):
        insert.ref.accept(self)
        if insert.op == "<<" and insert.value != None:
            insert.key_or_value.accept(self)
            insert.value.accept(self)
            self.emit_op(op_codes.OpCode.INSERT_TABLE)
        elif insert.op == "<<" and insert.value == None:
            insert.key_or_value.accept(self)
            self.emit_op(op_codes.OpCode.PUSH_BACK_ARRAY)
        else:
            raise Exception("Invalid Structure Insert!", insert.line)   

    def visit_BaseASTStructModify(self, mod):
        mod.ref.struct.accept(self)
        mod.ref.key_or_index.accept(self)
        mod.value.accept(self)
        self.emit_op(op_codes.OpCode.MODIFY_STRUCT)
    
    def visit_BaseASTUpdateStatement(self, update):
        ASSIGNMENT_OPS = ("=", "+=", "-=", "*=", "/=", "%=")
        if type(update.ref) == base_ast_objects.BaseASTIdentifier and update.op.value in ASSIGNMENT_OPS:
            update = self.rewrite_assignment(update)
            update.expr1.accept(self)
            self.update_variable(update.ref.text, update.line)
        elif type(update) == base_ast_objects.BaseASTStructRef and update.op.value in ASSIGNMENT_OPS:
            pass
        elif type(update.op) == base_ast_objects.BaseASTIdentifier and update.op.value in ASSIGNMENT_OPS:
            pass
        elif type(update.op) == base_ast_objects.BaseASTIdentifier and update.op.value == "<<":
            update.ref.accept(self)
            if update.expr2 != None:
                update.expr1.accept(self)
                update.expr2.accept(self)
                self.emit_op(op_codes.OpCode.INSERT_TABLE)
            else:
                update.expr1.accept(self)
                self.emit_op(op_codes.OpCode.PUSH_BACK_ARRAY)            
        else:
            raise Exception("Invalid Update Operation!")
    
    def visit_BaseASTVariableAssignment(self, ass):
        if ass.id != base_ast_objects.BaseASTIdentifier:
            raise Exception("Variable Assignments Must use Valid Identifiers!")
        ass = self.rewrite_assignment(ass)
        ass.expr.accept(self)
        self.update_variable(ass.id.text, ass.line)
    
    def compile_new_struct(self, struct_op, flags):
        self.emit_op(struct_op)
        for flag in flags:
            self.emit_op(flag)
        
    def compile_keyed_elements(self, keys, elements):
        i = 0
        while i < len(elements):
            keys[i].accept(self)
            elements[i].accept(self)
            i += 1
    
    def compile_elements(self, elements):
        i = len(elements)-1
        while i >= 0:
            elements[i].accept(self)
            self.emit_const(Values.python_repr_to_value(i))
            i -= 1
    
    def compile_curly_brackets(self, keys, elements):
        if len(elements) > 0:
            self.compile_keyed_elements(keys, elements)
            self.compile_new_struct(op_codes.OpCode.NEW_TABLE, [len(elements), True, False, True])
        else:
            self.compile_elements(keys)
            self.compile_new_struct(op_codes.OpCode.NEW_ARRAY, [len(keys), True, False, True])
    
    def compile_square_brackets(self, keys, elements):
        if len(elements) > 0:
            self.compile_keyed_elements(keys, elements, op_codes.OpCode.NEW_STRUCT, [])
        else:
            self.compile_elements(elements, op_codes.OpCode.NEW_ARRAY)
     
    def compile_alligator_brackets(self, keys, elements):
        if len(elements) > 0:
            if type(elements[0]) == base_ast_objects.BaseASTEmtpyElement:
                self.compile_keyed_elements(keys, elements, op_codes.OpCode.NEW_SET, [])
            else:
                self.compile_keyed_elements(keys, elements)
                self.compile_new_struct(op_codes.OpCode.NEW_PRIORITY_QUEUE, [len(elements), True, True, True])
        else:
            self.compile_elements(elements, NEW_DEQUE)
    
    def compile_paren_brackets(self, keys, elements):
        if len(elements) > 0:
            self.compile_keyed_elements(keys, elements, NEW_RECORD, [])
        else:
            self.compile_elements(elements, NEW_TUPLE)

    def visit_BaseASTStruct(self, s):            
        if s.open_bracket == "{":
            self.compile_curly_brackets(s.keys, s.elements)
        elif s.open_bracket == "[":
            self.compile_square_brackets(s.keys, s.elements)
        elif s.open_bracket == "<|":
            self.compile_alligator_brackets(s.keys, s.elements)
        elif s.open_bracket == "(":
            self.compile_paren_brackets(s.keys, s.elements)
        else:
            raise Exception("Attempting to Compile Invalid Structure", s.line)
    
    def visit_BaseASTStructRef(self, acc):
        acc.struct.accept(self)
        acc.key_or_index.accept(self)
        self.emit_op(op_codes.OpCode.ACCESS_STRUCT)
            
    def visit_BaseASTRepeat(self, r):
        pass
    
    def visit_BaseASTReturn(self, r):
        r.expr.accept(self)
        self.emit_op(op_codes.OpCode.RETURN)

    def compile_params(self, params):
        old_offset = self.local_offset
        self.local_offset = 0    
        self.new_scope()
        for p in params:
            if type(p[0]) != base_ast_objects.BaseASTIdentifier:
                raise Exception("Parameter Names Must be Valid Identifiers!")
            self.emit_variable(p[0].text)
        return old_offset       
    
    def compile(self):
        for s in self.ast:
            s.accept(self)
        self.emit_op(op_codes.OpCode.STOP)
        
        for f_id in self.function_map:
            print(self.function_map[f_id])
        return self.op_codes, self.consts, self.static_objs

    def print_ops(self):
        i = 0
        print("[", end="")
        while i < len(self.op_codes):
            if self.op_codes[i] == op_codes.OpCode.CONST.value:
                i += 4
                print(f"Const[{self.consts[Values.value_to_python_repr(self.op_codes[i])]}]", end=",")
            elif self.op_codes[i] == op_codes.OpCode.STATIC_STR.value:
                i += 4
                print(f"StaticStr[{self.static_objs[Values.value_to_python_repr(self.op_codes[i])]}]", end=",")
            else:
                print(self.op_codes[i], end=",")
                i += 4
        print("]")

    def visit_BaseASTSequence(self, seq):
        for s in seq.statements:
            s.accept(self)