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
        
    # Store the results of the serial or parallel version
    result_ast = None
    
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    name = MPI.Get_processor_name()   
    
    result_ast = [interpreter.expand(m)]
    if rank == 0:
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
        "{" + ("expensive_statement;"*1) + "}",
        "{" + ("expensive_statement;"*2) + "}",
        "{" + ("expensive_statement;"*4) + "}",
        "{" + ("expensive_statement;"*8) + "}",
        "{" + ("expensive_statement;"*16) + "}",
        "{" + ("expensive_statement;"*32) + "}",
        "{" + ("expensive_statement;"*64) + "}",
        "{" + ("expensive_statement;"*128) + "}",
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

