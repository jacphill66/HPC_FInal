
import heaping, compiling, Values, op_codes


"""
A value is a tagged union consisting of an: int, float, char, bool, null, a static obj or or a heap object. Its formatted as 8 bytes: 4 bytes of type and padding, 4 bytes of payload. The stack is an array of values.
"""

class UpValue:
    def __init__(self, addr, stack_addr):
        self.addr = addr
        self.stack_addr = stack_addr

    def __str__(self):
        return f"UpValue[{self.stack_addr}]"

class UpValueList:
    def __init__(self, stack, heap_manager, up_val=None, next=None, stack_addr=None):
        self.up_val = up_val
        self.next = next
        self.stack = stack
        self.heap_manager = heap_manager
        self.stack_addr = stack_addr
    
    def insert(self, up_val, stack_addr):
        if self.up_val == None:
            self.up_val = up_val
            self.stack_addr = stack_addr
            return self
        else:
            n = self
            if n.stack_addr <= stack_addr:
                return UpValueList(self.stack, self.heap_manager, up_val, n, stack_addr)
            else:
                while n.next != None and n.next.stack_addr > stack_addr:
                    n = n.next
                n.next = UpValueList(self.stack, self.heap_manager, up_val, n.next, stack_addr)
                return self

    def close_up_values(self, stack_addr):
        if self.up_val == None:
            return
        else:
            n = self
            while n != None and n.stack_addr >= stack_addr:
                curr_stack_addr = n.stack_addr
                ref = self.heap_manager.new_dynamic_up_value(self.stack[n.stack_addr:n.stack_addr+8], True)
                while n != None and n.stack_addr == curr_stack_addr:
                    self.heap_manager.close_up_value(n.up_val.addr, ref)
                    
                    if n.next == None or (n.next != None and n.next.stack_addr != curr_stack_addr):
                    
                        break
                    
                    n = n.next
                    
                n = n.next
            if n == None:
                return UpValueList(self.stack, self.heap_manager)
            else:
                return n
    
    def __str__(self):
        if self.up_val == None:
            print("Empty Up Value List")
        else:
            string = ""
            n = self
            while n != None:
                string += str(n.up_val) + ","
                n = n.next
        return string
            
class CallFrame:
    def __init__(self, ops, ip_addr, arity, func_val, func_id, offset, is_closure):
        self.ops = ops
        self.ip_addr = ip_addr
        self.arity = arity
        self.func_val = func_val
        self.func_id = func_id
        self.offset = offset
        self.is_closure = is_closure
    
    def __str__(self):
        c_str = "CallFrame["
        c_str += self.func_id
        c_str += ","
        c_str += str(self.offset)
        c_str += ", "
        c_str += str(self.arity)
        c_str += "]"
        return c_str
    
    def __repr__(self):
        return str(self)

class VM:
    def __init__(self, stack_size, ops, const_pool, static_objs):      
        # stack of 8 byte slots of values
        self.stack = bytearray(8 * stack_size)
        # instruction pointer, points to the current operation
        self.ip_addr = 0
        # an array of opcodes representing operations
        self.ops = ops
        
        self.closure_stack = []
        
        # Used by functions
        self.func_val = None
        self.func_id = "main"
        self.arity = 0
        self.offset = 0
        self.is_closure = False
        
        # Call stack
        self.call_stack = []
        
        # constants (literals) used in the program
        self.const_pool = const_pool
        self.static_objs = static_objs
        # heap
        self.heap_manager = heaping.HeapManager(8*2048, 8*2048, len(static_objs), static_objs)
        self.up_values = UpValueList(self.stack, self.heap_manager)

        # points to the (available) top of the stack
        self.stack_ptr = 0
        # the size of the stack
        self.stack_size = stack_size
    
    def close_up_value(self):
        n = self.up_values
        ref = self.heap_manager.new_dynamic_up_value(self.pop(), True)
        curr_stack_addr = self.stack_ptr
        while n != None and n.stack_addr == curr_stack_addr:
            self.heap_manager.close_up_value(n.up_val.addr, ref)        
            n = n.next
        if n == None:
            return UpValueList(self.stack, self.heap_manager)
        else:
            return n
    
    def get_outer_func(self):
        if len(self.closure_stack) > 0:
            # Return a value representing the outer closure
            return self.closure_stack[len(self.closure_stack)-1]
        else:
            # Otherwise return NULL value
            return bytearray(8)
    
    def next_instruction(self):
        op = self.ops[self.ip_addr:self.ip_addr+1]
        self.ip_addr += 1
        return op
    
    def push(self, val):
        if self.stack_ptr >= self.stack_size:
            raise Exception("Stack Overflow!")
        self.stack[self.stack_ptr:self.stack_ptr+8] = val
        self.stack_ptr += 8
    
    def pop(self):
        self.stack_ptr -= 8
        if self.stack_ptr < 0:
            raise Exception("Stack Underflow!")
        return self.stack[self.stack_ptr:self.stack_ptr+8]
    
    def push_const(self):
        self.push(self.const_pool[Values.value_to_python_repr(self.ops[self.ip_addr:self.ip_addr+8])])
        self.ip_addr += 8
    
    def push_str(self):
        val_ref = self.heap_manager.load_static_string(self.static_objs[Values.value_to_python_repr(self.ops[self.ip_addr:self.ip_addr+8])], Values.value_to_python_repr(self.ops[self.ip_addr:self.ip_addr+8]))
        self.push(val_ref)
        self.ip_addr += 8
    
    def set_static_global(self):
        self.heap_manager.set_static_global(Values.value_to_python_repr(self.ops[self.ip_addr:self.ip_addr+8]), self.pop())
        self.ip_addr += 8
    
    def set_local(self):
        index = self.offset + Values.value_to_python_repr(self.ops[self.ip_addr:self.ip_addr+8])
        self.stack[index:index+8] = self.pop()
        self.ip_addr += 8
    
    def get_static_global(self):
        self.push(self.heap_manager.get_static_global(Values.value_to_python_repr(self.ops[self.ip_addr:self.ip_addr+8])))  
        self.ip_addr += 8

    def get_local(self):
        index = self.offset + Values.value_to_python_repr(self.ops[self.ip_addr:self.ip_addr+8])
        self.push(self.stack[index:index+8])
        self.ip_addr += 8        
    
    def outer_offset(self):
        # used for getting the outer function when initializing closures
        return self.call_stack[len(self.call_stack)-1].offset
    
    def num_binary_op(self, op):
        # need to handle the case where the result isn't an int
        new_val = bytearray(8)
        o1 = self.pop()
        o2 = self.pop()
        v1 = Values.value_to_python_repr(o1)
        v2 = Values.value_to_python_repr(o2)
        res = None
        if op == op_codes.SUM:
            res = v1 + v2
        elif op == op_codes.SUB:
            res = v1 - v2
        elif op == op_codes.MULT:
            res = v1 * v2
        elif op == op_codes.DIV:
            res = v1 / v2
        elif op == op_codes.MOD:
            res = v1 % v2
        elif op == op_codes.EXPONENT:
            res = v1 ** v2
        else:
            raise Exception("Invalid Operation!")
        new_val = Values.python_repr_to_value(res)
        self.push(new_val)
        
    def factorial(self, i):
        if i == 1:
            return i
        return i * self.factorial(i-1)
    
    def num_unary_op(self, op):
        new_val = bytearray(8)
        o = self.pop()
        v = Values.value_to_python_repr(o)
        res = None
        if op == op_codes.FACTORIAL:
            res = self.factorial(v)
        elif op == op_codes.NEGATIVE:
            res = -v
        else:
            raise Exception("Invalid Integer Unary Op!")
        self.push(Values.python_repr_to_value(res))
        
    def bool_binary_op(self, op):
        new_val = bytearray(8)
        o1 = self.pop()
        o2 = self.pop()            
        
        res = None
        v1 = bool(int.from_bytes(o1[4:], byteorder='little'))
        v2 = bool(int.from_bytes(o2[4:], byteorder='little'))
        if op == op_codes.AND:
            res = v1 and v2
        elif op == op_codes.OR:
            res = v1 or v2
        else:
            raise Exception("Invalid Operation!")
        new_val[0] = Values.ValueType.BOOL.value
        new_val[4:] = int(res).to_bytes(4, byteorder='little')
        self.push(new_val)
    
    def boolean_unary_op(self, op):
        new_val = bytearray(8)
        o = self.pop()
        v = bool(int.from_bytes(o[4:], byteorder='little'))
        res = None
        if op == op_codes.NEGATE:
            res = not v
        else:
            raise Exception("Invalid Unary Boolean Operator!")
        new_val[0] = Values.ValueType.BOOL.value
        new_val[4:] = int(res).to_bytes(4, byteorder='little')
        self.push(new_val)

    def comparison_op(self, op):
        new_val = bytearray(8)
        o1 = self.pop()
        o2 = self.pop()
        res = None
        if op == op_codes.EQUAL:
            res = Values.compare_values(o1, o2, self.heap_manager)
        elif op == op_codes.GREATER_THAN:
            res = Values.greater_than(o1, o2, self.heap_manager)
        elif op == op_codes.LESS_THAN:
            res = Values.less_than(o1, o2, self.heap_manager)
        self.push(Values.python_repr_to_value(res))
    
    def push_null(self):
        # byte arrays default to 0b00000... (null)
        n = bytearray(8)
        self.push(n)
    
    def new_table(self):    
        cappacity = Values.value_to_python_repr(self.ops[self.ip_addr:self.ip_addr+8])
        self.ip_addr += 8
        resizable = Values.value_to_python_repr(self.ops[self.ip_addr:self.ip_addr+8])
        self.ip_addr += 8
        is_set = Values.value_to_python_repr(self.ops[self.ip_addr:self.ip_addr+8])
        self.ip_addr += 8
        gc = Values.value_to_python_repr(self.ops[self.ip_addr:self.ip_addr+8])
        self.ip_addr += 8

        table_value = self.heap_manager.new_table(cappacity, resizable, is_set, gc)
        
        i = 0
        while i < cappacity:
            el = self.pop()
            key = self.pop()
            self.heap_manager.add_table(table_value, key, el)
            i += 1
        self.push(table_value)

    def new_array(self):
        cappacity = Values.value_to_python_repr(self.ops[self.ip_addr:self.ip_addr+8])
        self.ip_addr += 8
        resizable = Values.value_to_python_repr(self.ops[self.ip_addr:self.ip_addr+8])
        self.ip_addr += 8
        immutable = Values.value_to_python_repr(self.ops[self.ip_addr:self.ip_addr+8])
        self.ip_addr += 8
        gc = Values.value_to_python_repr(self.ops[self.ip_addr:self.ip_addr+8])
        self.ip_addr += 8
        arr_val = self.heap_manager.new_array(cappacity, resizable, immutable, gc)
        i = 0
        while i < cappacity:
            index = self.pop()
            el = self.pop()
            self.heap_manager.arr_push_back(arr_val, el)
            i += 1
        self.push(arr_val)
        
    def insert_table(self):
        val = self.pop()
        key = self.pop()
        struct = self.pop()
        self.heap_manager.add_table(struct, key, val) 
    
    def push_back_arr(self):
        val = self.pop()
        arr = self.pop()
        self.heap_manager.arr_push_back(arr, val)
    
    def pop_back(self):
        arr = self.pop()
        res = self.heap_manager.struct_pop_back(arr)
        self.push(res)
    
    def modify_structure(self):
        val = self.pop()
        key = self.pop()
        struct = self.pop()
        self.heap_manager.modify_structure(struct, key, val) 
    
    def access_struct(self):
        key = self.pop()
        struct = self.pop()
        res = self.heap_manager.access_structure(struct, key)
        self.push(res)
    
    def struct_size(self):
        struct = self.pop()
        res = self.heap_manager.struct_size(struct)
        self.push(res)
    
    def pop_key_struct(self):
        struct = self.pop()
        key = self.pop()
        res = self.heap_manager.pop_key_structure(struct, key)
        self.push(res)
        
    def new_priority_queue(self):
        cappacity = Values.value_to_python_repr(self.ops[self.ip_addr:self.ip_addr+8])
        self.ip_addr += 8
        resizable = Values.value_to_python_repr(self.ops[self.ip_addr:self.ip_addr+8])
        self.ip_addr += 8
        using_map = Values.value_to_python_repr(self.ops[self.ip_addr:self.ip_addr+8])
        self.ip_addr += 8
        gc = Values.value_to_python_repr(self.ops[self.ip_addr:self.ip_addr+8])
        self.ip_addr += 8
        queue_val = self.heap_manager.new_priority_queue(resizable, using_map, cappacity, gc)
        i = 0
        while i < cappacity:
            priority = self.pop()
            key = self.pop()
            self.heap_manager.insert_priority_queue(queue_val, key, priority)
            i += 1
        self.push(queue_val)
    
    def get_up_value(self):
        index = Values.value_to_python_repr(self.ops[self.ip_addr:self.ip_addr+8])
        self.ip_addr += 8
        val = self.heap_manager.get_up_value(self.func_val, index, self.stack)
        self.push(val)
    
    def set_up_value(self):
        val = self.pop()
        index = Values.value_to_python_repr(self.ops[self.ip_addr:self.ip_addr+8])
        self.ip_addr += 8
        self.heap_manager.set_up_value(self.func_val, val, index, self.stack)
        
    def static_func(self):
        id_val = self.pop()
        arity = Values.value_to_python_repr(self.ops[self.ip_addr:self.ip_addr+8])
        self.ip_addr += 8
        
        up_value_count = Values.value_to_python_repr(self.ops[self.ip_addr:self.ip_addr+8])
        self.ip_addr += 8
        
        body_size = Values.value_to_python_repr(self.ops[self.ip_addr:self.ip_addr+8])
        self.ip_addr += 8
        
        gc = Values.value_to_python_repr(self.ops[self.ip_addr:self.ip_addr+8])
        self.ip_addr += 8
        
        # Create a new function object
        func_val = self.heap_manager.new_function(id_val, arity, body_size, up_value_count, gc)
        
        # Read in 
        addr, size, id_val, arity, body_size, up_value_count, gc = self.heap_manager.read_function_header(func_val)

        # Write the operations
        self.ip_addr = self.heap_manager.load_function(addr, body_size, up_value_count, self.ops, self.ip_addr)
        # Push the function object to the stack

        self.push(func_val)
        
    def call(self):
        call_arity = Values.value_to_python_repr(self.ops[self.ip_addr:self.ip_addr+8])
        self.ip_addr += 8        
        func_val = self.pop()   
        self.func_val = func_val        
        self.is_closure = False
        if func_val[0] == Values.ValueType.HEAP_OBJ.value:
            self.closure_stack.append(func_val)
            addr, size, id_val, func_val, up_value_count, gc = self.heap_manager.read_closure_header(func_val)
            self.is_closure  = True
                   
        self.call_stack.append(CallFrame(self.ops, self.ip_addr, self.arity, self.func_val, self.func_id, self.offset, self.is_closure))
        self.offset = self.stack_ptr - (call_arity * 8)      

        index = int.from_bytes(func_val[4:], byteorder="little")

        self.ops = self.static_objs[index][16:]

        self.ip_addr = 0
        self.arity = call_arity
        self.func_id = ""
        
            
    def return_call(self):    
        ret_val = self.pop()                
        
        self.stack_ptr = self.offset
        
        if self.up_values != None:
            self.up_values = self.up_values.close_up_values(self.offset)
        
        self.push(ret_val)
        
        frame = self.call_stack.pop()
         
        if frame.is_closure:
            self.closure_stack.pop()
                
        self.ops = frame.ops
        self.ip_addr = frame.ip_addr
        self.arity = frame.arity
        self.func_val = frame.func_val
        self.func_id = frame.func_id
        self.offset = frame.offset      
        self.is_closure = frame.is_closure
        
    def end_function(self):
        pass
    
    def stack_to_string(self):
        stack_str = "|"
        
        if self.stack_ptr == 0:
            return "Empty"
        
        i = 0
        while i < self.stack_ptr:
            stack_str += Values.value_to_string(self.stack[i:i+8], self.heap_manager.static_objs, self.heap_manager)
            stack_str += "|"
            i += 8
        return stack_str

    def print_stack(self):
        print(self.stack_to_string())
    
    def new_closure(self):
        outer_func = self.get_outer_func()  
        

        id_val = self.pop()
        func_val = self.pop()
        up_value_count = Values.value_to_python_repr(self.ops[self.ip_addr:self.ip_addr+8])
        self.ip_addr += 8
        gc = Values.value_to_python_repr(self.ops[self.ip_addr:self.ip_addr+8])
        self.ip_addr += 8
        
        closure_val = self.heap_manager.new_closure(id_val, func_val, up_value_count, gc)

        addr, size, id_val, func_val, up_value_count, gc = self.heap_manager.read_closure_header(closure_val)
                
        i = 0
        addr += 28
        while i < up_value_count:
            index_or_offset = Values.value_to_python_repr(self.ops[self.ip_addr:self.ip_addr+8])
            is_local = Values.value_to_python_repr(self.ops[self.ip_addr+8:self.ip_addr+16])
            
            if is_local:
                stack_addr = index_or_offset + self.offset
                self.heap_manager.load_up_value(addr, Values.python_repr_to_value(stack_addr), self.ops[self.ip_addr+8:self.ip_addr+16], bytearray(b'\x02\x00\x00\x00\x00\x00\x00\x00'))
                self.up_values = self.up_values.insert(UpValue(addr, stack_addr), stack_addr)
                
            else:
                outer_addr, outer_size, outer_id_val, outer_func_val, outer_up_value_count, outer_gc = self.heap_manager.read_closure_header(outer_func)
                                
                outer_up_val_addr = outer_addr + 28 + (index_or_offset * 24)
                
                if not self.heap_manager.is_closed(outer_up_val_addr):
                
                    stack_addr = Values.value_to_python_repr(self.heap_manager.index_or_offset(outer_up_val_addr))
                    
                    self.up_values = self.up_values.insert(UpValue(addr, stack_addr), stack_addr)
                    
                    self.heap_manager.load_up_value(addr, self.heap_manager.index_or_offset(outer_up_val_addr), self.ops[self.ip_addr+8:self.ip_addr+16], bytearray(b'\x02\x00\x00\x00\x00\x00\x00\x00'))
                else:
                    self.heap_manager.load_up_value(addr, self.heap_manager.index_or_offset(outer_up_val_addr), self.ops[self.ip_addr+8:self.ip_addr+16], bytearray(b'\x02\x00\x00\x00\x10\x00\x00\x00'))

            self.ip_addr += 16
            addr += 24
            i += 1
        self.push(closure_val)
        

        
    def execute_instruction(self, op):
            if op == op_codes.SUM:
                self.num_binary_op(op)
            elif op == op_codes.SUB:
                self.num_binary_op(op)
            elif op == op_codes.MULT:
                self.num_binary_op(op)
            elif op == op_codes.DIV:
                self.num_binary_op(op)
            elif op == op_codes.MOD:
                self.num_binary_op(op)
            elif op == op_codes.CONST:
                self.push_const()          
            elif op == op_codes.STATIC_STR:
                self.push_str()
            elif op == op_codes.AND:
                self.bool_binary_op(op)
            elif op == op_codes.OR:
                self.bool_binary_op(op)
            elif op == op_codes.NEGATE:
                self.boolean_unary_op(op)
            elif op == op_codes.SET_STATIC_GLOBAL:
                self.set_static_global()                
            elif op == op_codes.GET_STATIC_GLOBAL:
                self.get_static_global()
            elif op == op_codes.SET_LOCAL:
                self.set_local()
            elif op == op_codes.GET_LOCAL:
                self.get_local()          
            elif op == op_codes.POP:
                self.pop()
            elif op == op_codes.JUMP:
                self.ip_addr += Values.value_to_python_repr(self.ops[self.ip_addr:self.ip_addr+8])
            elif op == op_codes.JUMP_BACK:
                self.ip_addr -= Values.value_to_python_repr(self.ops[self.ip_addr:self.ip_addr+8])
            elif op == op_codes.LESS_THAN:
                self.comparison_op(op)
            elif op == op_codes.GREATER_THAN:
                self.comparison_op(op)
            elif op == op_codes.LESS_THAN_EQ:
                self.comparison_op(op)
            elif op == op_codes.GREATER_THAN_EQ:
                self.comparison_op(op)
            elif op == op_codes.EQUAL:
                self.comparison_op(op)
            elif op == op_codes.EXPONENT:
                self.num_binary_op(op)
            elif op == op_codes.FACTORIAL:
                self.num_unary_op(op)
            elif op == op_codes.NEGATIVE:
                self.num_unary_op(op)
            elif op == op_codes.FALSE_JUMP:
                val = self.pop()
                if val[0] != Values.ValueType.BOOL.value:
                    raise Exception("Expected a Boolean at Top of Stack!")
                expr = bool(int.from_bytes(val[4:], byteorder='little'))
                if not expr:
                    self.ip_addr += Values.value_to_python_repr(self.ops[self.ip_addr:self.ip_addr+8])
                else:
                    self.ip_addr += 8       
            elif op == op_codes.OUT:
                val = self.stack[self.stack_ptr-8 : self.stack_ptr]
                Values.print_value(val, self.static_objs, self.heap_manager)
            elif op == op_codes.NEW_TABLE:
                self.new_table()
            elif op == op_codes.NEW_ARRAY:
                self.new_array()
            elif op == op_codes.PUSH_BACK_ARRAY:
                self.push_back_arr()
            elif op == op_codes.POP_BACK:
                self.pop_back()
            elif op == op_codes.ACCESS_STRUCT:
                self.access_struct()
            elif op == op_codes.INSERT_TABLE:
                self.insert_table()   
            elif op == op_codes.MODIFY_STRUCT:
                self.modify_structure()
            elif op == op_codes.NULL:
                self.push_null()
            elif op == op_codes.STRUCT_SIZE:
                self.struct_size()
            elif op == op_codes.NEW_PRIORITY_QUEUE:
                self.new_priority_queue()
            elif op == op_codes.POP_KEY_STRUCT:
                self.pop_key_struct()
            elif op == op_codes.STOP:
                return True
            elif op == op_codes.CALL:
                self.call()
            elif op == op_codes.NEW_CLOSURE:
                self.new_closure()
            elif op == op_codes.RETURN:
                self.return_call()
            elif op == op_codes.CLOSE_UP_VALUE:
                self.up_values = self.close_up_value()
            elif op == op_codes.GET_UP_VALUE:
                self.get_up_value()
            elif op == op_codes.SET_UP_VALUE:
                self.set_up_value()
            else:
                print(int.from_bytes(op, byteorder="little"))
                raise Exception("Invalid Opcode!")
    
    def execute(self):   
        while self.ip_addr < len(self.ops):
            op = self.next_instruction()
            res = self.execute_instruction(op)
            if res:
                break
        print("Ending Stack:", self.stack[0:self.stack_ptr])