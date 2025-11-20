from module2.base_object import Var, Functor, Predicate, Node

class Skolemizer:
    def __init__(self):
        self.used_constants = set()
        self.used_functions = set()

    def generate_unique_constant(self):
        # Генератор имени константы
        base_chars = "abcdeijklmnopqrs"
        for char in base_chars:
            if char not in self.used_constants:
                return char
        # Если все одиночные символы заняты, добавляем индексы
        counter = 1
        while True:
            for char in base_chars:
                candidate = f"{char}{counter}"
                if candidate not in self.used_constants:
                    return candidate
            counter += 1

    def generate_unique_function(self):
        # Генератор имя функции
        base_names = ["f", "g", "h"]
        for name in base_names:
            if name not in self.used_functions:
                return name
        # Все базовые заняты, генерируем с индексами
        counter = 1
        while True:
            for name in base_names:
                candidate = f"{name}{counter}"
                if candidate not in self.used_functions:
                    return candidate
            counter += 1

    def build_skolem_form(self, form: Node):
        # Главный метод
        result  =self.skolem_recursive(form, [])
        self.used_constants.clear()
        self.used_functions.clear()
        return result

    def skolem_recursive(self, node: Node, vars: list):

        if node is None:
            return None

        if '∀' in node.value:
            var_name = node.value[1:]
            vars = vars + [var_name]
            new_left = self.skolem_recursive(node.left, vars)
            return Node (node.value, new_left, None)
        elif '∃' in node.value:
            var_name = node.value[1:]

            if len(vars) == 0:
                new_constant = self.generate_unique_constant()
                self.used_constants.add(new_constant)
                new_left = self.replace_vars(node.left, var_name, new_constant)
                return self.skolem_recursive(new_left, vars)
            else:
                function_name = self.generate_unique_function()
                self.used_functions.add(function_name)
                args =[]
                for arg in vars:
                    args.append(Var(arg))
                new_left = self.replace_vars(node.left, var_name, function_name, True, args)
                return self.skolem_recursive(new_left, vars)
        return node

    def replace_vars(self, node: Node, old, new, flag=False, f_args=None):
        # Вспомогательная функция замены переменной в поддереве квантора
        if node is None:
            return None
        # Если узел - предикат
        if node.object is not None and isinstance(node.object, Predicate):
            new_args = []
            # Делаем замену в его термах
            for arg in node.object.args:
                new_arg  = self.replace_var_in_term(arg, old, new, flag, f_args)
                new_args.append(new_arg)
            predicate = Predicate(node.object.name, new_args)
            #new_left = self.replace_vars(node.left, old, new, flag, f_args)
            #new_right = self.replace_vars(node.right, old, new, flag, f_args)
            return Node(str(predicate))

        new_left = self.replace_vars(node.left, old, new, flag, f_args)
        new_right = self.replace_vars(node.right, old, new, flag, f_args)
        return Node(node.value, new_left, new_right)

    def replace_var_in_term(self, term, old, new, is_function=False, f_args=None):
        if isinstance(term, Var):
            # Если это переменная, которую нужно заменить
            if term.name == old:
                if not is_function:
                    # Замена на новое имя
                    return Var(new)
                else:
                    # Замена на функтор
                    return Functor(new, f_args)
            else:
                # Оставляем как есть
                return term
        elif isinstance(term, Functor):
            # Рекурсивно обрабатываем аргументы функтора
            new_args = []
            for arg in term.args:
                new_arg = self.replace_var_in_term(arg, old, new, is_function, f_args)
                new_args.append(new_arg)
            # Создаем новый функтор с обновленными аргументами
            return Functor(term.name, new_args)
        else:
            return term
