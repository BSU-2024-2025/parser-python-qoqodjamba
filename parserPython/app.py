from flask import Flask, render_template, request, jsonify
import re
from typing import List, Any
import io

# Классы Lexer, Parser, Interpreter, и Utils остаются прежними

app = Flask(__name__)

class Token:
    def __init__(self, type: str, value: Any):
        self.type = type
        self.value = value

    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)})"

class Lexer:
    def __init__(self, source_code: str):
        self.source_code = source_code
        self.tokens = []
        self.token_specification = [
            ('NUMBER',   r'\d+'),
            ('IDENT',    r'[a-zA-Z_][a-zA-Z0-9_]*'),
            ('OP',       r'[+\-*/%!=<>&|]+'),
            ('PAREN',    r'[(){}]'),
            ('SEMICOLON', r';'),
            ('WHITESPACE', r'\s+'),
        ]

    def tokenize(self) -> List[Token]:
        token_regex = '|'.join(f'(?P<{name}>{regex})' for name, regex in self.token_specification)
        for match in re.finditer(token_regex, self.source_code):
            kind = match.lastgroup
            value = match.group()
            if kind == 'WHITESPACE':
                continue
            self.tokens.append(Token(kind, value))
        return self.tokens

class ASTNode:
    def __init__(self, type: str, value: Any = None, children: List['ASTNode'] = None):
        self.type = type
        self.value = value
        self.children = children or []

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current_token = None
        self.pos = -1
        self.advance()

    def advance(self):
        self.pos += 1
        self.current_token = self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def parse(self) -> ASTNode:
        return self.parse_statement()

    def parse_statement(self) -> ASTNode:
        if self.current_token.type == 'IDENT' and self.current_token.value == 'print':
            return self.parse_print()
        elif self.current_token.type == 'IDENT':
            return self.parse_assignment()
        else:
            return self.parse_expression()

    def parse_assignment(self) -> ASTNode:
        identifier = self.current_token
        self.advance()
        if self.current_token.type == 'OP' and self.current_token.value == '=':
            self.advance()
            value = self.parse_expression()
            if self.current_token and self.current_token.type == 'SEMICOLON':
                self.advance()
            return ASTNode('Assignment', identifier.value, [value])
        raise SyntaxError("Invalid assignment")

    def parse_print(self) -> ASTNode:
        self.advance()  # Skip 'print'
        if self.current_token.type == 'PAREN' and self.current_token.value == '(':
            self.advance()
            expr = self.parse_expression()
            if self.current_token.type == 'PAREN' and self.current_token.value == ')':
                self.advance()
                if self.current_token and self.current_token.type == 'SEMICOLON':
                    self.advance()
                return ASTNode('Print', None, [expr])
        raise SyntaxError("Invalid syntax for print")

    def parse_expression(self) -> ASTNode:
        left = self.parse_term()
        while self.current_token and self.current_token.type == 'OP' and self.current_token.value in ['+', '-', '==', '!=', '<', '>', '<=', '>=']:
            op = self.current_token
            self.advance()
            right = self.parse_term()
            left = ASTNode('BinaryOp', op.value, [left, right])
        return left


    def parse_term(self) -> ASTNode:
        left = self.parse_factor()
        while self.current_token and self.current_token.type == 'OP' and self.current_token.value in ['*', '/']:
            op = self.current_token
            self.advance()
            right = self.parse_factor()
            left = ASTNode('BinaryOp', op.value, [left, right])
        return left

    def parse_factor(self) -> ASTNode:
        token = self.current_token
        if token.type == 'NUMBER':
            self.advance()
            return ASTNode('Number', token.value)
        elif token.type == 'IDENT':
            self.advance()
            return ASTNode('Identifier', token.value)
        elif token.type == 'PAREN' and token.value == '(':
            self.advance()
            node = self.parse_expression()
            if self.current_token.type == 'PAREN' and self.current_token.value == ')':
                self.advance()
            return node
        raise SyntaxError("Invalid syntax")

class Interpreter:
    def __init__(self):
        self.variables = {}

    def evaluate(self, node: ASTNode, output: io.StringIO):
        if node.type == 'Number':
            return int(node.value)
        elif node.type == 'Identifier':
            if node.value in self.variables:
                return self.variables[node.value]
            raise NameError(f"Variable '{node.value}' is not defined")
        elif node.type == 'Assignment':
            value = self.evaluate(node.children[0], output)
            self.variables[node.value] = value
            return value
        elif node.type == 'BinaryOp':
            left = self.evaluate(node.children[0], output)
            right = self.evaluate(node.children[1], output)
            if node.value == '+':
                return left + right
            elif node.value == '-':
                return left - right
            elif node.value == '*':
                return left * right
            elif node.value == '/':
                return left // right  # Integer division
            raise ValueError(f"Unsupported operator: {node.value}")
        elif node.type == 'Print':
            value = self.evaluate(node.children[0], output)
            output.write(str(value) + '\n')
            return None

class Utils:
    def __init__(self):
        self.interpreter = Interpreter()

    def run_expression(self, code: str):
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        output = io.StringIO()
        
        # If the statement is an assignment, execute it but do not print anything
        if ast.type == 'Assignment':
            self.interpreter.evaluate(ast, output)
        # Only print if it's a Print node
        elif ast.type == 'Print':
            self.interpreter.evaluate(ast, output)

        return output.getvalue()


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run_code', methods=['POST'])
def run_code():
    code = request.form['code']
    utils = Utils()
    try:
        result = ""
        for line in code.splitlines():
            if line.strip():
                result += utils.run_expression(line.strip())
        
        if result:
            return jsonify(success=True, message="Code executed successfully!", output=result)
        else:
            return jsonify(success=True, message="Code executed successfully but no output.", output="")
    except Exception as e:
        return jsonify(success=False, message=f"Error: {e}", output="")

if __name__ == '__main__':
    app.run(debug=True)
