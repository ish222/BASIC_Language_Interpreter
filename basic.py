# Imports
from cgitb import reset
from string_with_arrows import *
import string



# Digits constant
DIGITS = "0123456789"  # We'll use this to detect if a character is a digit
LETTERS = string.ascii_letters
LETTERS_DIGITS = LETTERS + DIGITS


# Error class
class Error:
    def __init__(self, pos_start, pos_end, error_name, details):  # The error class will take in an error name, its beginning and end positions and its complementary message or details
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_name = error_name
        self.details = details

    def message(self):  # Returns the error message containing details about the file name and the error location
        message = f"{self.error_name}: {self.details}\n"
        message += f"File {self.pos_start.file_name}, line {self.pos_start.line_num + 1}"
        message += "\n\n" + string_with_arrows(self.pos_start.file_text, self.pos_start, self.pos_end)  # Allows for arrow indicators in the error message for better readability
        return message

# Subclasses of the Error parent class for different error types
class IllegalCharError(Error):  # This is for illegal characters which are not recognised or don't have a complementary token
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, "Illegal character", details)  # Calls the parent constructor while passing the error name and details


class InvalidSyntaxError(Error):  # This is for errors in the parsing process for unrecognised syntax
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, "Invalid syntax", details)

class RunTimeError(Error):  # This is for errors picked up by the interpreter upon code execution
    def __init__(self, pos_start, pos_end, details, context):
        super().__init__(pos_start, pos_end, "Runtime error", details)
        self.context = context

    def message(self):
        message = self.generate_traceback()
        message += f"{self.error_name}: {self.details}\n"
        message += "\n\n" + string_with_arrows(self.pos_start.file_text, self.pos_start, self.pos_end)  # Allows for arrow indicators in the error message for better readability
        return message
        
    def generate_traceback(self):
        message = ""
        pos = self.pos_start
        context = self.context

        while context:  # Loops through the entire traceback to show the full origin and context of an error
            message = f"   File {pos.file_name}, line {str(pos.line_num + 1)}, in {context.display_name}\n" + message
            pos = context.parent_entry_pos
            context = context.parent

        return "Traceback (most recent call last):\n" + message


# Position Class
class Position:  # This will keep track of the line number, column number, current index, file name and file text.
    def __init__(self, index, line_num, col_num, file_name, file_text):
        self.index = index
        self.line_num = line_num
        self.col_num = col_num
        self.file_name = file_name
        self.file_text = file_text

    def advance(self, current_char = None):  # Advances into the next index and updates the line and column numbers if necessary
        self.index += 1
        self.col_num += 1
        
        if current_char == '\n':  # Checks if the current character is a new line which then increments the line number and resets the column number
            self.line_num += 1
            self.col_num = 0

        return self

    def copy(self):  # Creates a copy of the position
        return Position(self.index, self.line_num, self.col_num, self.file_name, self.file_text)



# Token constants for the different token types
T_INT = 'INT'
T_FLOAT = 'FLOAT'
T_PLUS = 'PLUS'
T_MINUS = 'MINUS'
T_MUL = 'MUL'
T_DIV = 'DIV'
T_POWER = 'POWER'  # E.g. 2^3=8
T_LBRAC = 'LBRAC'
T_RBRAC = 'RBRAC'
T_IDENTIFIER = 'IDENTIFIER'
T_KEYWORD = 'KEYWORD'
T_EQ = 'EQ'
T_EOF = 'EOF'  # Allows us to detect if we've reached the end of the file inside the parser

KEYWORDS = [
    "VAR", "INT", "FLOAT", "CHAR", "BOOL", "STRING"
]


# Token Class
class Token:
    def __init__(self, type_, value = None, pos_start = None, pos_end = None):
        self.type = type_  # This will denote what the token type is eg INT, PLUS, STRING etc...
        self.value = value  # The value of the token acquired from the input

        if pos_start:  # These position values are added to obtain the position of any error in the parser class, from the token
            self.pos_start = pos_start.copy()
            self.pos_end = pos_start.copy()  # If no position end is given, it is assumed to be the next token after the start
            self.pos_end.advance()
        
        if pos_end:
            self.pos_end = pos_end

    def matches(self, type_, value):
        return self.type == type_ and self.value == value

    def __repr__(self):  # This repr method is to provide an unambiguous description of the object for developer use
        if self.value:
            return f"{self.type}:{self.value}"
        return f"{self.type}"




# Lexer Class
class Lexer:
    def __init__(self, file_name, text):  # The raw text input will be passed into the constructor so it can be processed into its relevant tokens
        self.file_name = file_name
        self.text = text
        self.pos = Position(-1, 0, -1, file_name, text)  # Keeps track of the current position of the character in the text, the file name and contents and the index and column numbers are initialised to -1 so it can be looped through later
        self.current_char = None
        self.advance()  # Calls the advance method described below to change the position to 0 to start at the begining of the text
        
    def advance(self):  # This function increments into the next character in the input text
        self.pos.advance(self.current_char)
        self.current_char = self.text[self.pos.index] if self.pos.index < len(self.text) else None  # Checks that a higher index exists and increments to it unless its the final character where its set to None when incremented past

    def make_tokens(self):  # Creates the tokens by analysing the data in the input text
        tokens = []  # An empty list to hold the tokens
        while self.current_char is not None:  # Loops through all the characters in the text
            if self.current_char in " \t":  # Checks for spaces and tabs and ignores them
                self.advance()
            elif self.current_char in DIGITS:  # Since a number can be more than one character, we're going to use a function that obtains a number from the text
                tokens.append(self.get_number())
            elif self.current_char in LETTERS:
                tokens.append(self.make_identifier())
            elif self.current_char == '+':  # These statements check for all the different token types and then append the tokens list with each corresponding token object
                tokens.append(Token(T_PLUS, pos_start = self.pos))  # The positions of each of these tokens is tracked too
                self.advance()
            elif self.current_char == '-':
                tokens.append(Token(T_MINUS, pos_start = self.pos))
                self.advance()
            elif self.current_char == '*':
                tokens.append(Token(T_MUL, pos_start = self.pos))
                self.advance()
            elif self.current_char == '/':
                tokens.append(Token(T_DIV, pos_start = self.pos))
                self.advance()
            elif self.current_char == '(':
                tokens.append(Token(T_LBRAC, pos_start = self.pos))
                self.advance()
            elif self.current_char == ')':
                tokens.append(Token(T_RBRAC, pos_start = self.pos))
                self.advance()
            elif self.current_char == '^':
                tokens.append(Token(T_POWER, pos_start = self.pos))
                self.advance()
            elif self.current_char == '=':
                tokens.append(Token(T_EQ, pos_start = self.pos))
                self.advance()
            else:  # If we cant find a complementary token for the input character, then we have to raise an error
                pos_start = self.pos.copy()  # Makes a copy position object at the beginning of the error
                char = self.current_char  # Stores the illegal character
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, "'" + char + "'")  # Returns the start and end positions of the illegal characters, an empty list (signifying an error was raised) and creates a complementary error object

        tokens.append(Token(T_EOF, pos_start = self.pos))  # After successful tokenising, an End Of File token is appended to the tokens list
        return tokens, None  # If everything went well, the tokens list should be returned alongside None for the error

    def get_number(self):
        num_str = ""  # To keep track of the number in string form
        dot_count = 0  # To keep track of the number of dots in the number to allow for decimal input
        pos_start = self.pos.copy()  # Tracks the position of the initial number

        while self.current_char is not None and self.current_char in DIGITS + '.':  # Loops through all the characters of the number
            if self.current_char == '.':
                if dot_count == 1: break  # If there is already a dot in the number then you cannot have another so an error is raised
                dot_count += 1
                num_str += '.'
            else:
                num_str += self.current_char
            self.advance()

        if dot_count == 0:  # Checks if the dot count is zero meaning that the number must be an integer
            return Token(T_INT, int(num_str), pos_start, self.pos)
        else:  # If the number does have a decimal point then it must a floating point number
            return Token(T_FLOAT, float(num_str), pos_start, self.pos)

    def make_identifier(self):
        identifier_str = ""
        pos_start = self.pos.copy()

        while self.current_char != None and self.current_char in LETTERS_DIGITS + '_':
            identifier_str += self.current_char
            self.advance()

        tok_type  = T_KEYWORD if identifier_str in KEYWORDS else T_IDENTIFIER
        return Token(tok_type, identifier_str, pos_start, self.pos)



# Nodes class
class NumberNode:
    def __init__(self, tok):  # This will take in a number token (int or float)
        self.tok = tok

        self.pos_start = self.tok.pos_start
        self.pos_end = self.tok.pos_end

    def __repr__(self):
        return f"{self.tok}"


class VarAccessNode:
    def __init__(self, var_name_token):
        self.var_name_token = var_name_token

        self.pos_start = self.var_name_token.pos_start
        self.pos_end = self.var_name_token.pos_end


class VarAssignNode:
    def __init__(self, var_name_token, value_node):
        self.var_name_token = var_name_token
        self.value_node = value_node

        self.pos_start = self.var_name_token.pos_start
        self.pos_end = self.value_node.pos_end


class BinaryOpNode:  # This class will be for add, subtract, multiply and divide operations
    def __init__(self, left_node, op_token, right_node):  # This will take in the left node, the operation token and the right node
        self.left_node = left_node  # The number on the left of the operator
        self.op_token = op_token  # The operator
        self.right_node = right_node  # The number on the right of the operator

        self.pos_start = self.left_node.pos_start
        self.pos_end = self.right_node.pos_end

    def __repr__(self):
        return f"({self.left_node}, {self.op_token}, {self.right_node})"


class UnaryOpNode:  # This class allows us to implement the second and third factor types in the grammar text file (e.g. -5 and bracket functionality e.g. (5+3)*2)
    def __init__(self, op_token, node):
        self.op_token = op_token
        self.node = node

        self.pos_start = self.op_token.pos_start
        self.pos_end = node.pos_end

    def __repr__(self):
        return f"({self.op_token}, {self.node})"




# Parse result class (allows for easy error checking)
class ParseResult:
    def __init__(self):
        self.error = None  # This class will keep track of an error (if any exists) and the node
        self.node = None

    def register(self, result):
        if isinstance(result, ParseResult):
            if result.error: self.error = result.error
            return result.node

        return result

    def success(self, node):
        self.node = node
        return self

    def failure(self, error):
        self.error = error
        return self




# Parser class
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.token_idx = -1  # Will keep track of the index of the token (similar to Lexer)
        self.advance()

    def advance(self):
        self.token_idx += 1
        if self.token_idx < len(self.tokens):  # If the index is in range of the tokens
            self.current_token = self.tokens[self.token_idx]  # Grab that current token
        return self.current_token

    def parse(self):
        res = self.expr()
        if not res.error and self.current_token.type != T_EOF:  # If the final token type is not the end of file error, there was left over code to parse therefore there must've been a syntax error
            return res.failure(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected a valid arithmetic operator!"))
        return res



    def factor(self):  # This determines what type of factor we have
        result = ParseResult()
        token = self.current_token

        if token.type in (T_PLUS, T_MINUS):  # Checks if current token is an integer or a float
            result.register(self.advance())
            factor = result.register(self.factor())
            if result.error: return result
            return result.success(UnaryOpNode(token, factor))

        elif token.type == T_IDENTIFIER: 
            result.register(self.advance())
            return result.success(VarAccessNode(token))
        
        elif token.type in (T_INT, T_FLOAT):  # If token is of type integer or float, advance and return a number node of the token
            result.register(self.advance())
            return result.success(NumberNode(token))

        elif token.type == T_LBRAC:
            result.register(self.advance())
            expr = result.register(self.expr())
            if result.error: return result
            if self.current_token.type == T_RBRAC:
                result.register(self.advance())
                return result.success(expr)
            else:  # If right bracket is not found
                return result.failure(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected ')'"))

        return result.failure(InvalidSyntaxError(token.pos_start, token.pos_end, "Invalid syntax"))

    def term(self):  # A term is a factor multiplied/divided by another factor. See grammar.txt
        return self.binary_op(self.factor, (T_MUL, T_DIV, T_POWER))

    def expr(self):  # An expression is a term plus/minus another term.
        result = ParseResult()
        if self.current_token.matches(T_KEYWORD, 'VAR'):
            result.register(self.advance())
            if self.current_token.type != T_IDENTIFIER:
                return result.failure(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected identifier"))
            var_name = self.current_token
            result.register(self.advance())

            if self.current_token.type != T_EQ:
                return result.failure(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected '='"))
            result.register(self.advance())
            expr = result.register(self.expr())
            if result.error: return result
            return result.success(VarAssignNode(var_name, expr))

        return self.binary_op(self.term, (T_PLUS, T_MINUS))

    def binary_op(self, func, ops):
        """
        Takes a function which corresponds to the rule of the grammar (e.g. term, expression) and a list of accepted operation tokens
        relevant to the function (e.g. plus/minus for expressions), SEE grammar.txt
        """
        result = ParseResult()
        left = result.register(func())  # Obtains the left factor using the factor method defined above
        if result.error: return result

        while self.current_token.type in ops:
            op_token = self.current_token
            result.register(self.advance())
            right = result.register(func())
            if result.error: return result
            left = BinaryOpNode(left, op_token, right)

        return result.success(left)


# Runtime result class
class RunTimeResult:  # This class will keep track of the current result and errors (if any)
    def __init__(self):
        self.value = None
        self.error = None

    def register(self, result):
        if result.error: self.error = result.error
        return result.value

    def success(self, value):
        self.value = value
        return self

    def failure(self, error):
        self.error = error
        return self

# Number class
class Number:  # This class will be for storing numbers and then operating on them with numbers
    def __init__(self, value):
        self.value = value
        self.set_position()  # This is to track the position of the number in case of a mathematical error e.g. division by 0
        self.set_context()  # This is to track the context of the specific number node

    def set_position(self, pos_start=None, pos_end=None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self

    def set_context(self, context=None):
        self.context = context
        return self

    def added_to(self, other):
        if isinstance(other, Number):  # Checks if the types of the two objects to be added is the same
            return Number(self.value + other.value).set_context(self.context), None  # Created new number object with the operation of the function applied

    def subtracted_by(self, other):
        if isinstance(other, Number):
            return Number(self.value - other.value).set_context(self.context), None  # The second return is the error which for these operations is none

    def multiplied_by(self, other):
        if isinstance(other, Number):
            return Number(self.value * other.value).set_context(self.context), None

    def divided_by(self, other):
        if isinstance(other, Number):
            if other.value == 0:
                return None, RunTimeError(other.pos_start, other.pos_end, "Division by 0!", self.context)
            return Number(self.value / other.value).set_context(self.context), None

    def power_to(self, other):
        if isinstance(other, Number):
            return Number(pow(self.value, other.value)).set_context(self.context), None

    def __repr__(self):
        return str(self.value)

# Context class
class Context:  # This is a class to track the current context of the program
    def __init__(self, display_name, parent=None, parent_entry_pos=None):
        """
        string display_name  = Context name
        string parent = Parent context name
        string parent_entry_pos = Position in the code where the context changed
        """
        self.display_name = display_name
        self.parent = parent
        self.parent_entry_pos = parent_entry_pos
        self.symbol_table = None


# Symbol table class
class SymbolTable: # This is a class to track the variable names and their values
    def __init__(self):
        self.symbols = {}
        self.parent = None  # Symbol table for global variables

    def get(self, name):
        value = self.symbols.get(name, None)
        if value == None and self.parent:
           return self.parent.get(name)
        return value

    def set(self, name, value):
        self.symbols[name] = value

    def remove(self, name):
        del self.symbols[name]



# Interpreter class
class Interpreter:  # Interpreter will traverse through the node "tree" and by looking at the node types, it will determine the code to be executed
    def visit(self, node, context):
        """
        This will process the node provided and visit all the child nodes. There will be a different visit method for each node type.
        """
        method_name = f"visit_{type(node).__name__}"  # This will create a string with the name of the node type, e.g. visit_NumberNode.
        method = getattr(self, method_name, self.no_visit_method)
        return method(node, context)

    def no_visit_method(self, node, context):
        raise Exception(f"No visit_{type(node).__name__} method defined")

    def visit_NumberNode(self, node, context):
        return RunTimeResult().success(Number(node.tok.value).set_context(context).set_position(node.pos_start, node.pos_end))

    def visit_VarAccessNode(self, node, context):
        result = RunTimeResult()
        var_name = node.var_name_token.value
        value = context.symbol_table.get(var_name)

        if not value: return result.failure(RunTimeError(node.pos_start, node.pos_end, f"'{var_name}' is not defined!", context))
        return result.success(value)

    def visit_VarAssignNode(self, node, context):
        result = RunTimeResult()
        var_name = node.var_name_token.value
        value = result.register(self.visit(node.value_node, context))
        if result.error: return result
        context.symbol_table.set(var_name, value)
        return result.success(value)


    def visit_BinaryOpNode(self, node, context):
        result = RunTimeResult()
        left = result.register(self.visit(node.left_node, context))  # We need to visit the left and right child nodes of the binary operator node
        if result.error: return result
        right = result.register(self.visit(node.right_node, context))
        if result.error: return result

        # Now we need to check the operator type
        if node.op_token.type == T_PLUS:
            res, error = left.added_to(right)
        elif node.op_token.type == T_MINUS:
            res, error = left.subtracted_by(right)
        elif node.op_token.type == T_MUL:
            res, error = left.multiplied_by(right)
        elif node.op_token.type == T_DIV:
            res, error = left.divided_by(right)
        elif node.op_token.type == T_POWER:
            res, error = left.power_to(right)

        if error:
            return result.failure(error)
        else:
            return result.success(res.set_position(node.pos_start, node.pos_end))

    def visit_UnaryOpNode(self, node, context):
        result = RunTimeResult()
        number = result.register(self.visit(node.node, context))
        if result.error: return result

        error = None
        if node.op_token.type == T_MINUS:
            number, error = number.multiplied_by(Number(-1))  # Multiplies a number by -1 for the case of a single minus

        if error:
            return result.failure(error)
        else:
            return result.success(number.set_position(node.pos_start, node.pos_end))


# Run functions

global_symbol_table = SymbolTable()
global_symbol_table.set("NULL", Number(0))

def run(file_name, text):  # This is going to get the input text and return a list of token objects and an error if needed
    lexer = Lexer(file_name, text)
    tokens, error = lexer.make_tokens()
    if error: return None, error

    # Generate the abstract syntax tree (AST)
    parser = Parser(tokens)
    ast = parser.parse()
    if ast.error: return None, ast.error  # Returns out if an error is found during parsing

    # Running the program by creating an interpreter instance
    interpreter = Interpreter()
    context = Context("<program>")  # Root context of the whole program
    context.symbol_table = global_symbol_table
    result = interpreter.visit(ast.node, context)

    return result.value, result.error
