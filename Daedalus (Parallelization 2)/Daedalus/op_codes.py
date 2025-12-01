from enum import Enum
import Values

class OpCode(Enum):
    CONST = 0
    SUM = 1
    SUB = 2
    MULT = 3
    DIV = 4
    MOD = 5
    TRUE_JUMP = 6
    FALSE_JUMP = 7
    JUMP = 8
    JUMP_BACK = 9
    POP = 10
    OUT = 11
    STR_LIT = 12
    NEGATE = 13
    NEGATIVE = 14
    LESS_THAN = 15
    GREATER_THAN = 16
    LESS_THAN_EQ = 17
    GREATER_THAN_EQ = 18
    EQUAL = 19    
    FACTORIAL = 20
    SET_LOCAL = 21
    GET_LOCAL = 22
    SET_STATIC_GLOBAL = 23
    GET_STATIC_GLOBAL = 24
    SET_DYNAMIC_GLOBAL = 25
    GET_DYNAMIC_GLOBAL = 26
    STATIC_STR = 27
    NEW_TABLE = 28
    NEW_ARRAY = 29
    ACCESS_STRUCT = 30
    INSERT_TABLE = 31
    AND = 32
    OR = 33
    EXPONENT = 34
    NULL = 35
    MODIFY_STRUCT = 36
    PUSH_BACK_ARRAY = 37
    POP_BACK = 38
    STRUCT_SIZE = 39
    NEW_PRIORITY_QUEUE = 40
    POP_KEY_STRUCT = 41
    STOP = 42
    NEW_CLOSURE = 43
    RETURN = 44
    CALL = 45
    GET_UP_VALUE = 46
    SET_UP_VALUE = 47
    CLOSE_UP_VALUE = 48
    STATIC_FUNC = 49

SUM = (OpCode.SUM.value).to_bytes(1, byteorder="little")
SUB = (OpCode.SUB.value).to_bytes(1, byteorder="little")
MULT = (OpCode.MULT.value).to_bytes(1, byteorder="little")
DIV = (OpCode.DIV.value).to_bytes(1, byteorder="little")
MOD = (OpCode.MOD.value).to_bytes(1, byteorder="little")
CONST = (OpCode.CONST.value).to_bytes(1, byteorder="little")
STATIC_STR = (OpCode.STATIC_STR.value).to_bytes(1, byteorder="little")
AND = (OpCode.AND.value).to_bytes(1, byteorder="little")
OR = (OpCode.OR.value).to_bytes(1, byteorder="little")
NEGATE = (OpCode.NEGATE.value).to_bytes(1, byteorder="little")
SET_STATIC_GLOBAL = (OpCode.SET_STATIC_GLOBAL.value).to_bytes(1, byteorder="little")
GET_STATIC_GLOBAL = (OpCode.GET_STATIC_GLOBAL.value).to_bytes(1, byteorder="little")
SET_LOCAL = (OpCode.SET_LOCAL.value).to_bytes(1, byteorder="little")
GET_LOCAL = (OpCode.GET_LOCAL.value).to_bytes(1, byteorder="little")
POP = (OpCode.POP.value).to_bytes(1, byteorder="little")
JUMP = (OpCode.JUMP.value).to_bytes(1, byteorder="little")
JUMP_BACK = (OpCode.JUMP_BACK.value).to_bytes(1, byteorder="little")
LESS_THAN = (OpCode.LESS_THAN.value).to_bytes(1, byteorder="little")
GREATER_THAN = (OpCode.GREATER_THAN.value).to_bytes(1, byteorder="little")
LESS_THAN_EQ = (OpCode.LESS_THAN_EQ.value).to_bytes(1, byteorder="little")
GREATER_THAN_EQ = (OpCode.GREATER_THAN_EQ.value).to_bytes(1, byteorder="little")
EQUAL = (OpCode.EQUAL.value).to_bytes(1, byteorder="little")
EXPONENT = (OpCode.EXPONENT.value).to_bytes(1, byteorder="little")
FACTORIAL = (OpCode.FACTORIAL.value).to_bytes(1, byteorder="little")
NEGATIVE = (OpCode.NEGATIVE.value).to_bytes(1, byteorder="little")
FALSE_JUMP = (OpCode.FALSE_JUMP.value).to_bytes(1, byteorder="little")
OUT = (OpCode.OUT.value).to_bytes(1, byteorder="little")
NEW_TABLE = (OpCode.NEW_TABLE.value).to_bytes(1, byteorder="little")
NEW_ARRAY = (OpCode.NEW_ARRAY.value).to_bytes(1, byteorder="little")
PUSH_BACK_ARRAY = (OpCode.PUSH_BACK_ARRAY.value).to_bytes(1, byteorder="little")
POP_BACK = (OpCode.POP_BACK.value).to_bytes(1, byteorder="little")
ACCESS_STRUCT = (OpCode.ACCESS_STRUCT.value).to_bytes(1, byteorder="little")
INSERT_TABLE = (OpCode.INSERT_TABLE.value).to_bytes(1, byteorder="little")
MODIFY_STRUCT = (OpCode.MODIFY_STRUCT.value).to_bytes(1, byteorder="little")
NULL = (OpCode.NULL.value).to_bytes(1, byteorder="little")
STRUCT_SIZE = (OpCode.STRUCT_SIZE.value).to_bytes(1, byteorder="little")
NEW_PRIORITY_QUEUE = (OpCode.NEW_PRIORITY_QUEUE.value).to_bytes(1, byteorder="little")
POP_KEY_STRUCT = (OpCode.POP_KEY_STRUCT.value).to_bytes(1, byteorder="little")
STOP = (OpCode.STOP.value).to_bytes(1, byteorder="little")
RETURN = (OpCode.RETURN.value).to_bytes(1, byteorder="little")
CALL = (OpCode.CALL.value).to_bytes(1, byteorder="little")
STATIC_FUNC = (OpCode.STATIC_FUNC.value).to_bytes(1, byteorder="little")
NEW_CLOSURE = (OpCode.NEW_CLOSURE.value).to_bytes(1, byteorder="little")
CLOSE_UP_VALUE = (OpCode.CLOSE_UP_VALUE.value).to_bytes(1, byteorder="little")
GET_UP_VALUE = (OpCode.GET_UP_VALUE.value).to_bytes(1, byteorder="little")
SET_UP_VALUE = (OpCode.SET_UP_VALUE.value).to_bytes(1, byteorder="little")

def stringify_op(op_codes, index, consts):
    if op_codes[index:index+1] == SUM:
        return "+", index+1
    elif op_codes[index:index+1] == SUB:
        return "-", index+1
    elif op_codes[index:index+1] == MULT:
        return "*", index+1
    elif op_codes[index:index+1] == DIV:
        return "/", index+1
    elif op_codes[index:index+1] == MOD:
        return "%", index+1
    elif op_codes[index:index+1] == CONST:
        index += 1
        return f"Const[{consts[Values.value_to_python_repr(op_codes[index:index+8])]}]", index+8
    elif op_codes[index:index+1] == STATIC_STR:
        index += 1
        return f"Static String[{Values.value_to_python_repr(op_codes[index:index+8])}]", index+8
    elif op_codes[index:index+1] == AND:
        raise Exception("Decompiling Op Unimplemented!")
    elif op_codes[index:index+1] == OR:
        raise Exception("Decompiling Op Unimplemented!")
    elif op_codes[index:index+1] == NEGATE:
        raise Exception("Decompiling Op Unimplemented!")
    elif op_codes[index:index+1] == SET_STATIC_GLOBAL:
        index += 1
        return f"Set Global[{Values.value_to_python_repr(op_codes[index:index+8])}]", index+8
    elif op_codes[index:index+1] == GET_STATIC_GLOBAL:
        index += 1
        return f"Get Global[{Values.value_to_python_repr(op_codes[index:index+8])}]", index+8
    elif op_codes[index:index+1] == SET_LOCAL:
        index += 1
        return f"Set Local[{Values.value_to_python_repr(op_codes[index:index+8])}]", index+8
    elif op_codes[index:index+1] == GET_LOCAL:
        index += 1
        return f"Get Local[{Values.value_to_python_repr(op_codes[index:index+8])}]", index+8
    elif op_codes[index:index+1] == POP:
        return "pop", index+1
    elif op_codes[index:index+1] == JUMP:
        raise Exception("Decompiling Op Unimplemented!")
    elif op_codes[index:index+1] == JUMP_BACK:
        raise Exception("Decompiling Op Unimplemented!")
    elif op_codes[index:index+1] == LESS_THAN:
        raise Exception("Decompiling Op Unimplemented!")
    elif op_codes[index:index+1] == GREATER_THAN:
        raise Exception("Decompiling Op Unimplemented!")
    elif op_codes[index:index+1] == LESS_THAN_EQ:
        raise Exception("Decompiling Op Unimplemented!")
    elif op_codes[index:index+1] == GREATER_THAN_EQ:
        raise Exception("Decompiling Op Unimplemented!")
    elif op_codes[index:index+1] == EQUAL:
        raise Exception("Decompiling Op Unimplemented!")
    elif op_codes[index:index+1] == EXPONENT:
        raise Exception("Decompiling Op Unimplemented!")
    elif op_codes[index:index+1] == FACTORIAL:
        raise Exception("Decompiling Op Unimplemented!")
    elif op_codes[index:index+1] == NEGATIVE:
        raise Exception("Decompiling Op Unimplemented!")
    elif op_codes[index:index+1] == FALSE_JUMP:
        raise Exception("Decompiling Op Unimplemented!")
    elif op_codes[index:index+1] == OUT:
        return "out", index+1   
    elif op_codes[index:index+1] == NEW_TABLE:
        raise Exception("Decompiling Op Unimplemented!")
    elif op_codes[index:index+1] == NEW_ARRAY:
        raise Exception("Decompiling Op Unimplemented!")
    elif op_codes[index:index+1] == PUSH_BACK_ARRAY:
        raise Exception("Decompiling Op Unimplemented!")
    elif op_codes[index:index+1] == POP_BACK:
        raise Exception("Decompiling Op Unimplemented!")
    elif op_codes[index:index+1] == ACCESS_STRUCT:
        raise Exception("Decompiling Op Unimplemented!")
    elif op_codes[index:index+1] == INSERT_TABLE:
        raise Exception("Decompiling Op Unimplemented!")
    elif op_codes[index:index+1] == MODIFY_STRUCT:
        raise Exception("Decompiling Op Unimplemented!")
    elif op_codes[index:index+1] == NULL:
        return "null", index+1    
    elif op_codes[index:index+1] == STRUCT_SIZE:
        raise Exception("Decompiling Op Unimplemented!")
    elif op_codes[index:index+1] == NEW_PRIORITY_QUEUE:
        raise Exception("Decompiling Op Unimplemented!")
    elif op_codes[index:index+1] == POP_KEY_STRUCT:
        raise Exception("Decompiling Op Unimplemented!")
    elif op_codes[index:index+1] == STOP:
        return "stop", index+1  
    elif op_codes[index:index+1] == RETURN:
        return "return", index+1  
    elif op_codes[index:index+1] == NEW_CLOSURE:
        index += 1
        up_value_count = Values.value_to_python_repr(op_codes[index:index+8])
        index += 8
        gc = Values.value_to_python_repr(op_codes[index:index+8])
        index += 8
        
        up_val_str = "["
        i = 0
        while i < up_value_count:
            index_or_offset = Values.value_to_python_repr(op_codes[index:index+8])
            is_local = Values.value_to_python_repr(op_codes[index+8:index+16])
            up_val_str += f"[{index_or_offset}, {is_local}]"
            index += 16
            i += 1
        up_val_str += "]"
        return f"New Closure[Up Values:{up_val_str}]", index
        
    elif op_codes[index:index+1] == CALL:
        index += 1
        return f"Call[{Values.value_to_python_repr(op_codes[index:index+8])}]", index+8  
    elif op_codes[index:index+1] == CLOSE_UP_VALUE:
        return "Close Up Value", index+1
    elif op_codes[index:index+1] == GET_UP_VALUE:
        index += 1
        return f"Get Up Value[{Values.value_to_python_repr(op_codes[index:index+8])}]", index+8  
    else:
        raise Exception("Invalid Op Code!")
        
        
def decompile(op_codes, consts):
    decompiled_ops = []
    index = 0
    while index < len(op_codes):
        str_op, index = stringify_op(op_codes, index, consts)
        decompiled_ops.append(str_op)
    print(decompiled_ops)