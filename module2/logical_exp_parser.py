import re
from typing import List
from module2.base_object import Node

class LogicalExpressionParser:
    def __init__(self):
        self.operators = {
            '¬': 5,
            '∀': 4,
            '∃': 4,
            '∧': 3,
            '∨': 2,
            '→': 1,
            '≡': 0
        }

    def tokenize(self, expression):
        # удаляем пробелы и разбиваем на токены
        expression = expression.replace(' ', '')
        tokens = re.findall(r'[\[\]a-zA-Z,_0-9А-Яа-яЁё]+|¬|∧|∨|→|≡|\(|\)|∀[a-zA-Z]|∃[a-zA-Z]', expression)
        return tokens

    def parse(self, expression):
        # получаем токены, находимся 0, вызываем парсер выражения
        tokens = self.tokenize(expression)
        self.tokens = tokens
        self.pos = 0
        return self.parse_expression()

    def parse_expression(self):
        return self.parse_binary_operator(0)

    def parse_binary_operator(self, prestige):
        # парсим левую часть (может быть унарной операцией (not) или атомарным выражением)
        left = self.parse_unary_part()
        # цикл пока встречаем операцию престижнее
        while (self.pos < len(self.tokens) and self.tokens[self.pos] in self.operators
               and self.operators[self.tokens[self.pos]] >= prestige):
            operator = self.tokens[self.pos]
            operator_prestige = self.operators[operator]
            self.pos += 1
            # рекурсивно парсим правую часть с учетом ассоциативности слева направо (+1 - для остановки на таких же операциях)
            right = self.parse_binary_operator(operator_prestige + 1)
            left = Node(operator, left, right)

        return left


    def parse_unary_part(self):
        # парсим унарную часть, если отрицание - то создается узел с одним ребенком (выражение/переменная)
        if self.pos < len(self.tokens) and self.tokens[self.pos] == '¬':
            operator = '¬'
            self.pos += 1
            operand = self.parse_unary_part()
            return Node(operator, operand, None)

        # обрабатываем кванторы ∀ и ∃
        if self.pos < len(self.tokens) and ('∀' in self.tokens[self.pos] or '∃' in self.tokens[self.pos]):
            quantifier = self.tokens[self.pos]
            self.pos += 1
            # парсим выражение, к которому применяется квантор или следующий квантор
            expression = self.parse_unary_part()
            return Node(quantifier, expression, None)

        return self.parse_atom()

    def parse_atom(self):
        # парсим элемент (выражение/переменная)
        token = self.tokens[self.pos]
        # выражение
        if token == '(':
            self.pos += 1
            expr = self.parse_expression()
            self.pos += 1
            return expr
        # элемент
        elif re.match(r'[\[\]a-zA-Z,_0-9А-Яа-яЁё]+', token):
            self.pos += 1
            return Node(token)


class TreeToStringConverter:
    def __init__(self):
        self.operators = {
            '¬': 5,
            '∧': 3,
            '∨': 2,
            '→': 1,
            '≡': 0
        }

    def get_precedence(self, node):
        op = node.value
        if op in self.operators:
            return self.operators[op]
        elif op.startswith('∀') or op.startswith('∃'):
            return 4
        else:
            return 6

    def convert(self, node, parent_precedence=-1):
        if node is None:
            return ""

        # Атомарный узел (переменная, предикат)
        if node.left is None and node.right is None:
            return node.value

        current_precedence = self.get_precedence(node)

        # Унарный оператор (отрицание)
        if node.value == '¬':
            child_str = self.convert(node.left, current_precedence)
            return '¬' + child_str

        # Кванторы
        if node.value.startswith('∀') or node.value.startswith('∃'):
            child_str = self.convert(node.left, -1)  # Не ставим скобки для внутренних выражений
            return node.value + '(' + child_str + ')'

        # Бинарные операторы
        left_str = self.convert(node.left, current_precedence)
        right_str = self.convert(node.right, current_precedence)
        result = left_str + ' ' + node.value + ' ' + right_str

        # Добавляем скобки если приоритет текущего оператора ниже родительского
        if current_precedence < parent_precedence:
            result = '(' + result + ')'

        return result