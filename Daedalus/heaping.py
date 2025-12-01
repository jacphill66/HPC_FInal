
from enum import Enum
import Values, op_codes

class HeapType(Enum):
    IMMUTABLE_STRING = 0
    MUTABLE_STRING = 1
    TABLE = 2
    ARRAY = 3
    PRIORITY_QUEUE = 4
    DEQUE = 5
    CLOSURE = 6
    UP_VALUE = 7
   
NULL = 0b0000
NULL_VALUE = bytearray(8)
NULL_VALUE[0] = 0b0000
NULL_VALUE[1] = 0b0000
NULL_VALUE[2] = 0b0000
NULL_VALUE[3] = 0b0000
NULL_VALUE[4] = 0b0000
NULL_VALUE[5] = 0b0000
NULL_VALUE[6] = 0b0000
NULL_VALUE[7] = 0b0000

TRUE = Values.python_repr_to_value(True)

IMMUTABLE_STRING = HeapType.IMMUTABLE_STRING.value
TABLE = HeapType.TABLE.value
ARRAY = HeapType.ARRAY.value
PRIORITY_QUEUE = HeapType.PRIORITY_QUEUE.value

class MinimalHeap:
    def __init__(self, cap):
        self.cap = cap
        self.arr = bytearray(cap)
    
    def read_bytes(self, addr, size):
        bytes = bytearray(size)
        i = 0
        while i < size:
            bytes[i] = self.arr[addr + i]
            i += 1
        return bytes

    def write_bytes(self, addr, size, bytes):
        i = 0
        while i < size:
            self.arr[addr + i] = bytes[i]
            i += 1
    
class DynamicHeap:
    def __init__(self, cap):
        self.cap = cap # cappacity
        self.arr = bytearray(cap) # stores the data
        self.remaining = cap # remaining space
        
        self.head_to_end = cap # remaining space from head to the end
        self.head = 0 # head position; used for efficent writing
        
        self.free_map = {0:cap} # free slots; addr:size
        self.alloc_map = {} # allocated slots; addr:size

        self.heap_ids = {} # id -> addr
        self.heap_addrs = {} # addr -> id
        
    def gc_mark_table():
        pass
    
    def gc_mark_array():
        pass
    
    def gc_mark_queue():
        pass
    
    def gc_mark_closure():
        pass
    
    def gc_mark_dynamic_up_value():
        pass
    
    def gc_mark_object(self, heap_value):
        addr, type, flags, size = self.read_heap_object_header(heap_value)
        if type == HeapType.TABLE.value:
            addr, _, total_entries, cappacity, is_set, resizable = self.read_table_header(heap_value)
            return self.gc_mark_table(addr, cappacity, is_set)
        elif type == HeapType.ARRAY.value:
            addr, size, num_elements, resizable, immutable, gc = self.read_arr_header(heap_value)
            return self.gc_mark_array(addr, num_elements)
        elif type == HeapType.PRIORITY_QUEUE.value:
            addr, table_val, size, num_elements, resizable, using_map, gc = self.free_priority(heap_value)
            return self.gc_free_priority_queue(addr, num_elements)
        elif type == HeapType.CLOSURE.value:
            addr, size, id_val, func_val, up_value_count, gc = read_closure_header(heap_value)
            return self.gc_mark_closure()
        elif type == HeapType.UP_VALUE.value:
            addr, table_val, size, num_elements, resizable, using_map, gc = self.read_dynamic_up_value(heap_value)
            return self.gc_mark_dynamic_up_value()
        else:
            print(type)
            raise Exception("Attempting to Convert an Invalid Heap Object to a String!")
    
    def sweep(self, heap_id):
        addr = self.heap_ids[heap_id]
        # if the flag is set
        # free it
        
    def collect_garbage(self):
        for id in self.heap_ids:
            self.sweep(heap_id)
    
    def get_addr(self, heap_id):
        if not (heap_id in self.heap_ids):
            raise Exception("Invalid Heap ID")
        return self.heap_ids[heap_id]
    
    def get_id(self, heap_addr):
        if not (heap_addr in self.heap_addrs):
            raise Exception("Invalid Heap Address")
        return self.heap_addrs[heap_addr]
    
    def update_id(self, id_1, id_2):
        """
        Not Used
        """
        if not (id_1 in self.heap_ids):
            raise Exception("Invalid Heap ID")
        if not (id_2 in self.heap_ids):
            raise Exception("Invalid Heap ID")
        
        self.addrs[id_1] = addr
        self.ids[addr] = id_2
        
        self.addrs[id_2] = addr
        self.addrs.remove(id_1)

    def select_location(self, size):
        # Finds a suitable (big enough) location in the free list
        for addr in self.free_map:
            if size <= self.free_map[addr]:
                return addr
        return -1

    def allocate_addr(self, id, addr, size):
        """
        Allocates a piece of memory at an address. It's assumed the address is free and has enough space.
        """
        if size <= 0:
            raise Exception("Size Must be at Least 1!")
        
        # Update the remaining space and free list
        old_size = self.free_map[addr]
        del self.free_map[addr]
        self.remaining -= size
        new_size = old_size-size
        
        # If the allocation used all of the free space, don't update it
        if new_size > 0:
            self.free_map.update({addr+size:new_size})
        
        # Update the allocation map
        self.alloc_map[addr] = size
        
        # Add the new heap object to the mappings
        self.heap_ids.update({id:addr})
        self.heap_addrs.update({addr:id})
        return addr
        
    def allocate_head(self, id, size):
        """
        DynamicHeap keeps track of a head for quick allocation and for compaction. This method allocates memory starting at the head address.
        """
        # Standard allocation, using the head as an address
        addr = self.allocate_addr(id, self.head, size)
        
        # Adjust head and the head to end space
        self.head += size
        self.head_to_end -= size
        return addr
    
    def allocate(self, id, size):
        """
        Allocate tries to allocate at the head, then a free slot. If these fail, it compacts the memory and allocates it at the new head.
        """
        
        # Try to allocate it at the head if there's space
        if size <= self.head_to_end:
            return self.allocate_head(id, size)
        else:
            # If there's no space whatsoever, throw an error
            if self.remaining < size:
                raise Exception("Allocation Failed: Heap is Out of Memory!")
            else:
                # Try to find a large enough free space
                addr = self.select_location(size)
                
                #If there isn't one, compact and allocate at the new head
                if addr == -1:
                    self.compact()
                    return self.allocate_head(id, size)
                # If there is, allocate it in the free space
                else:
                    
                    return self.allocate_addr(id, addr, size)
                    
    def free(self, id, size):
        """
        Frees a valid adress and adds the free memory to the free list
        """
        if not (id in self.heap_ids):
            raise Exception("Attempting to Free Invalid Heap ID!")
        addr = self.heap_ids[id]
        if not addr in self.alloc_map:
            raise Exception("Attempting to Free Unallocated Memory!")
        
        # Remove it from the allocated objects, delte its id
        del self.alloc_map[addr]
        del self.heap_ids[id]
        del self.heap_addrs[addr]
        
        # Update the free map with the open space
        self.free_map[addr] = size
        
        # Adjust the remaining size
        self.remaining += size
            
    def compact(self):
        """
        Shifts all of the blocks of allocated memory to the beigning of the heaps array by iterating through the array, shifting all allocated blocks to the start
        """
        addr = 0 # Current addr
        start = 0 # Start of free memory; [0, start) is allocated
        while addr < self.cap:
            if addr in self.free_map:
                # If the addr is free, move past it
                addr += self.free_map[addr]
            else:
                # If the addr isn't free, shift the block back to the start
                size = self.alloc_map[addr]
                del self.alloc_map[addr]
                
                # Get the heap id of the current object
                id = self.heap_addrs[addr] 
                
                # Update its address
                self.heap_ids[id] = start
                
                # Delete the old address
                del self.heap_addrs[addr] 
                
                # Update the new address to point to id
                self.heap_addrs[start] = id 
                
                # Update the allocations map
                self.alloc_map[start] = size 
                
                # Copy (and potentially overwrite) the old memory
                self.overwrite_copy(start, addr, size)
                
                # Adjust the current addr and start of the allocated block
                start += size
                addr += size
        
        # Move the head to the end of the contigous allocated block
        self.head = start
        
        # Adjust the remaining space
        self.head_to_end = self.remaining 
        self.free_map = {start:self.remaining}
   
    def overwrite_copy(self, new_addr, old_addr, size):
        """
        Copies memory from one address to another, potentially overwriting memory at the old address durring the copy.
        """
        i = 0
        while i < size:
            self.arr[new_addr + i] = self.arr[old_addr + i]
            i += 1
   
    def read_bytes(self, addr, size):
        """
        Reads bytes from a valid allocated address into a new byte array.
        """
        s = self.alloc_map.get(addr)
        # changed s != size
        if s == None or s < size:
            raise Exception("Attempting to Read Unallocated Memory")
        chunk = bytearray(size)
        i = 0
        while i < size:
            chunk[i] = self.arr[addr + i]
            i += 1
        return chunk

    def write_bytes(self, addr, size, bytes):
        if size < 0:
            raise Exception("Size Must be Greater Than Zero!")
        s = self.alloc_map.get(addr)
        if s == None or s < size:
            raise Exception("Attempting to Write to Unfree Memory!")
        i = 0
        while i < size:
            self.arr[addr + i] = bytes[i]
            i += 1

    def unsafe_write_bytes(self, addr, size, bytes):
        """
        Writes bytes to an address.
        """
        if size < 0:
            raise Exception("Size Must be Greater Than Zero!")
        s = self.alloc_map.get(addr)
        i = 0
        while i < size:
            self.arr[addr + i] = bytes[i]
            i += 1

    def unsafe_read_bytes(self, addr, size):
        """
        Reads bytes from an address into a new byte array.
        """
        chunk = bytearray(size)
        i = 0
        while i < size:
            chunk[i] = self.arr[addr + i]
            i += 1
        return chunk
    
    def reallocate(self, id, size, new_size):
        added_size = new_size - size
        if not (id in self.heap_ids):
            raise Exception("Attempting to Reallocate Invalid Heap ID!")
        addr = self.heap_ids[id]
        if new_size <= size:
            raise Exception("New Size is Equal or Smaller Than Old Size!")
        if added_size  > self.remaining:
            raise Exception("Heap is Out of Memory!")
        if not (addr in self.alloc_map):
            raise Exception("Address isn't Allocated!")
        size = self.alloc_map[addr]
        next_addr = addr+size
        if next_addr in self.free_map and added_size <= self.free_map[next_addr]:
            free_space = self.free_map[next_addr]
            adjusted_addr = next_addr + added_size
            del self.free_map[next_addr]
            self.free_map[adjusted_addr] = free_space - added_size
            self.alloc_map[addr] = new_size
            self.remaining -= added_size
            if next_addr == self.head:
                self.head = next_addr + added_size
                self.head_to_end -= added_size
            return addr
        else:
            bytes = self.read_bytes(addr, size)
            self.free(id, size)
            new_addr = self.allocate(id, new_size)
            self.write_bytes(new_addr, size, bytes)
            return new_addr
    
    def print_chunk(self, addr, size):
        print(f"Chunk at:{addr} [{self.arr[addr:addr+size]} {size} bytes")
    
class HeapManager:
    def __init__(self, dynamic_size, static_size, static_obj_count, static_objs):
        self.dynamic_heap = DynamicHeap(dynamic_size)
        self.static_heap = MinimalHeap(static_size)
        self.id = 0
        self.static_obj_count = static_obj_count
        self.intern_table_ref = self.new_table(1, True, True, False)
        self.static_objs = static_objs
    
    def set_static_global(self, addr, val):
        self.static_heap.write_bytes(addr, 8, val)
    
    def get_static_global(self, addr):
        return self.static_heap.read_bytes(addr, 8)    

    def new_id(self):
        """ 
        Create a new heap id
        """
        self.id += 1
        return self.id - 1
    
    def generate_flag_byte(self, gc):
        """
        Set flags and markers for garbage collection, and marking
        """
        flags = 0b0000
        GARBAGE_COLLECTED = 0b0000
        if gc:
            GARBAGE_COLLECTED = 0b0001
            
        return flags | GARBAGE_COLLECTED
        
    def check_flags(self, byte):
        """
        Checks which flags are set
        """
        IS_GARBAGE_COLLECTED = 0b00001
        
        # Checks which bits are set
        return IS_GARBAGE_COLLECTED & byte
       
    def read_heap_object_header(self, id_val):
        """
        Reads in a heap objects header:
        Type 1 byte | Flags and Padding 3 bytes | 4 bytes size
        """
        id = int.from_bytes(id_val[4:], byteorder="little")
        addr = self.dynamic_heap.get_addr(id)
        type = self.dynamic_heap.arr[addr]
        flags = self.dynamic_heap.arr[addr+1]

        size = int.from_bytes(self.dynamic_heap.arr[addr+4:addr+8], byteorder="little")
        return addr, type, flags, size

    def read_heap_object(self, heap_value):
        """
        Reads a heap object. Used when you need to read in the whole heap object. For example, printing a string.
        """
        
        if heap_value[0] != Values.ValueType.HEAP_OBJ.value:
            raise Exception("Attempting to Read an Invalid Heap Reference")
        
        

        # get the header
        addr, type, flags, size = self.read_heap_object_header(heap_value)
        return self.dynamic_heap.read_bytes(addr, size)
    
    def table_to_string(self, table_addr, cappacity, is_set):
        table_str = "{"
        # Offset by the header (12 bytes)
        offset = table_addr + 12
                
        # Step size; how far to move to the next cell
        step_size = 8
        
        # Add 8 bytes for key values
        if not is_set:
            step_size += 8
        
        # Index of the current cell, start at relative 0
        index = offset
        i = 0
        
        # Go through the elements linearly
        while i < cappacity:
            # Add each non null value in the old table into the new table
            if is_set:
                # If its a set, just move the key
                if self.dynamic_heap.arr[index] != NULL:
                    el = self.dynamic_heap.arr[index:index+8]
                    table_str += Values.value_to_string(el, self.static_objs, self) + ","
            else:
                # If its a key:value, move both
                if self.dynamic_heap.arr[index] != NULL:
                    key = Values.value_to_string(self.dynamic_heap.arr[index:index+8], self.static_objs, self)
                    element = Values.value_to_string(self.dynamic_heap.arr[index+8:index+8+8], self.static_objs, self)
                    table_str += key + ":" + element + ","
            index += step_size
            i += 1
        return table_str + "}"
    
    def array_to_string(self, addr, num_entries):
        i = 0
        addr = addr + 12
        arr_str = "{"
        while i < num_entries:
            arr_str += Values.value_to_string(self.dynamic_heap.arr[addr:addr+8], self.static_objs, self)
            arr_str += ","
            addr += 8
            i += 1
        arr_str += "}"
        return arr_str
    
    def priority_queue_to_string(self, addr, num_entries):
        i = 0
        addr = addr + 20
        
        queue_str = "<|"
        while i < num_entries:
            queue_str += Values.value_to_string(self.dynamic_heap.arr[addr:addr+8], self.static_objs, self)
            addr += 8
            queue_str += ":"
            queue_str += Values.value_to_string(self.dynamic_heap.arr[addr:addr+8], self.static_objs, self)
            queue_str += ","
            addr += 8
            i += 1
        queue_str += "|>"
        return queue_str
    
    def heap_object_to_string(self, heap_value):
        addr, type, flags, size = self.read_heap_object_header(heap_value)
        if type == HeapType.TABLE.value:
            addr, _, total_entries, cappacity, is_set, resizable = self.read_table_header(heap_value)
            return self.table_to_string(addr, cappacity, is_set)
        elif type == HeapType.ARRAY.value:
            addr, size, num_elements, resizable, immutable, gc = self.read_arr_header(heap_value)
            return self.array_to_string(addr, num_elements)
        elif type == HeapType.PRIORITY_QUEUE.value:
            addr, table_val, size, num_elements, resizable, using_map, gc = self.read_priority_queue_header(heap_value)
            return self.priority_queue_to_string(addr, num_elements)
        elif type == HeapType.CLOSURE.value:
            return self.closure_to_string()
        else:
            print(type)
            raise Exception("Attempting to Convert an Invalid Heap Object to a String!")
    
    def closure_to_string(self):
        return f"Closure[]"
    
    def get_static_object_type(self, val):
        i = int.from_bytes(val[4:], byteorder="little")
        if i >= self.static_obj_count:
            raise Exception("Attempting to Access Invalid Static Object")
        return self.static_objs[i][0]
    
    def read_static_object(self, val):
        i = int.from_bytes(val[4:], byteorder="little")
        if i >= self.static_obj_count:
            raise Exception("Attempting to Access Invalid Static Object")
        return self.static_objs[i]
            
    def read_object_payload(self, val):
        obj = None
        if val[0] == Values.ValueType.HEAP_OBJ.value:
            obj = self.read_heap_object(val)
        else:
            obj = self.read_static_object(val)
        return obj[8:]

    def read_string_payload(self, str_val):
        """
        Returns the characters stored in a string from a string value. Assumes that str_val is a valid string.
        """
        obj = None
        if str_val[0] == Values.ValueType.HEAP_OBJ.value:
            obj = self.read_heap_object(str_val)
        else:
            obj = self.read_static_object(str_val)
        return obj[8:]
    
    def is_orderable(self, v):
        _, t, _, _ = heap_manager.read_heap_object_header(v)
        if t == heaping.HeapType.IMMUTABLE_STRING:
            return True
        elif t == heaping.HeapType.MUTABLE_STRING:
            return True
        return False
        
    def greater_than_strings(self, v1, v2):
        s1 = self.read_string_payload(v1)
        s2 = self.read_string_payload(v2)
        return s1 > s2

    def less_than_strings(self, v1, v2):
        s1 = self.read_string_payload(v1)
        s2 = self.read_string_payload(v2)
        return s1 < s2

    def compare_strings(self, v1, v2):
        """
        Compares two strings represented as values. If they have the same characters (represented by bytes), they are equivalent. Assumes both v1 and v2 are string values.
        """
        s1 = self.read_string_payload(v1)
        s2 = self.read_string_payload(v2)
        return s1 == s2
    
    def compare_tables(self, v1, v2):
        """
        Ensures two tables have the same number of keys, and the same key, value pairs.
        """
        
        addr1, size1, total_entries1, cappacity1, is_set1, resizable1 = self.read_table_header(v1)
        addr2, size2, total_entries2, cappacity2, is_set2, resizable2 = self.read_table_header(v2)
        
        if cappacity1 != cappacity2:
            return False
        
        # Offset by the header (12 bytes)
        offset = addr1 + 12
        
        # Step size; how far to move to the next cell
        step_size = 8
        
        # Add 8 bytes for key values
        if not is_set1:
            step_size += 8
        
        # Index of the current cell, start at relative 0
        index = offset
        i = 0
        
        # Go through the elements linearly
        while i < cappacity1:
            # Add each non null value in the old table into the new table
            if is_set1:
                # If its a set, just move the key
                if self.dynamic_heap.arr[index] != NULL:
                    i = self.find_table_cell(addr2, cappacity2, is_set2, self.dynamic_heap.arr[index:index+8])
                    if i == None:
                        return False
            else:
                # If its a key:value, move both
                if self.dynamic_heap.arr[index] != NULL:
                    i = self.find_table_cell(addr2, cappacity2, is_set2, self.dynamic_heap.arr[index:index+8])
                    if i == None:
                        return False
                    el1 = self.dynamic_heap.arr[index+8:index+8+8]
                    el2 = self.dynamic_heap.arr[i+8:i+8+8]
                    if not Values.compare_values(el1, el2, self):
                        return False
                    
            index += step_size
            i += 1
        return True
    
    def compare_priority_queues(self, queue1, queue2):
        queue_addr1, table_val1, size1, num_elements1, resizable1, using_map1, gc1 = self.read_priority_queue_header(queue1)
        queue_addr2, table_val2, size2, num_elements2, resizable2, using_map2, gc2 = self.read_priority_queue_header(queue2)
        
        if num_elements1 != num_elements2:
            return False
            
        i = 0
        addr1 = queue_addr1 + 20
        addr2 = queue_addr2 + 20
        
        while i < num_elements1:
            if not Values.compare_values(self.dynamic_heap.unsafe_read_bytes(addr1, 8), self.dynamic_heap.unsafe_read_bytes(addr2, 8), self):
                return False
            addr1 += 8
            addr2 += 8
            if not Values.compare_values(self.dynamic_heap.unsafe_read_bytes(addr1, 8), self.dynamic_heap.unsafe_read_bytes(addr2, 8), self):
                return False
            addr1 += 8
            addr2 += 8
            i += 1
        return True
        

    
    def compare_arrays(self, arr1, arr2):
        addr1, _, num_elements1, resizable1, immutable1, gc1 = self.read_arr_header(arr1)
        addr2, _, num_elements2, resizable2, immutable2, gc2 = self.read_arr_header(arr2)
        if num_elements1 != num_elements2:
            return False
        
        i = 0
        addr1 += 12
        addr2 += 12
        while i < num_elements1:
            if not Values.compare_values(self.dynamic_heap.unsafe_read_bytes(addr1, 8), self.dynamic_heap.unsafe_read_bytes(addr2, 8), self):
                return False
            addr1 += 8
            addr2 += 8
            i += 1
        return True
            
    def compare_heap_objs(self, v1, v2):
        """
        Determines if two heap objects are (loosley) equivalent. Assumes that v1 and v2 are heap object values.
        """
        
        addr1, type1, flags1, size1 = self.read_heap_object_header(v1)
        addr2, type2, flags2, size2 = self.read_heap_object_header(v2)
        
        if self.is_string(v1) and self.is_string(v2):
            return Values.compare_strings(v1, v2, self)
        elif type1 != type2:
            return False
        elif type1 == HeapType.TABLE.value:
            return self.compare_tables(v1, v2)
        elif type1 == HeapType.ARRAY.value:
            return self.compare_arrays(v1, v2)
        elif type1 == HeapType.PRIORITY_QUEUE.value:
            return self.compare_priority_queues(v1, v2)
        else:
            raise Exception("Attempting to Compare Invalid Heap Types!")
    
    def is_string(self, v):
        if v[0] == Values.ValueType.STATIC_OBJ.value:
            index = int.from_bytes(v[4:], byteorder="little")
            return self.static_objs[index][0] == Values.StaticObjectType.STATIC_STRING.value
            
        if v[0] == Values.ValueType.HEAP_OBJ.value:
            _, type, _, _ = self.read_heap_object_header(v)
            
            if type == HeapType.IMMUTABLE_STRING.value:
                return True
                
            if type == HeapType.MUTABLE_STRING.value:
                return True
                
        return False

    def deprecated_compare_values(self, val1, val2):
        if val1[0] < Values.ValueType.HEAP_OBJ.value and val2[0] < Values.ValueType.HEAP_OBJ.value:
            return val1 == val2
        else:
            obj_1 = self.read_object_payload(val1)
            obj_2 = self.read_object_payload(val2)
            return obj_1 == obj_2

    def val_as_heap_ref(self, id):
        val_ref = bytearray(8)
        val_ref[0] = Values.ValueType.HEAP_OBJ.value
        val_ref[4:] = id.to_bytes(4, byteorder="little")
        return val_ref

    def allocate_str(self, str, gc):
        """
        Allocates an immutable string (max length 2^32) on the heap.
        Subtract 8 bytes for the header size
        """
        chars = len(str)
        if chars > 4294967288:
            raise Exception("String is Too Long!")
        
        # generate a heap id
        id = self.new_id() 
        
        # 1 byte of type, 3 byte of flags and spacing, 4 bytes of size 
        size = 8 + chars
        addr = self.dynamic_heap.allocate(id, size)
        
        # Write the header (1 byte type | 1 byte flags | 4 bytes size)
        self.dynamic_heap.arr[addr] = HeapType.IMMUTABLE_STRING.value
        self.dynamic_heap.arr[addr+1] = self.generate_flag_byte(gc)
        self.dynamic_heap.arr[addr+4:addr+8] = size.to_bytes(4, byteorder="little")
        
        # The write is unsafe because its writing in the middle of an allocated block
        # Write the chars to the heap
        self.dynamic_heap.unsafe_write_bytes(addr+8, chars, bytes(str, 'utf-8'))
        
        # Return the heap object used by the VM
        return self.val_as_heap_ref(id)       

    def calculate_table_size(self, cappacity, is_set):
        # Header size
        size = 12
        
        # Space for cappacity 8 byte keys
        size += 8 * cappacity
        
        # If it isn't a set, need space for values
        if not is_set:
            size += (cappacity * 8)
        
        return size
        
    def generate_table_flags(self, resizable, is_set):
        """
        Generates table specific flags
        """
        flag = 0b0000
        if resizable:
            flag |= 0b0001
        if is_set:
            flag |= 0b0010

        return flag
    
    def generate_table_header(self, id, cappacity, resizable, is_set, gc):
        header = None
        size = self.calculate_table_size(cappacity, is_set)
        header = bytearray(12)
        header[0] = HeapType.TABLE.value
        header[1] = self.generate_flag_byte(gc)
        # 2 is empty for now
        header[3] = self.generate_table_flags(resizable, is_set)
        
        # size
        header[4:8] = size.to_bytes(4, byteorder="little") 
        
        # entry count
        header[8:12] = (0).to_bytes(4, byteorder="little") 
        return header, size
    
    def extract_table_flags(self, table_flags):
        resizable = bool(table_flags & 0b0001)
        is_set = bool(table_flags & 0b0010)
        return resizable, is_set
    
    def read_table_header(self, id_val):
        """
        Reads in information specific to tables.
        """
        addr, type, _, size = self.read_heap_object_header(id_val)
        if type != HeapType.TABLE.value:
            raise Exception("Attempting to Read a Non-Table!")
        table_flags = self.dynamic_heap.arr[addr+3]
        
        resizable, is_set = self.extract_table_flags(table_flags)
        total_entries, cappacity = self.extract_table_sizes(addr, size, is_set)
        
        return addr, size, total_entries, cappacity, is_set, resizable
    
    def new_table(self, cappacity, resizable, is_set, gc):
        """
        Initializes a table of cappacity on the heap.
        """
        id = self.new_id()
        header, size = self.generate_table_header(id, cappacity, resizable, is_set, gc)
        addr = self.dynamic_heap.allocate(id, size)
        self.dynamic_heap.write_bytes(addr, 12, header)
        # Every byte must be null for probing to work
        i = addr + 12
        while i < size:
            self.dynamic_heap.arr[i] = NULL
            i += 1  
        return self.val_as_heap_ref(id)
        
    def generate_array_header(self, id, cappacity, resizable, immutable, gc):
        size = 12 + cappacity * 8
        header = bytearray(12)
        header[0] = HeapType.ARRAY.value
        header[1] = self.generate_flag_byte(gc)
        if resizable:
            header[3] |= 0b0001
        if immutable:
            header[3] |= 0b0010
        header[4:8] = size.to_bytes(4, byteorder="little") 
        header[8:12] = (0).to_bytes(4, byteorder="little") 
        return header, size
    
    def read_priority_queue_header(self, priority_queue_val):
        id = int.from_bytes(priority_queue_val[4:], byteorder="little")
        addr = self.dynamic_heap.get_addr(id)
        header = self.dynamic_heap.read_bytes(addr, 20)
        gc = 0b0001 & header[1]
        resizable = 0b0001 & header[3]
        using_map = 0b0010 & header[3]
        size = int.from_bytes(header[4:8], byteorder="little")
        num_elements = int.from_bytes(header[8:12], byteorder="little")
        table_val = header[12:20]
        return addr, table_val, size, num_elements, resizable, using_map, gc
    
    def generate_priority_queue_header(self, id, using_map, resizable, cappacity, gc):
        size = 20 + cappacity * 16
        header = bytearray(20)
        header[0] = HeapType.PRIORITY_QUEUE.value
        header[1] = self.generate_flag_byte(gc)
        if resizable:
            header[3] |= 0b0001
        if using_map:
            header[3] |= 0b0010
        header[4:8] = size.to_bytes(4, byteorder="little") 
        header[8:12] = (0).to_bytes(4, byteorder="little") 
        header[12:] = self.new_table(cappacity, resizable, False, gc)
        return header, size
    
    def new_priority_queue(self, resizable, using_map, cappacity, gc):
        id = self.new_id()
        header, size = self.generate_priority_queue_header(id, using_map, resizable, cappacity, gc)
        addr = self.dynamic_heap.allocate(id, size)
        self.dynamic_heap.write_bytes(addr, 20, header)
        return self.val_as_heap_ref(id)
    
    def priority_queue_swap(self, addr1, key1, addr2, key2, table_val):
        payload1 = self.dynamic_heap.unsafe_read_bytes(addr1, 16)
        self.dynamic_heap.unsafe_write_bytes(addr1, 16, self.dynamic_heap.unsafe_read_bytes(addr2, 16))
        self.dynamic_heap.unsafe_write_bytes(addr2, 16, payload1)
        addr_val_1 = bytearray(8)
        addr_val_1[0:4] = Values.ValueType.ADDR.value.to_bytes(4, byteorder="little")
        addr_val_1[4:] = addr1.to_bytes(4, byteorder="little")
        addr_val_2 = bytearray(8)
        addr_val_2[0:4] = Values.ValueType.ADDR.value.to_bytes(4, byteorder="little")
        addr_val_2[4:] = addr2.to_bytes(4, byteorder="little")
        self.modify_table(table_val, key1, addr_val_1)
        self.modify_table(table_val, key2, addr_val_2)
    
    def extraxt_max_priority_queue_helper(self, queue_addr, table_val, num_elements):
        if num_elements == 0:
            raise Exception("Can't Extract Max from an Empty Queue!")
        
        # Index of the first element
        start_addr = queue_addr+20
        
        # Index of the last element
        end_addr = queue_addr+20 + 16 * (num_elements-1)
        
        # First key (max element)
        max = self.dynamic_heap.unsafe_read_bytes(start_addr, 8)
        
        # Decrement the elements
        self.decrement_struct_entries(queue_addr, num_elements)
        
        # Swap first and last
        self.priority_queue_swap(end_addr, self.dynamic_heap.unsafe_read_bytes(end_addr, 8), start_addr, max, table_val)
        
        # Sift the new first element down to its correct place
        self.sift_down(start_addr, table_val, end_addr, start_addr) 
        
        # Return it
        return max
    
    def priority_queue_get_priority(self, queue_val, key_val):
        queue_addr, table_val, size, num_elements, resizable, using_map, gc = self.read_priority_queue_header(queue_val)
        
        addr_val = self.search_table(table_val, key_val)
        addr = int.from_bytes(addr_val[4:], byteorder="little")
        
        return self.dynamic_heap.unsafe_read_bytes(addr+8, 8)
    
    def extract_max_priority_queue(self, queue_val):
        queue_addr, table_val, size, num_elements, resizable, using_map, gc = self.read_priority_queue_header(queue_val)
        return self.extraxt_max_priority_queue_helper(queue_addr, table_val, num_elements)
    
    def remove_key_priority_queue(self, queue_val, key_val):
        queue_addr, table_val, size, num_elements, resizable, using_map, gc = self.read_priority_queue_header(queue_val)
        if num_elements == 0:
            raise Exception("Priority Queue is Empty!")
        self.max_heap_increase_helper(queue_addr, table_val, key_val, Values.generate_max_val())
        return self.extraxt_max_priority_queue_helper(queue_addr, table_val, num_elements)
    
    def addr_to_heap_index(self, addr, start_addr):
        return (addr - start_addr) / 16
            
    def heap_index_to_addr(self, index, start_addr):
        return int((index * 16) + start_addr)
    
    def get_parent_addr(self, start_addr, index_addr):
        return int(self.heap_index_to_addr((self.addr_to_heap_index(index_addr, start_addr) - 1) // 2, start_addr))
    
    def left_child_priority_queue(self, index_addr, start_addr):
        return int(self.heap_index_to_addr(self.addr_to_heap_index(index_addr, start_addr) * 2 + 1, start_addr))
    
    def right_child_priority_queue(self, index_addr, start_addr):
        return int(self.heap_index_to_addr(self.addr_to_heap_index(index_addr, start_addr) * 2 + 2, start_addr))
    
    def sift_down(self, index_addr, table_val, end_addr, start_addr):
        left_addr = self.left_child_priority_queue(index_addr, start_addr)
        left_key = self.dynamic_heap.unsafe_read_bytes(left_addr, 8)
        left_priority = self.dynamic_heap.unsafe_read_bytes(left_addr+8, 8)

        right_addr = self.right_child_priority_queue(index_addr, start_addr)
        right_key = self.dynamic_heap.unsafe_read_bytes(right_addr, 8)
        right_priority = self.dynamic_heap.unsafe_read_bytes(right_addr+8, 8)

        largest_addr = index_addr
        largest_key = self.dynamic_heap.unsafe_read_bytes(index_addr, 8)
        largest_priority = self.dynamic_heap.unsafe_read_bytes(index_addr+8, 8)
        
        if left_addr < end_addr and Values.greater_than(left_priority, largest_priority, self):
            largest_addr = left_addr
            largest_key = left_key
            largest_priority = left_priority
        if right_addr < end_addr and Values.greater_than(right_priority, largest_priority, self):
            largest_addr = right_addr
            largest_key = right_key
            largest_priority = right_priority
         
        if largest_addr != index_addr:
            index_key = self.dynamic_heap.unsafe_read_bytes(index_addr, 8)
            self.priority_queue_swap(largest_addr, largest_key, index_addr, index_key, table_val)
            self.sift_down(largest_addr, table_val, end_addr, start_addr)
    
    def sift_up(self, index_addr, start_addr, table_val):
        parent_addr = self.get_parent_addr(start_addr, index_addr)
        parent_key = self.dynamic_heap.unsafe_read_bytes(parent_addr, 8)
        parent_priority = self.dynamic_heap.unsafe_read_bytes(parent_addr+8, 8)
        
        index_key = self.dynamic_heap.unsafe_read_bytes(index_addr, 8)
        index_priority = self.dynamic_heap.unsafe_read_bytes(index_addr+8, 8)
                
        while index_addr > start_addr and Values.greater_than(index_priority, parent_priority, self):
            # If the index is in range and the parent is bigger swap them
            self.priority_queue_swap(parent_addr, parent_key, index_addr, index_key, table_val)
            
            # Adjust parent and index, repeat
            index_addr = parent_addr
            index_key = index_key
            index_priority = index_priority
                        
            parent_addr = self.get_parent_addr(start_addr, parent_addr)
            parent_key = self.dynamic_heap.unsafe_read_bytes(parent_addr, 8)
            parent_priority = self.dynamic_heap.unsafe_read_bytes(parent_addr+8, 8)
    
    def max_heap_increase_helper(self, queue_addr, table_val, key_val, priority_val):
        # Extract the Address of the Key:Priority in the Queue
        addr_val = self.search_table(table_val, key_val)
        addr = int.from_bytes(addr_val[4:], byteorder="little")
        
        # Read in the Old Priority
        old_priority_val = self.dynamic_heap.unsafe_read_bytes(addr+8, 8)
                
        if Values.less_than(priority_val, old_priority_val, self):
            raise Exception("New Priority is Less than Old Priority!")
        
        # Update Queue with the New Priority
        self.dynamic_heap.unsafe_write_bytes(addr+8, 8, priority_val) 
                
        # Sift Up
        self.sift_up(addr, queue_addr+20, table_val)
    
    def max_heap_increase(self, priority_queue_val, key_val, priority_val):
        # Read in table meta data
        queue_addr, table_val, size, num_elements, resizable, using_map, gc = self.read_priority_queue_header(priority_queue_val)
        
        # Delegate to the helper
        self.max_heap_increase_helper(queue_addr, table_val, key_val, priority_val)
        
    def insert_priority_queue(self, priority_queue_val, key_val, priority_val):
        queue_addr, table_val, size, num_elements, resizable, using_map, gc = self.read_priority_queue_header(priority_queue_val)
        
        cappacity = (size - 20) / 16
        if num_elements == cappacity:
            if resizable:
                self.resize_priority_queue(priority_queue_val)
            else:
                raise Exception("Priority Queue is Full!")
        
        # Add the Key:Priority to the End
        end_addr = queue_addr + 20 + (num_elements * 16)
        self.dynamic_heap.unsafe_write_bytes(end_addr, 8, key_val)
        self.dynamic_heap.unsafe_write_bytes(end_addr+8, 8, priority_val)

        # Update the Table with the New Address
        new_addr = bytearray(8)
        new_addr[0] = Values.ValueType.ADDR.value
        new_addr[4:] = end_addr.to_bytes(4, byteorder="little")
        self.add_table(table_val, key_val, new_addr)              
        self.increment_struct_entries(queue_addr, num_elements)
                            
        # Increase the Priority
        # It uses its own priority, but its out of place, so it will be shifted up
        self.max_heap_increase_helper(queue_addr, table_val, key_val, priority_val)

        # Return something
        return key_val
    
    def generate_deque_header(self, id, resizable, cappacity):
        size = 12 + cappacity * 8
        header = bytearray(12)
        header[0] = HeapType.DEQUE.value
        header[1] = self.generate_flag_byte(gc)
        if resizable:
            header[3] |= 0b0001
        header[4:8] = size.to_bytes(4, byteorder="little") 
        header[8:12] = (0).to_bytes(4, byteorder="little") 
        return header, size
    
    def read_deque_header(self, deque_val):
        id = int.from_bytes(deque_val[4:], byteorder="little")
        addr = self.dynamic_heap.get_addr(id)
        header = self.dynamic_heap.read_bytes(addr, 12)
        gc = 0b0001 & header[1]
        resizable = 0b0001 & header[3]
        size = int.from_bytes(header[4:8], byteorder="little")
        num_elements = int.from_bytes(header[8:], byteorder="little")
        return addr, size, num_elements, resizable, gc
        
    def load_function(self, addr, body_size, up_value_count, op_codes, op_addr):
        func_op_addr = addr + 28
        self.dynamic_heap.unsafe_write_bytes(func_op_addr, body_size, op_codes[op_addr:op_addr+body_size])
        op_addr += body_size
        i = up_value_count
        while i > 0:
            self.dynamic_heap.unsafe_write_bytes(op_addr, 8, op_codes[op_addr:op_addr+8])
            op_addr += 8
            self.dynamic_heap.unsafe_write_bytes(op_addr, 8, op_codes[op_addr:op_addr+8])
            op_addr += 8
            self.dynamic_heap.unsafe_write_bytes(op_addr, 8, NULL_VALUE)
            i -= 1
        
        return op_addr
            

    def call_closure(self, func_val):
        addr, size, id_val, arity, body_size, up_value_count, gc = self.read_function_header(func_val)
        return self.dynamic_heap.arr, addr+28, arity, func_val, id_val
    
    def new_dynamic_up_value(self, value, gc):
        id = self.new_id()
        header = bytearray(16)
        header[0] = HeapType.UP_VALUE.value
        header[1] = self.generate_flag_byte(gc)
        header[4:8] = (16).to_bytes(4, byteorder="little") 
        header[8:16] = value
        addr = self.dynamic_heap.allocate(id, 16)
        self.dynamic_heap.write_bytes(addr, 16, header)
        return self.val_as_heap_ref(id)
    
    def read_dynamic_up_value(self, id_val):
        id = int.from_bytes(id_val[4:8], byteorder="little")
        addr = self.dynamic_heap.get_addr(id)
        return self.dynamic_heap.unsafe_read_bytes(addr+8, 8)
    
    def write_dynamic_up_value(self, id_val, val):
        id = int.from_bytes(id_val[4:8], byteorder="little")
        addr = self.dynamic_heap.get_addr(id)
        return self.dynamic_heap.unsafe_write_bytes(addr+8, 8, val) 
    
    def index_or_offset(self, up_val_addr):
        return self.dynamic_heap.unsafe_read_bytes(up_val_addr, 8)
    
    def is_closed(self, up_val_addr):
        return Values.value_to_python_repr(self.dynamic_heap.unsafe_read_bytes(up_val_addr+16, 8))
    
    def close_up_value(self, up_val_addr, closed_ref):
        self.dynamic_heap.unsafe_write_bytes(up_val_addr, 8, closed_ref)
        self.dynamic_heap.unsafe_write_bytes(up_val_addr+16, 8, TRUE)
        
    def bind_up_value(self, up_val_addr, ):
        pass
    
    def resolve_up_value(self, closure_val, index):
        pass
    
    def read_closure_header(self, closure_val):
        id = int.from_bytes(closure_val[4:], byteorder="little")
        addr = self.dynamic_heap.get_addr(id)
        header = self.dynamic_heap.read_bytes(addr, 28)
        gc = bool(0b0001 & header[1])
        size = int.from_bytes(header[4:8], byteorder="little")
        id_val = header[8:16]
        func_val = header[16:24]
        up_value_count = int.from_bytes(header[24:28], byteorder="little")
        return addr, size, id_val, func_val, up_value_count, gc    
    
    def generate_closure_header(self, id_val, func_val, up_value_count, gc):
        size = 28 + (up_value_count * 24)
        header = bytearray(28)
        header[0] = HeapType.CLOSURE.value
        header[1] = self.generate_flag_byte(gc)
        header[4:8] = size.to_bytes(4, byteorder="little") 
        header[8:16] = id_val
        header[16:24] = func_val
        header[24:28] = up_value_count.to_bytes(4, byteorder="little")
        return header, size
    
    def new_closure(self, id_val, func_val, up_value_count, gc):
        id = self.new_id()
        header, size = self.generate_closure_header(id_val, func_val, up_value_count, gc)
        addr = self.dynamic_heap.allocate(id, size)
        self.dynamic_heap.write_bytes(addr, 28, header)
        return self.val_as_heap_ref(id)
    
    def load_up_value(self, addr, index_or_offset, is_local, is_closed):
        self.dynamic_heap.unsafe_write_bytes(addr, 8, index_or_offset)
        self.dynamic_heap.unsafe_write_bytes(addr+8, 8, is_local)
        self.dynamic_heap.unsafe_write_bytes(addr+16, 8, is_closed)
    
    def new_up_value(self, func_addr):
        pass
        
    def set_up_value():
        pass
    
    def set_up_value(self, closure_val, val, index, stack):
        addr, size, id_val, func_val, up_value_count, gc = self.read_closure_header(closure_val)

        up_val_addr = addr + 28 + (index * 24)
        
        payload = self.dynamic_heap.unsafe_read_bytes(up_val_addr, 24)
    
        is_local = Values.value_to_python_repr(payload[8:16])
        is_closed = Values.value_to_python_repr(payload[16:24])

        if is_closed:
            # set a dynamic up val
            self.write_dynamic_up_value(payload[0:8], val)
        else:
            # set a live up value
            stack_addr = Values.value_to_python_repr(payload[0:8])
            stack[stack_addr:stack_addr+8] = val
            
    
    def get_up_value(self, closure_val, index, stack):
        addr, size, id_val, func_val, up_value_count, gc = self.read_closure_header(closure_val)

        up_val_addr = addr + 28 + (index * 24)
        
        payload = self.dynamic_heap.unsafe_read_bytes(up_val_addr, 24)
    
        is_local = Values.value_to_python_repr(payload[8:16])
        is_closed = Values.value_to_python_repr(payload[16:24])

        if is_closed:
            # read a dynamic val
            return self.read_dynamic_up_value(payload[0:8])
        else:
            stack_addr = Values.value_to_python_repr(payload[0:8])
            return stack[stack_addr:stack_addr+8]
        
    def new_deque(self, cappacity, gc):
        """
        Creates a new Array on the Heap
        """
        id = self.new_id()
        header, size = self.generate_deque_header(id, cappacity, resizable, gc)
        addr = self.dynamic_heap.allocate(id, size)

    def new_array(self, cappacity, resizable, immutable, gc):
        """
        Creates a new Array on the Heap
        """
        id = self.new_id()
        header, size = self.generate_array_header(id, cappacity, resizable, immutable, gc)
        addr = self.dynamic_heap.allocate(id, size)
        self.dynamic_heap.write_bytes(addr, 12, header)
        return self.val_as_heap_ref(id)
    
    def read_arr_header(self, arr_val):
        id = int.from_bytes(arr_val[4:], byteorder="little")
        addr = self.dynamic_heap.get_addr(id)
        header = self.dynamic_heap.read_bytes(addr, 12)
        gc = 0b0001 & header[1]
        resizable = 0b0001 & header[3]
        immutable = 0b0010 & header[3]
        size = int.from_bytes(header[4:8], byteorder="little")
        num_elements = int.from_bytes(header[8:], byteorder="little")
        return addr, size, num_elements, resizable, immutable, gc
    
    def increment_struct_entries(self, addr, num_entries):
        self.dynamic_heap.unsafe_write_bytes(addr+8, 4, (num_entries+1).to_bytes(4, byteorder="little"))
    
    def decrement_struct_entries(self, addr, num_entries):
        self.dynamic_heap.unsafe_write_bytes(addr+8, 4, (num_entries-1).to_bytes(4, byteorder="little"))
    
    def arr_push_back(self, arr_val, val):
        addr, size, num_elements, resizable, immutable, gc = self.read_arr_header(arr_val)
        cappacity = (size - 12) / 8
        if num_elements == cappacity:
            addr = self.resize_arr(arr_val, size, 2)
        index_addr = addr + 12 + num_elements * 8
        self.dynamic_heap.unsafe_write_bytes(index_addr, 8, val)          
        self.increment_struct_entries(addr, num_elements)   
        
    def arr_pop_back(self, arr_val):
        addr, size, num_elements, resizable, immutable, gc = self.read_arr_header(arr_val)
        if num_elements == 0:
            raise Exception("Attempting to Pop an Empty Array!")
        index_addr = addr + 12 + (num_elements-1) * 8
        self.decrement_struct_entries(addr, num_elements)
        return self.dynamic_heap.unsafe_read_bytes(index_addr, 8)
        
    def arr_modify_index(self, arr_val, index_val, val):
        addr, size, num_elements, resizable, immutable, gc = self.read_arr_header(arr_val)
        index = int.from_bytes(index_val[4:], byteorder="little")
        if index >= num_elements:
            raise Exception("Attempting to Modify Out of Bounds Array Index")
        index_addr = addr + 12 + index * 8
        self.dynamic_heap.unsafe_write_bytes(index_addr, 8, val)          
        
    def arr_get_index(self, arr_val, index_val):
        addr, size, num_elements, resizable, immutable, gc = self.read_arr_header(arr_val)
        index = int.from_bytes(index_val[4:], byteorder="little")
        if index >= num_elements:
            raise Exception("Attempting to Access Out of Bounds Array Index")
        index_addr = addr + 12 + index * 8
        return self.dynamic_heap.unsafe_read_bytes(index_addr, 8)
        
    def resize_arr(self, arr_val, size, growth_factor):
        id = int.from_bytes(arr_val[4:], byteorder="little")
        return self.dynamic_heap.reallocate(id, size, size*growth_factor) 
    
    def extract_table_sizes(self, addr, size, is_set):
        total_entries = int.from_bytes(self.dynamic_heap.arr[addr+8:addr+12], byteorder="little")
        
        payload_size = size - 12
                        
        cappacity = -1                
        if is_set:
            cappacity = payload_size // 8
        else:
            cappacity = payload_size // (8 + 8)
        return total_entries, cappacity
        
    def load_static_string(self, obj_str, static_obj_index):
        """
        Loads a static string into the intern table
        """
        str_val = bytearray(8)
        str_val[0] = Values.ValueType.STATIC_OBJ.value
        str_val[4:8] = static_obj_index.to_bytes(4, byteorder="little")
        addr, _, total_entries, cappacity, is_set, resizable = self.read_table_header(self.intern_table_ref)
        return self.add_table(self.intern_table_ref, str_val, None) 

    def hash_value(self, cappacity, key_value, probe_num):
        """
        Determines the index of a key in a given table.
        """
        if key_value[0] == Values.ValueType.HEAP_OBJ.value:
            obj = self.read_heap_object(key_value)
            if obj[0] == HeapType.IMMUTABLE_STRING.value:
                key = obj[8:].decode("utf-8") 
                hash_value = 0
                for char in key:
                    hash_value = (hash_value * 31 + ord(char)) % cappacity
                return (hash_value + probe_num) % cappacity
        elif key_value[0] == Values.ValueType.STATIC_OBJ.value:
            # static string
            i = int.from_bytes(key_value[4:], byteorder="little")
            key = self.static_objs[i][8:].decode("utf-8") 
            hash_value = 0
            for char in key:
                hash_value = (hash_value * 31 + ord(char)) % cappacity
                return (hash_value + probe_num) % cappacity
        raise Exception("Can Only Hash Strings (for now)!")      
    
    def probe_num(self, cappacity, key_value, index):
        """
        Determines the probe number of a key in a given table.
        """
        return (index - self.hash(cappacity, key_value, 0)) % cappacity
    
    def find_table_cell(self, table_addr, cappacity, is_set, key_value):
        """
        Finds the potentially null cell of the table where key_value belongs. Backbone of: insert, search and modify
        """        
        # Offset by the header (12 bytes)
        offset = table_addr + 12
        
        # Determine the index, relative to the begining of the array
        relative_index = self.hash_value(cappacity, key_value, 0)

        # Step size; how far to move to the next cell
        step_size = 8
        
        # Add 8 bytes for key values
        if not is_set:
            step_size += 8
        
        # Index of the start of the next cell
        index = offset + (relative_index * step_size)
        
        # Starting with a probe number of 0
        i = 0
        while i < cappacity:
            # If null is reached, end of probe chain, return
            if self.dynamic_heap.arr[index] == NULL:
                return index

            # Compare the keys, if they match, return the index
            if Values.compare_values(key_value, self.dynamic_heap.arr[index:index+8], self):
                return index
            
            # Update the relative index (next cell relative to start)
            relative_index = ((relative_index + 1) % cappacity)
            # Calculate the acctual index (index of next cell)
            index = offset + (relative_index * step_size)
            i += 1   
            
        # If the end of the table is reached, there's no room or the key wasn't found
        return None
    
    def calculate_indices(self, key_index, is_set):
        start_index = key_index
        end_index = key_index+8
        if not is_set:
            # If its not a set add 8 bytes for key
            start_index += 8
            end_index += 8
        return start_index, end_index
    
    # Should work for all objects that store entries
    def increment_table_entries(self, table_addr):
        val = int.from_bytes(self.dynamic_heap.arr[table_addr+8:table_addr+12], byteorder='little')
        val += 1
        self.dynamic_heap.arr[table_addr+8:table_addr+12] = val.to_bytes(4, byteorder='little')
        
    def add_table_helper(self, table_addr, cappacity, is_set, key_value, value):
        key_index = self.find_table_cell(table_addr, cappacity, is_set, key_value)

        if key_index == None:
            raise Exception("Table is Full!")
        
        start_index, end_index = self.calculate_indices(key_index, is_set)
            
        if self.dynamic_heap.arr[key_index] != NULL:
            # If the key-value is none, it's already in the table
            return self.dynamic_heap.arr[start_index:end_index]
        else:     
            self.increment_table_entries(table_addr)
            if is_set:
                self.dynamic_heap.arr[start_index:end_index] = key_value
                return key_value
            else:
                self.dynamic_heap.arr[key_index:start_index] = key_value
                self.dynamic_heap.arr[start_index:end_index] = value  
                return key_value
                
    def add_table(self, table_value, key_value, value):
        """
        Add an element in a table. Assumes the key is not in the table.
        """        
                
        addr, _, total_entries, cappacity, is_set, resizable = self.read_table_header(table_value)

        # Extract the flags here
        gc = False
        
        if self.dynamic_heap.arr[addr] != HeapType.TABLE.value:
            raise Exception("Attempting to Add to a Non-Table Object")

        if total_entries + 1 > cappacity:
            if resizable:
                _, addr, cappacity = self.resize_table_helper(addr, resizable, cappacity, is_set, gc, 2) 
            else:
                raise Exception("Panic: Attempting to Add to Full Map!")     
        return self.add_table_helper(addr, cappacity, is_set, key_value, value)
          
    def search_table_helper(self, table_addr, cappacity, is_set, key_value):
        key_index = self.find_table_cell(table_addr, cappacity, is_set, key_value)
        
        if key_index == None:
            raise Exception("Coulnd't Find Key in Table!")
        
        start_index, end_index = self.calculate_indices(key_index, is_set)
            
        if self.dynamic_heap.arr[key_index] == NULL:
            raise Exception("Couldn't Find Key in Table!")
        else:
            return self.dynamic_heap.arr[start_index:end_index]
        
    def search_table(self, table_val, key_value):
        addr, size, total_entries, cappacity, is_set, resizable = self.read_table_header(table_val)
        return self.search_table_helper(addr, cappacity, is_set, key_value) 
    
    def modify_table_helper(self, table_addr, cappacity, is_set, key_value, value):
        key_index = self.find_table_cell(table_addr, cappacity, is_set, key_value)
        
        if is_set:
            raise Exception("Can't Modify Value of a Set!")
        
        if key_index == None:
            raise Exception("Coulnd't Find Key in Table!")
        
        start_index, end_index = self.calculate_indices(key_index, is_set)
            
        if self.dynamic_heap.arr[key_index] == NULL:
            raise Exception("Couldn't Find Key in Table!")
        else:
            self.dynamic_heap.arr[start_index:end_index] = value                
    
    def modify_table(self, table_val, key_value, value):
        addr, size, total_entries, cappacity, is_set, resizable = self.read_table_header(table_val)
        return self.modify_table_helper(addr, cappacity, is_set, key_value, value) 
    
    def access_structure(self, struct_val, key_value):
        if struct_val[0] != Values.ValueType.HEAP_OBJ.value:
            raise Exception("Attempting to Modify an Invalid Structure!")
        _, type, _, _ = self.read_heap_object_header(struct_val)    
        if type == TABLE:
            return self.search_table(struct_val, key_value)
        elif type == ARRAY:
            return self.arr_get_index(struct_val, key_value)
        elif type == PRIORITY_QUEUE:
            return self.priority_queue_get_priority(struct_val, key_value)
        else:
            raise Exception("Attempting to Modify Invalid Heap Structure!")
    
    def struct_pop_back(self, struct_val):
        if struct_val[0] != Values.ValueType.HEAP_OBJ.value:
            raise Exception("Attempting to Pop Back of an Invalid Structure!")
        _, type, _, _ = self.read_heap_object_header(struct_val)    
        
        if type == PRIORITY_QUEUE:
            return self.extract_max_priority_queue(struct_val)
        elif type == ARRAY:
            return self.arr_pop_back(struct_val)
        else:
            print(type, PRIORITY_QUEUE)
            raise Exception("Attempting to Pop Back of an Invalid Heap Structure!")
            
    def modify_structure(self, struct_val, key_value, value):
        if struct_val[0] != Values.ValueType.HEAP_OBJ.value:
            raise Exception("Attempting to Modify an Invalid Structure!")
        _, type, _, _ = self.read_heap_object_header(struct_val)    
        
        if type == TABLE:
            return self.modify_table(struct_val, key_value, value)
        elif type == ARRAY:
            return self.arr_modify_index(struct_val, key_value, value)
        elif type == PRIORITY_QUEUE:
            return self.max_heap_increase(struct_val, key_value, value)
        else:
            raise Exception("Attempting to Modify Invalid Heap Structure!")
    
    def pop_key_structure(self, struct_val, key_val):
        if struct_val[0] != Values.ValueType.HEAP_OBJ.value:
            raise Exception("Attempting to Modify an Invalid Structure!")
        _, type, _, _ = self.read_heap_object_header(struct_val)    
        
        if type == PRIORITY_QUEUE:
            return self.remove_key_priority_queue(struct_val, key_val)
        else:
            raise Exception("Attempting to Remove from an Invalid Heap Structure!")
            
    def struct_size(self, struct_val):
        if struct_val[0] != Values.ValueType.HEAP_OBJ.value:
            raise Exception("Attempting to Retrieve the Size of an Invalid Structure!")
        id = int.from_bytes(struct_val[4:], byteorder="little")
        addr = self.dynamic_heap.get_addr(id)
        size_bytes = self.dynamic_heap.unsafe_read_bytes(addr+8, 4)
        v = bytearray(8)
        v[0] = Values.ValueType.I32.value
        v[4:] = size_bytes
        return v
        
    def remove_from_table(self):
        pass
    
    def free_heap_object_helper(self, id):
        # Get the address
        addr = self.dynamic_heap.get_addr(id)
        # Read the size
        size = int.from_bytes(self.dynamic_heap.arr[addr+4:addr+8], byteorder="little")
        # Call free with the address and size
        self.dynamic_heap.free(id, size)
    
    def free_heap_object(self, obj_val):
        # Read in the id
        id = int.from_bytes(obj_val[4:], byteorder="little")
        self.free_heap_object_helper(id)
    
    def no_check_insert_table(self, table_addr, cappacity,  is_set, key_value, value):
        """
        Inserts an element into a table without checking if the element is already in the table. Used by resize for copying elements into a table.
        """
        i = 0
        offset = table_addr + 12
        relative_index = self.hash_value(cappacity, key_value, 0)
        step_size = 8
        if not is_set:
            step_size += 8
        index = offset + (relative_index * step_size)
        while i < cappacity:
            if self.dynamic_heap.arr[index] == NULL:
                self.dynamic_heap.arr[index:index+8] =key_value
                if not is_set:     
                    self.dynamic_heap.arr[index+8:index+8+8] = value
                return 
            relative_index = (relative_index + 1) % cappacity
            index = offset + (relative_index * step_size)
            i += 1
    
    def print_heap_object(self, obj_val):
        pass
    
    def resize_table_helper(self, table_addr, resizable, cappacity, is_set, gc, growth_factor):
        # Calculate the new cappacity
        new_cappacity = cappacity * growth_factor
        
        # Retrieve the original table ID
        og_id = self.dynamic_heap.get_id(table_addr)
        
        # Create a new table
        new_table = self.new_table(new_cappacity, resizable, is_set, gc)

        # Extract the address and ID of the new table
        new_table_id = int.from_bytes(new_table[4:], byteorder="little")
        new_table_addr = self.dynamic_heap.get_addr(new_table_id)

        # Offset by the header (12 bytes)
        offset = table_addr + 12
        
        # Step size; how far to move to the next cell
        step_size = 8
        
        # Add 8 bytes for key values
        if not is_set:
            step_size += 8
        
        # Index of the current cell, start at relative 0
        index = offset
        i = 0
        entry_count = 0
        
        # Go through the elements linearly
        while i < cappacity:
            # Add each non null value in the old table into the new table
            if is_set:
                # If its a set, just move the key
                if self.dynamic_heap.arr[index] != NULL:
                    self.no_check_insert_table(new_table_addr, new_cappacity, is_set, self.dynamic_heap.arr[index:index+8], None)
                    entry_count += 1
            else:
                # If its a key:value, move both
                if self.dynamic_heap.arr[index] != NULL:
                    self.no_check_insert_table(new_table_addr, new_cappacity, is_set, self.dynamic_heap.arr[index:index+8], self.dynamic_heap.arr[index+8:index+8+8])
                    entry_count += 1
            
            index += step_size
            i += 1

        # update entry count for the new table
        self.dynamic_heap.arr[new_table_addr+8:new_table_addr+12] = entry_count.to_bytes(4, byteorder="little")        
        self.free_heap_object_helper(og_id)
        self.dynamic_heap.heap_addrs[new_table_addr] = og_id
        del self.dynamic_heap.heap_ids[new_table_id]
        self.dynamic_heap.heap_ids[og_id] = new_table_addr        
        # Return an ID and essential meta data
        return self.val_as_heap_ref(og_id), new_table_addr, new_cappacity
    
    def resize_table(self, table_value):
        pass    