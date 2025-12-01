from enum import Enum

import struct 

class ValueType(Enum):
    NULL = 0
    I32 = 1
    BOOL = 2
    F32 = 3
    ADDR = 4
    MAX_VAL = 5
    OP_CODE = 6
    HEAP_OBJ = 7
    STATIC_OBJ = 8

class StaticObjectType(Enum):
    STATIC_STRING = 0
    STATIC_FUNC = 1

def generate_max_val():
    value = bytearray(8)
    value[0] = ValueType.MAX_VAL.value
    return value

def python_repr_to_value(data):
    value = bytearray(8)
    if data == None:
        return value
    elif type(data) == int:
        if data > 2147483647 or data < -2147483648:
            raise Exception("Int is Too Big!")
        value[0] = ValueType.I32.value
        value[4:] = data.to_bytes(4, byteorder='little', signed=True)
        return value
    elif type(data) == float:
        if not(-3.4028235e+38 <= data <= 3.4028235e+38):
            raise Exception("Float is Too Big!")
        value[0] = ValueType.F32.value
        value[4:] = struct.pack('<f', data)
        return value
    elif type(data) == bool:
        value[0] = ValueType.BOOL.value
        value[4:] = int(data).to_bytes(4, byteorder='little')
        return value
    elif type(data) == None:
        value[0] = ValueType.BOOL.value
        value[4:] = int(data.value).to_bytes(4, byteorder='little')
        return value
    else:
        raise Exception("Trying to Convert Incorrect Data Type to Value!")
    
def static_object_to_string(val):
    if val[0] == StaticObjectType.STATIC_STRING.value:
        return val[8:].decode("utf-8")
    elif val[0] == StaticObjectType.STATIC_FUNC.value:
        return "Func"
    else:
        raise Exception("Attempting to Print Invalid Static Object")

def value_to_string(val, static_objs, heap_manager):
    if val[0] == ValueType.NULL.value:
        return "null"
    elif val[0] == ValueType.I32.value:
        return str(int.from_bytes(val[4:], byteorder='little', signed=True))
    elif val[0] == ValueType.F32.value:
            return str(struct.unpack('<f', val[4:])[0])
    elif val[0] == ValueType.BOOL.value:
        return str(bool(int.from_bytes(val[4:], byteorder='little')))
    elif val[0] == ValueType.ADDR.value:
        return f"Addr[{str(int.from_bytes(val[4:], byteorder='little'))}]"
    elif val[0] == ValueType.OP_CODE.value:
        return f"OpCode[{str(int.from_bytes(val[4:], byteorder='little'))}]"
    elif val[0] == ValueType.STATIC_OBJ.value:
        obj = static_objs[int.from_bytes(val[4:], byteorder='little')]
        return static_object_to_string(obj)
    elif val[0] == ValueType.HEAP_OBJ.value:
        return heap_manager.heap_object_to_string(val)
    else:
        raise Exception("Trying to Stringify Invalid Value!")
        
def unused_compare_static_values(v1, v2, static_values):
    if v1[0] != Values.ValueType.STATIC_OBJ or v2[0] != Values.ValueType.STATIC_OBJ:
        raise Exception("Trying to Compare Invalid Static Objects!")
    i1 = int.from_bytes(v1[4:], byteorder="little")
    i2 = int.from_bytes(v2[4:], byteorder="little")
    
    t1 = static_objs[i1][0]
    t2 = static_objs[i1][0]
    
    if t1 == StaticObjectType.STATIC_STRING and t2 == StaitcObjectType.STATIC_STRING:
        return static_objs[i1][8:] == static_objs[i2][8:]
    else:
        raise Exception("Trying to Compare Invalid Static Objects!")

def is_orderable(v, heap_manager):
    if v[0] == ValueType.I32.value:
        return True
    elif v[0] == ValueType.F32.value:
        return True
    elif v[0] == ValueType.MAX_VAL.value:
        return True
    elif v[0] == ValueType.HEAP_OBJ.value:
        return heap_manager.is_orderable(v)
    elif v[0] == ValueType.STATIC_OBJ.value:
        t = heap_manager.get_static_object_type(v)
        if t == StaticObjectType.STATIC_STRING.value:
            return True
    return False

def greater_than(v1, v2, heap_manager):
    if is_orderable(v1, heap_manager) and is_orderable(v2, heap_manager):
        if v1[0] < ValueType.HEAP_OBJ.value and v2[0] < ValueType.HEAP_OBJ.value:
            if v2[0] == ValueType.MAX_VAL.value:
                return False
            if v1[0] == ValueType.MAX_VAL.value:
                return True
            p_v1 = value_to_python_repr(v1)
            p_v2 = value_to_python_repr(v2)
            return p_v1 > p_v2
        elif heap_manager.is_string(v1) and heap_manager.is_string(v2):
            return heap_manager.greater_than_string(v1, v2)
    return False

def less_than(v1, v2, heap_manager):
    if is_orderable(v1, heap_manager) and is_orderable(v2, heap_manager):
        if v1[0] < ValueType.HEAP_OBJ.value and v2[0] < ValueType.HEAP_OBJ.value:
            if v1[0] == ValueType.MAX_VAL.value:
                return False
            if v2[0] == ValueType.MAX_VAL.value:
                return True
            p_v1 = value_to_python_repr(v1)
            p_v2 = value_to_python_repr(v2)
            return p_v1 < p_v2
        elif heap_manager.is_string(v1) and heap_manager.is_string(v2):
            return heap_manager.less_than_string(v1, v2)
    return False
    
def compare_values(v1, v2, heap_manager):
    if v1 == v2:
        return True
    elif v1[0] < ValueType.HEAP_OBJ.value and v2[0] < ValueType.HEAP_OBJ.value:
        return v1[4:] == v2[4:]
    elif heap_manager.is_string(v1) and heap_manager.is_string(v2):
        return heap_manager.compare_strings(v1, v2)
    elif v1[0] != v2[0]:
        return False
    elif v1[0] == ValueType.HEAP_OBJ.value and v2[0] == ValueType.HEAP_OBJ.value:
        return heap_manager.compare_heap_objs(v1, v2)
    elif v1[0] == ValueType.STATIC_OBJ.value and v2[0] == ValueType.STATIC_OBJ.value:        pass
    else:
        raise Exception("Attempting to Compare Invalid Values!")
    
def print_value(val, static_objs, heap_manager):
    print(value_to_string(val, static_objs, heap_manager))

def value_to_python_repr(v):
    if v[0] == ValueType.I32.value:
        return int.from_bytes(v[4:], byteorder='little', signed=True)
    elif v[0] == ValueType.F32.value:
        return struct.unpack('<f', v[4:])[0]
    elif v[0] == ValueType.BOOL.value:
        return bool(int.from_bytes(v[4:], byteorder='little'))
    elif v[0] == ValueType.NULL.value:
        return None
    else:
        raise Exception("Attempting to Convert Invalid Data")