import re
from typing import List

class Term:
    pass

class Var(Term):
    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if isinstance(other, Var):
            return self.name == other.name
        return False

    def __hash__(self):
        return hash(self.name)

    def is_constant(self):
        if self.name[0] in "xyzwtuv" and (len(self.name) == 1 or self.name[1].isdigit()):
            return False
        return True

class Functor(Term):
    def __init__(self, name: str, args: List[Term]):
        self.name = name
        self.args = args

    def __str__(self):
        args_str = ','.join(str(arg) for arg in self.args)
        return f"{self.name}[{args_str}]"

    def __eq__(self, other):
        if isinstance(other, Functor):
            if self.name != other.name or len(self.args) != len(other.args):
                return False
            return all(a == b for a, b in zip(self.args, other.args))
        return False

    def __hash__(self):
        return hash((self.name, tuple(self.args)))

class Predicate:
    def __init__(self, name: str, args: List[Term]):
        self.name = name
        self.args = args
        self.negation_flag = False

    def __str__(self):
        args_str = ','.join(str(arg) for arg in self.args)
        negation = ''
        if self.negation_flag:
            negation = '¬'
        return f"{negation}{self.name}[{args_str}]"

    def set_negation_flag(self, flag):
        self.negation_flag = flag

class Node:
    def __init__(self, value, left=None, right=None):
        self.object = None
        self.value = value
        self.left = left
        self.right = right
        if (value not in ['∧', '∨', '→', '≡', '¬']) and ('∀' not in value) and ('∃' not in value):
            self.parse_to_object()

    def parse_to_object(self):
        tokens = re.findall(r'[a-zA-Z_А-Яа-яЁё]+|\]|\[|,', self.value)
        predicate_name = tokens[0]
        pos = 1
        predicate_args = []
        if pos < len(tokens) and tokens[pos] == '[':
            pos += 1
            predicate_args, pos = self.parse_args(pos, tokens)
        self.object = Predicate(predicate_name, predicate_args)


    def parse_args(self, pos, tokens):
        args = []
        while pos < len(tokens) and tokens[pos] != ']':
            if tokens[pos] == ',':
                pos+=1
                continue
            term_name = tokens[pos]
            pos += 1
            if pos< len(tokens) and tokens[pos]=='[':
                pos+=1
                functor_args, pos = self.parse_args(pos, tokens)
                if pos < len(tokens) and tokens[pos] == ']':
                    pos += 1
                args.append(Functor(term_name, functor_args))
            else:
                args.append(Var(term_name))
        return args, pos

    def printer(self):
        print(str(self.object))

    def visualize_tree(self, prefix="", is_left=True):
        result = ""
        if self.right:
            result += self.right.visualize_tree(prefix + ("│   " if is_left else "    "), False)
        result += prefix + ("└── " if is_left else "┌── ") + str(self.value) + "\n"
        if self.left:
            result += self.left.visualize_tree(prefix + ("    " if is_left else "│   "), True)
        return result