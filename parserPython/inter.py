import re
from typing import List, Any

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
            ('PAREN',    r'[(){};]'),
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
        if self.current_token.type == 'IDENT':
            return self.parse_assignment()
        else:
            return self.parse_expression()

    def parse_assignment(self) -> ASTNode:
        identifier = self.current_token
        self.advance()
        if self.current_token.type == 'OP' and self.current_token.value == '=':
            self.advance()
            value = self.parse_expression()
            return ASTNode('Assignment', identifier.value, [value])
        raise SyntaxError("Invalid assignment")

    def parse_expression(self) -> ASTNode:
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

class Interpreter:
    def __init__(self):
        self.variables = {}

    def evaluate(self, node: ASTNode):
        if node.type == 'Number':
            return int(node.value)
        elif node.type == 'Identifier':
            if node.value in self.variables:
                return self.variables[node.value]
            raise NameError(f"Variable '{node.value}' is not defined")
        elif node.type == 'Assignment':
            value = self.evaluate(node.children[0])
            self.variables[node.value] = value
            return value

class Utils:
    def run_expression(self, code: str) -> str:
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        interpreter = Interpreter()
        result = interpreter.evaluate(ast)
        return str(result)

if __name__ == "__main__":
    utils = Utils()
    output = utils.run_expression('y = 4;')
    print(output)
