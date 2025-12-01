from mpi4py import MPI
import time
import base_lexing, base_parsing, compiling, interpreting, heaping, analyzing, expansion, interpreter, base_ast_objects
from ParserBuilder import *

def build_compiler(grammar, expansion_classes):
    builder = ParserBuilder()
    parser = builder.build_parser(grammar)
    
    l = base_lexing.BaseLexer(expansion_classes)
    tokens = l.lex_base()
    p = base_parsing.BaseParser(tokens)
    ast = p.parse()
    e = expansion.Expander()
    ast = e.expand(ast)
    i = interpreter.Interpreter()
    for s in ast:
        if type(s) == base_ast_objects.BaseASTClass:
            i.add_class(s)
        elif type(s) == base_ast_objects.BaseASTCallable and s.call_type == "func":
            i.add_function(s)
        else:
            print(s)
            raise Exception("Each Statement Must be a Valid Operation Class!")
    
    return parser, i

def parallel_expand(parser, interpreter, program, run=False):
    t0 = time.perf_counter()
    
    # Generate a RAW AST for the program
    m = parser.match(program)
    result_ast = [None] * len(m.children)
    
    # Standard MPI
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    name = MPI.Get_processor_name()    
    
    # Store the results of the serial or parallel version
    result_ast = None
    
    # If the size exceeds the number of children, run it in serial
    # (There needs to be at least one statement per process)
    if size > len(m.children):
        if rank == 0:
            result_ast = [interpreter.expand(m)]
            if run:
                analyzer = analyzing.BaseASTAnalyzer(result_ast)   
                analyzer.type_check()
                if len(analyzer.type_errors) > 0:
                    analyzer.print_type_errors()
                    exit()

                c = compiling.BaseCompiler(result_ast)
                ops, consts, static_objs = c.compile()
                    
                vm = interpreting.VM(1024, ops, consts, static_objs)
                vm.execute()
                print(time.perf_counter() - t0)
    else:
        # Run it in parallel only if the Raw AST can be partitioned into at least one statement per process
        
        # Determine groupings based on the size and the number of statements
        rem = len(m.children) % size
        step = len(m.children) // size
        start = rank*step
        end = start + step

        if rem > 0 and end + rem == len(m.children):
            end += rem
            
        # Expand each group of statements in parallel
        result_ast = [None] * (end-start)
        for i in range(start, end):
            result_ast[i-start] = interpreter.expand(m.children[i])  

        # Gather the results into result_ast
        result_ast = comm.gather(result_ast, root=0)

        # Only evaluate the resulting program in one process
        if rank == 0:
            # print(f"Data: {result_ast}, Rank: {rank}")
            lst = []

            # Gather produces a list of lists, turn them into one list
            for l in result_ast:
                for s in l:
                    lst.append(s)
            result_ast = lst
            print("Time:", time.perf_counter() - t0)
            
            # Run (analyze -> compile -> execute) the program
            if run:
                analyzer = analyzing.BaseASTAnalyzer(result_ast)   
                analyzer.type_check()
                if len(analyzer.type_errors) > 0:
                    analyzer.print_type_errors()
                    exit()

                c = compiling.BaseCompiler(result_ast)
                ops, consts, static_objs = c.compile()
                
                vm = interpreting.VM(1024, ops, consts, static_objs)
                vm.execute()
                
    if rank == 0:
        # A useful tooltip for debugging (ensure the program finishes)
        print("Completed Execution")        
                
if __name__ == "__main__":
    # PEG
    grammar = """
            start = all_white_space* (statement[statement] all_white_space*)*;
            statement = i_statement[s] | w_statement[s] | slowly_statement[s] | expensive_statement[s] | expression_statement[s] | print_statement[p] | var_statement[v] | var_assignment[v] | jack_loop[j] | fib_loop[f] | block_statement[b];
            slowly_statement = "slowly" white_space* statement[s];
            jack_loop = "jack" all_white_space* block_statement[block];
            fib_loop = "fib" white_space+ num_expr[n$] all_white_space* block_statement[block];
            expensive_statement = "expensive_statement" ";";
            print_statement = "print" white_space*  expression[e] ";";
            var_assignment = reference[r] white_space* "=" white_space* expression[e] ";";
            i_statement = "if" white_space+ expression[e]  all_white_space* block_statement[block];
            w_statement = "while" white_space+ expression[e] all_white_space* block_statement[block];
            var_statement = "var" white_space* identifier[id$] white_space* "=" white_space* expression[e] white_space* ";";
            block_statement = "{" all_white_space* (statement[s] all_white_space*)* "}";
            expression_statement = expression[e]";";
            expression = binary_expression[e] | value_expression;
            binary_expression = value_expression[v1] op[o$] expression[v2];
            value_expression = num_expr[n$] | bool_expr[b$] | reference[r];
            op = "+" | "-" | "*" | "<" | "%" | "==";
            white_space = " " | "   ";
            all_white_space = " " | "   " | "\n";
            num_expr = digit+;
            digit = "0" | "1" | "2" |"3" | "4" | "5" | "6" | "7" | "8" | "9";
            bool_expr = "true" | "false";
            identifier = alnum+;
            alnum = "a" | "b" | "c" | "d" | "e" | "f" | "g" | "h" | "i" | "k" | "l" | "m" | "n" | "o" | "p" |"q" | "r" | "s" | "t" | "u" | "v" | "w" | "x" | "y" | "z";
            reference = identifier[id$];
        """
    
    # Expansion Classes
    expansion_classes = """
        def fib(n){
            if n < 2 {
                return n;
            }
            else {
                return fib(n-1) + fib(n-2);
            }
        }
    
        class start {
            def expand(s*) {         
                return unpack(s);
            }
        }
        
        class comp_time {
            def expand(s) {
                eval(eval(s));
                return 'statement[null;];
            }            
        }
                
        class slowly_statement{
            def expand(s){
                var count = 0;
                while count < 100000 {
                    count = count + 1;
                }
                return s;
            }
        }
        
        class expensive_statement{
            def expand(){
                var count = 0;
                while count < 1000000 {
                    count = count + 1;
                }
                return 'statement[null;];
            }
        }
        
        class fib_loop{
            def expand(n, s){
                return `statement[{|
                    ~`statement[var count = ~fib(n);];
                    ~`statement[
                        while count > 0 {
                            ~s;
                            count = count-1;
                        }
                    ];
                |}];
            }
        }
        
        class jack_loop{
            def expand(s){
                return `statement[
                    while true {
                        ~s;
                    }
                ];
            }
        }
        
        
        class reference{
            def expand(r){
                return ID(r);
            }
        }
        
        class var_statement{
            def expand(id, e){
                return `statement[var expr[(~id)] = (~e);];
            }
        }
        
        class var_assignment {
            def expand(id, e){
                return `statement[expr[(~id)] = (~e);];
            }
        }
        
        class identifier{
            def expand(id){
                return id;
            }
        }
        
        class statement {
            def expand(s) {
                return s;
            }
        }        
        
        class print_statement{
            def expand(e){
                var a = `print(~e);
                return `statement[
                    ~a;
                ];
            }
        }
        
        class w_statement{
            def expand(e, s) {
                return `statement[
                    while ~e {
                        ~s;
                    }
                ];
            }
        }
        
        class i_statement{
            def expand(e, s) {
                return `statement[
                    if ~e {
                        ~s;
                    }
                ];
            }
        }
        
        class block_statement{
            def expand(b*) {
                return unpack(b);
            }
        }
        
        class binary_expression {
            def expand(lhs, op, rhs){
                return `((~lhs) infix[~op] (~rhs));
            }
        }
        
        class value_expression {
            def expand(v){
                return v;
            }
        }
        
        class op {
            def expand(op){
                return op;
            }
        }
        
        class num_expr {
            def expand(i) {
                return int(i);
            }
        }
        
        class expression {
            def expand(e) {
                return e;
            }
        }
        
        class expression_statement {
            def expand(e){                
                return `statement[
                    ~e;
                ];
            }
        }
        
        class bool_expr{
            def expand(e) {
                if e == "true"{
                    return true;
                }
                else{
                    return false;
                }
            }
        }

    """
    
    # Build a compiler based on the PEG and Expansion Classes
    p, i = build_compiler(grammar, expansion_classes)
    
    # Input program
    progs = [
        "1+2+3;"*1000,
        "1+2+3;"*2000,
        "1+2+3;"*4000,
        "1+2+3;"*8000,
        "1+2+3;"*16000,
        "1+2+3;"*32000,
        "1+2+3;"*64000,
        "1+2+3;"*128000,
    ]
    

    for prog in progs:
        parallel_expand(p, i, prog, run=True)



"""
        var count = 0;
        while count<10000{
            if 0==count%2{
                print count;
            }
            count = count+1;
        }
    """

"""
    expensive_statement;
    expensive_statement;
    expensive_statement;
    expensive_statement;
    expensive_statement;
    expensive_statement;
"""

# Don't use the id count within a fib loop
"""
    var a = 0;
    fib 10 {
        a = a+1;
    }
    print a;
"""

