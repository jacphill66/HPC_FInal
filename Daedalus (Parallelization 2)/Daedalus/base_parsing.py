import lexing, parsing, analyzing, base_ast_objects

class BaseParser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.ast = None
        self.error = None       
        self.QUOTE_OPS = ("'", "`", "~")
        self.PREFIX_OPS = ("-", "!", "$")
        self.POSTFIX_OPS = ("!", "[", "#")
        self.INFIX_OPS = ("+", "-", "*", "/", "%", "^", "&&", "||", "<", ">", "==", "<=", ">=", "//", "?", "!!")
        
        #(infix/postfix prec, prefix prec, left_ass = true, right_ass = false
        self.PRECEDENCE_ASSOCIATIVITY = {        
            "+":(1, -1, True),
            "-":(1, 4, True),
            "*":(2, -1, True),
            "/":(2, -1, True),
            "//":(2, -1, True),
            "%":(2, -1, True),
            "^":(3, -1, False),
            "!":(4, 4, True),
            "#":(4, -1, True),
            "&&":(1, -1, True),
            "||":(1, -1, True),
            "?":(0, -1, True),
            "<":(0, -1, True),
            ">":(0, -1, True),
            "<=":(0, -1, True),
            ">=":(0, -1, True),
            "==":(0, -1, True),
            "(":(4, -1, True),   
            "[":(4, -1, True),
            "!!":(1, -1, True),
            "$":(-1, 4, True),
            "'":(-1, 0, True),   
            "`":(-1, 0, True),   
            "~":(-1, 4, True),   
            "@":(-1, 4, True),   
            "infix":(4, -1, True),
            "prefix":(4, 4, True),
            "postfix":(4, 4, True), 
        }

    def parse_annotation_or_expr(self):
        if parsing.curr_tok_val(self.tokens, self.pos) == "expr":
            return self.parse_expression()
        else:
            pass
    
    def parse_id_or_expr(self):
        if parsing.curr_tok_val(self.tokens, self.pos) == "expr":
            return self.parse_expression()
        else:
            tok, self.pos = parsing.next_token(self.tokens, self.pos)
            return base_ast_objects.BaseASTString(tok.value, tok.line, "IMMUTABLE")
            
    def parse_op_or_expr(self):
        if parsing.curr_tok_val(self.tokens, self.pos) == "expr":
            return self.parse_expression()
        else:
            tok, self.pos = parsing.next_token(self.tokens, self.pos)
            return base_ast_objects.BaseASTString(tok.value, tok.line, "IMMUTABLE")
            
    def parse_annotation_body(self):
        return self.parse_expression()
    
    def parse_class(self):
        self.pos += 1
        id = self.parse_id_or_expr()
        line = self.tokens[self.pos].line
        methods = {}
        _, self.pos = parsing.expect_token(self.tokens, self.pos, "{") 
        while parsing.curr_tok_val(self.tokens, self.pos) != "}":
            if parsing.curr_tok_val(self.tokens, self.pos) == "def":
                self.pos += 1
                m = self.parse_callable(False, True, self.tokens[self.pos].line)
                methods[m.id.value] = m
            else:
                print("Not implemented Yet!")
                exit()
        _, self.pos = parsing.expect_token(self.tokens, self.pos, "}")
        return base_ast_objects.BaseASTClass(id, methods, line)
                
    def get_line(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos].line
        return self.tokens[len(self.tokens)-1].line
    
    def get_prec(self, op, prefix):
        if op in self.PRECEDENCE_ASSOCIATIVITY.keys():
            if prefix:
                return self.PRECEDENCE_ASSOCIATIVITY[op][1]
            else:
                return self.PRECEDENCE_ASSOCIATIVITY[op][0]
        else:
            return -1

    def get_ass(self, op):
        if op in self.PRECEDENCE_ASSOCIATIVITY.keys():
            return self.PRECEDENCE_ASSOCIATIVITY[op][2]
        raise Exception("Internal Error: Invalid Operator")
    
    def parse_call(self, expr, line):
        args = []
        i = 0
        while self.pos < len(self.tokens) and parsing.curr_tok_val(self.tokens, self.pos) != ")":
            arg = self.parse_expression()
            args.append(arg)
            if parsing.curr_tok_val(self.tokens, self.pos) == ")":
                break
            else:
                _, self.pos = parsing.expect_token(self.tokens, self.pos, ",")
            i += 1
        _, self.pos = parsing.expect_token(self.tokens, self.pos, ")")
        return base_ast_objects.BaseASTCall(expr, args, line)
    
    def parse_key_value(self, closing_bracket):
        key_or_el = self.parse_expression()
        el = None
        if parsing.curr_tok_val(self.tokens, self.pos) == ":":
            self.pos += 1
            el = self.parse_expression()
        if parsing.curr_tok_val(self.tokens, self.pos) == closing_bracket:
            return key_or_el, el
        else:
            _, self.pos = parsing.expect_token(self.tokens, self.pos, ",")
        return key_or_el, el
            
    def parse_elements(self, closing_bracket):
        keys = []
        elements = []
        
        while self.pos < len(self.tokens) and parsing.curr_tok_val(self.tokens, self.pos) != closing_bracket:
            k, e = self.parse_key_value(closing_bracket)
            if e != None:
                keys.append(k)
                elements.append(e)
            else:
                keys.append(k)   
        _, self.pos = parsing.expect_token(self.tokens, self.pos, closing_bracket)

        
        if len(elements) != 0 and len(keys) != len(elements):
            raise Exception(f"The Number of Keys and Elements must Match in a Keyed Structure", self.get_line())
        return keys, elements
    
    def parse_table(self, line):
        keys, els = self.parse_elements("}")
        return base_ast_objects.BaseASTStruct(keys, els, "{", "}", line)
        
    def parse_array(self, line):
        keys, els = self.parse_elements("]")
        return base_ast_objects.BaseASTStruct(keys, els, "[", "]", line)   
    
    def parse_tuple_elements(self, expr):
        keys = [expr]
        elements = []
        if parsing.curr_tok_val(self.tokens, self.pos) == ":":
            _, self.pos = parsing.next_token(self.tokens, self.pos)
            elements.append(self.parse_expression())
        if parsing.curr_tok_val(self.tokens, self.pos) == ",":
            _, self.pos = parsing.next_token(self.tokens, self.pos)

        while self.pos < len(self.tokens) and parsing.curr_tok_val(self.tokens, self.pos) != ")":
            k, e = self.parse_key_value(")")
            if e != None:
                keys.append(k)
                elements.append(e)
            else:
                keys.append(k)   
        _, self.pos = parsing.expect_token(self.tokens, self.pos, ")")
        
        if len(elements) != 0 and len(keys) != len(elements):
            raise Exception(f"The Number of Keys and Elements must Match in a Keyed Structure", self.get_line())
        return keys, elements
    
    def parse_tuple(self, expr, line):
        keys, els = self.parse_tuple_elements(expr)
        return base_ast_objects.BaseASTStruct(keys, els, "(", ")", line)
    
    def parse_stack(self, line):
        keys, els = self.parse_elements("|>")
        return base_ast_objects.BaseASTStruct(keys, els, "<|", "|>", line)
    
    def parse_atom(self, token):
        if token.value == "statement":
            _, self.pos = parsing.expect_token(self.tokens, self.pos, "[")
            statement = self.parse_statement()
            _, self.pos = parsing.expect_token(self.tokens, self.pos, "]")
            return statement
        elif token.type == lexing.TokenType.INTEGER:
            return base_ast_objects.BaseASTInt(int(token.value), token.line)
        elif token.type == lexing.TokenType.FLOAT:
            return base_ast_objects.BaseASTFloat(float(token.value), token.line)
        elif token.type == lexing.TokenType.KEYWORD and token.value == "null":
            return base_ast_objects.BaseASTNull(token.line)
        elif token.type == lexing.TokenType.KEYWORD:
            if token.value == "true":
                return base_ast_objects.BaseASTBool(True, token.line)
            elif token.value == "false":
                return base_ast_objects.BaseASTBool(False, token.line)
            else:
                raise Exception(f"Invalid Keyword Literal", self.get_line())
        elif token.type == lexing.TokenType.STRING:
            return base_ast_objects.BaseASTString(token.value, token.line, "IMMUTABLE")
        elif token.type == lexing.TokenType.SYMBOL:
            if token.value == "{":
                return self.parse_table(token.line)
            elif token.value == "[":
                return self.parse_array(token.line)
            elif token.value == "(":
                return self.parse_tuple(token.line)
            elif token.value == "<|":
                return self.parse_stack(token.line)
            elif token.value == "_":
                return base_ast_objects.BaseASTEmtpyElement()
            else:   
                return base_ast_objects.BaseASTIdentifier(token.value, token.line)
        elif token.type == lexing.TokenType.IDENTIFIER:
            return base_ast_objects.BaseASTIdentifier(token.value, token.line)
        raise Exception(f"Invalid Literal", self.get_line())

    def parse_lhs(self):
        tok, self.pos = parsing.next_token(self.tokens, self.pos)
        if tok.value in self.PREFIX_OPS:
            ast = self.split(self.get_prec(tok.value, True))
            return base_ast_objects.BaseASTUnaryOp(ast, tok.value, True, tok.line)
        elif tok.value == "prefix":
            _, self.pos = parsing.expect_token(self.tokens, self.pos, "[")
            op = self.split(0)
            _, self.pos = parsing.expect_token(self.tokens, self.pos, "]")
            ast = self.split(self.get_prec(tok.value, True))
            return base_ast_objects.BaseASTUnaryOp(ast, op, True, tok.line)
        elif tok.value == "~":
            ast = self.split(self.get_prec(tok.value, True))
            return base_ast_objects.BaseASTQuoted(tok.value, ast, tok.line)
        elif tok.value in ("'", "`"):
            ast = self.split(self.get_prec(tok.value, True))
            return base_ast_objects.BaseASTQuoted(tok.value, ast, tok.line)
        elif tok.value == "@":
            annotation = self.parse_annotation_body()
            ast = self.split(self.get_prec(tok.value, True))
            return base_ast_objects.BaseASTAnnotatedExpression(annotation, ast, tok.line)
        elif tok.value == "(":
            if parsing.curr_tok_val(self.tokens, self.pos) == ")":
                _, self.pos = parsing.next_token(self.tokens, self.pos)
                return base_ast_objects.BaseASTStruct([], [], "(", ")", [-1, 8, True, False], tok.line)
            ast = self.split(0)
            if parsing.curr_tok_val(self.tokens, self.pos) in (",", ":"):               
                return self.parse_tuple(ast, tok.line)
            _, self.pos = parsing.expect_token(self.tokens, self.pos, ")")
            return ast
        else:
            return self.parse_atom(tok)
        raise Exception("Invalid Prefix Operator", self.get_line())
        
    def parse_rhs(self, prec, lhs):
        tok, self.pos = parsing.next_token(self.tokens, self.pos)
        if tok.value in self.POSTFIX_OPS:
            if tok.value == "[":
                key_or_index = self.parse_expression()
                _, self.pos = parsing.expect_token(self.tokens, self.pos, "]")
                return base_ast_objects.BaseASTStructRef(lhs, key_or_index, tok.line)
            else:
                return base_ast_objects.BaseASTUnaryOp(lhs, tok.value, False, tok.line)
        elif tok.value == "postfix":
            _, self.pos = parsing.expect_token(self.tokens, self.pos, "[")
            op = self.split(0)
            _, self.pos = parsing.expect_token(self.tokens, self.pos, "]")
            return base_ast_objects.BaseASTUnaryOp(lhs, op, False, tok.line)
        elif tok.value  == "(":
            return self.parse_call(lhs, tok.line)     
        elif tok.value == "infix":
            prec = prec+1 if self.get_ass(tok.value) else prec
            _, self.pos = parsing.expect_token(self.tokens, self.pos, "[")
            op = self.split(0)
            _, self.pos = parsing.expect_token(self.tokens, self.pos, "]")
            ast = self.split(prec)
            return base_ast_objects.BaseASTBinaryOp(lhs, op, ast, tok.line)
        elif tok.value in self.INFIX_OPS:
            prec = prec+1 if self.get_ass(tok.value) else prec
            ast = self.split(prec)
            return base_ast_objects.BaseASTBinaryOp(lhs, tok.value, ast, tok.line)
        raise Exception("Invalid Otherfix Operator", self.get_line())   

    def split(self, prec):
        lhs = self.parse_lhs()
        while self.pos < len(self.tokens) and self.get_prec(parsing.curr_tok_val(self.tokens, self.pos), False) >= prec:
            lhs = self.parse_rhs(prec, lhs)
        return lhs

    def parse_expression(self):
        if parsing.curr_tok_val(self.tokens, self.pos) == "expr":
            _, self.pos = parsing.next_token(self.tokens, self.pos)
            _, self.pos = parsing.expect_token(self.tokens, self.pos, "[")
            expr = self.parse_expression()
            _, self.pos = parsing.expect_token(self.tokens, self.pos, "]")
            return expr
        return self.split(0)
    
    def parse_params(self, line):
        params = []
        var_args = False
        _, self.pos = parsing.expect_token(self.tokens, self.pos, "(")
        i = 0
        while self.pos < len(self.tokens) and parsing.curr_tok_val(self.tokens, self.pos) != ")":
            annotation = None
            p = self.parse_id_or_expr()
            if parsing.curr_tok_val(self.tokens, self.pos) == ":":
                _, self.pos = parsing.next_token(self.tokens, self.pos)
                annotation = self.parse_expession()
            params.append([p, annotation])
            
            if parsing.curr_tok_val(self.tokens, self.pos) == "*":
                var_args = True
                self.pos += 1
                break
            if parsing.curr_tok_val(self.tokens, self.pos) == ")":
                break
            else:
                _, self.pos = parsing.expect_token(self.tokens, self.pos, ",")
            i += 1
        _, self.pos = parsing.expect_token(self.tokens, self.pos, ")")
        return params, var_args
        
    def parse_callable(self, is_macro, is_method, line):
        id = self.parse_id_or_expr()
        
        params, var_args = self.parse_params(line)
        annotation = None
        if parsing.curr_tok_val(self.tokens, self.pos) == "->":
            _, self.pos = parsing.next_token(self.tokens, self.pos)
            annotation = self.parse_expression()
        _, self.pos = parsing.expect_token(self.tokens, self.pos, "{")
        body = self.parse_block("}", line)
        
        if is_macro:
            return base_ast_objects.BaseASTCallable(id, params, annotation, body, "macro", var_args, body.line)
        elif is_method:
            body.statements.append(base_ast_objects.BaseASTReturn(base_ast_objects.BaseASTNull(body.line)))
            return base_ast_objects.BaseASTCallable(id, params, annotation, body, "method", var_args, body.line)
        else:
            body.statements.append(base_ast_objects.BaseASTReturn(base_ast_objects.BaseASTNull(body.line)))
            return base_ast_objects.BaseASTCallable(id, params, annotation, body, "func", var_args, body.line)
    
    def parse_return(self, line):
        expr = self.parse_expression()
        _, self.pos = parsing.expect_token(self.tokens, self.pos, ";")
        return base_ast_objects.BaseASTReturn(expr)
        
    def parse_if(self, line):
        expr = self.parse_expression()
        _, self.pos = parsing.expect_token(self.tokens, self.pos, "{")
        statement = self.parse_block("}", self.get_line())
        else_statement = None
        if self.pos < len(self.tokens) and parsing.curr_tok_val(self.tokens, self.pos) == "else":
            self.pos += 1
            _, self.pos = parsing.expect_token(self.tokens, self.pos, "{")
            else_statement = self.parse_block("}", self.get_line())
        return base_ast_objects.BaseASTIf(expr, statement, else_statement, line)
    
    def parse_while(self, line):
        expr = self.parse_expression()
        _, self.pos = parsing.expect_token(self.tokens, self.pos, "{")
        statement = self.parse_block("}", self.get_line())
        return base_ast_objects.BaseASTWhile(expr, statement, line)
        
    def parse_block(self, closed_bracket, line):
        statements = []
        while self.pos < len(self.tokens) and parsing.curr_tok_val(self.tokens, self.pos) != closed_bracket:
            statement = self.parse_statement()
            statements.append(statement)
        _, self.pos = parsing.expect_token(self.tokens, self.pos, closed_bracket)
        if closed_bracket == "}":
            return base_ast_objects.BaseASTBlock(statements, line)
        elif closed_bracket == "|}":
            return base_ast_objects.BaseASTSequence(statements, line)

        raise Exception(f"Invalid Block", self.get_line())
        
    def parse_var(self, line):
        id = self.parse_id_or_expr()

        annotation = None
        if parsing.curr_tok_val(self.tokens, self.pos) == ":":
            self.pos += 1
            annotation = self.parse_expression()
   
        op = self.parse_op_or_expr()
   
        expr = self.parse_expression()
           
        _, self.pos = parsing.expect_token(self.tokens, self.pos, ";")

        return base_ast_objects.BaseASTVariableDeclaration(id, annotation, op, expr, line)
    
    def parse_struct_modify(self, ref):
        val = self.parse_expression()
        _, self.pos = parsing.expect_token(self.tokens, self.pos, ";")
        return base_ast_objects.BaseASTStructModify(ref, val, tok.line)
        
    def parse_struct_op(self, ref, op):
        tok, self.pos = parsing.next_token(self.tokens, self.pos)
        key_or_val = self.parse_expression()
        val = None
        if parsing.curr_tok_val(self.tokens, self.pos) == ":":
            tok, self.pos = parsing.next_token(self.tokens, self.pos)
            val = self.parse_expression()    
        return base_ast_objects.BaseASTStructOp(ref, op, key_or_val, val, tok.line)
         
    def parse_other_statement(self, line):
        self.pos -= 1
        ref = self.parse_expression()
        if parsing.curr_tok_val(self.tokens, self.pos) == ";":
            self.pos += 1
            return base_ast_objects.BaseASTExprStatement(ref, line)
        else:
            op = self.parse_op_or_expr()
            
            expr1 = self.parse_expression()
            
            expr2 = None
            
            if parsing.curr_tok_val(self.tokens, self.pos) == ":":
                self.pos += 1
                expr2 = self.parse_expression()

            _, self.pos = parsing.expect_token(self.tokens, self.pos, ";")
            
            return base_ast_objects.BaseASTUpdateStatement(ref, op, expr1, expr2, line)
        
    def parse_loop(self, line):
        statement = self.parse_statement()
        return base_ast_objects.BaseASTLoop(statement, line)
    
    def parse_repeat(self, line):
        expr = self.parse_expression()
        statement = self.parse_statement()
        return base_ast_objects.BaseASTRepeat(expr, statement, line)
    
    def handle_expr_or_statement(line):
        pass
    
    def parse_raw_ast(self):
        pass
    
    def parse_statement(self):
        line = self.tokens[self.pos].line
        start = parsing.curr_tok_val(self.tokens, self.pos)
        self.pos += 1
        if start == "@":
            a = self.parse_annotation_body()
            s = self.parse_statement()
            return base_ast_objects.BaseASTAnnotatedStatement(a, s, line)
        elif start == "if":
            return self.parse_if(line)
        elif start == "while":
            return self.parse_while(line)
        elif start  == "loop":
            return self.parse_loop(line)
        elif start == "repeat":
            return self.parse_parse_repeat(line)
        elif start == "macro":
            return self.parse_callable(True, False, line)
        elif start == "def":
            return self.parse_callable(False, False, line)
        elif start == "return":
            return self.parse_return(line)
        elif start == "{|":
            return self.parse_block("|}", line)
        elif start == "{":
            return self.parse_block("}", line)
        elif start == "var":
            return self.parse_var(line)
        else:
            return self.parse_other_statement(line)

    def parse(self):
        statements = []
        while self.pos < len(self.tokens):
            s = None
            if parsing.curr_tok_val(self.tokens, self.pos) == "class":
                s = self.parse_class()
            else:
                s = self.parse_statement()
            statements.append(s)
        self.ast = statements
        return statements