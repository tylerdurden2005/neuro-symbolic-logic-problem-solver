from pydoc import replace

from module2.base_object import Var, Functor, Predicate, Node
class Prenexer:
    def __init__(self):
        self.used_names = set()
    def replacement_impl_equiv(self, node: Node):
        # убираем импликации и эквиваленции в формуле
        if node is None:
            return None

        new_left = self.replacement_impl_equiv(node.left)
        new_right = self.replacement_impl_equiv(node.right)
        # заменяем операторы
        if node.value == '→':
            # A → B ≡ ¬A ∨ B
            not_left = Node('¬', new_left, None)
            return Node('∨', not_left, new_right)

        elif node.value == '≡':
            # A ≡ B ≡ (¬A ∨ B) ∧ (¬B ∨ A)
            not_a = Node('¬', new_left, None)
            not_b = Node('¬', new_right, None)
            left_impl = Node('∨', not_a, new_right)  # ¬A ∨ B
            right_impl = Node('∨', not_b, new_left)  # ¬B ∨ A
            return Node('∧', left_impl, right_impl)

        else:
            # для всех других операторов возвращаем узел с обработанными потомками
            return Node(node.value, new_left, new_right)

    def push_negation_to_atoms(self, node):
        # проталкивание отрицания к атомарным формулам
        if node is None:
            return None
        # если это отрицание
        if node.value == '¬':
            child = node.left
            # двойное отрицание: ¬¬A ≡ A
            if child.value == '¬':
                return self.push_negation_to_atoms(child.left)

            # закон де Моргана: ¬(A ∧ B) ≡ ¬A ∨ ¬B
            elif child.value == '∧':
                left_neg = Node('¬', child.left)
                right_neg = Node('¬', child.right)
                new_left = self.push_negation_to_atoms(left_neg)
                new_right = self.push_negation_to_atoms(right_neg)
                return Node('∨', new_left, new_right)

            # закон де Моргана: ¬(A ∨ B) ≡ ¬A ∧ ¬B
            elif child.value == '∨':
                left_neg = Node('¬', child.left)
                right_neg = Node('¬', child.right)
                new_left = self.push_negation_to_atoms(left_neg)
                new_right = self.push_negation_to_atoms(right_neg)
                return Node('∧', new_left, new_right)

            # для кванторов: ¬∀x P(x) ≡ ∃x ¬P(x)
            elif '∀' in child.value:
                new_quant = child.value.replace('∀', '∃')
                new_body = Node('¬', child.left)
                return Node(new_quant, self.push_negation_to_atoms(new_body))

            # для кванторов: ¬∃x P(x) ≡ ∀x ¬P(x)
            elif '∃' in child.value:
                new_quant = child.value.replace('∃', '∀')
                new_body = Node('¬', child.left)
                return Node(new_quant, self.push_negation_to_atoms(new_body))
            else:
                # предикаты
                return node

        # обрабатываем кванторы, как встреченные узлы
        elif '∀' in node.value or '∃' in node.value:
            new_body = self.push_negation_to_atoms(node.left)
            return Node(node.value, new_body)

        # обрабатываем бинарные операторы, как встреченные узлы
        elif node.value in ['∧', '∨']:
            new_left = self.push_negation_to_atoms(node.left)
            new_right = self.push_negation_to_atoms(node.right)
            return Node(node.value, new_left, new_right)
        else:
            # предикаты
            return node

    def generate_unique_name(self):
        # генератор имени переменной
        base_chars = "xyzwtuv"
        for char in base_chars:
            if char not in self.used_names:
                return char
        # если все одиночные символы заняты, добавляем индексы
        counter = 1
        while True:
            for char in base_chars:
                candidate = f"{char}{counter}"
                if candidate not in self.used_names:
                    return candidate
            counter += 1

    def rename_related_vars(self, node: Node):
        # переименование связанных переменных
        if node is None:
            return None

        # если узел - квантор
        if '∀' in node.value or '∃' in node.value:
            quantifier_char = node.value[0]
            var_name = node.value[1:]

            # проверяем, использовалось ли уже это имя переменной в формуле
            if var_name in self.used_names:
                # конфликт имен - генерируем новое имя
                new_name = self.generate_unique_name()
                # заменяем имя переменной в кванторе
                node.value = quantifier_char + new_name
                self.used_names.add(new_name)
                # заменяем все вхождения этой переменной в поддереве квантора
                if node.left:
                    node.left = self.replace_vars(node.left, var_name, new_name)
            else:
                # имя не использовалось, добаляется в множество использоанных
                self.used_names.add(var_name)
            # обрабатываем поддерево
            node.left = self.rename_related_vars(node.left)
        else:
            node.left = self.rename_related_vars(node.left)
            node.right = self.rename_related_vars(node.right)
        return node

    def replace_vars(self, node: Node, old, new):
        # вспомогательная функция замены переменной в поддереве квантора
        if node is None:
            return None
        # если встретили квантор с именем переменной, которую меняем
        if ('∀' in node.value or '∃' in node.value) and node.value[1:] == old:
            return node
        #
        if '∀' in node.value or '∃' in node.value:
            new_left = self.replace_vars(node.left, old, new)
            return Node(node.value, new_left, node.right)
        # если узел - предикат
        if node.object is not None and isinstance(node.object, Predicate):
            new_args = []
            # делаем замену в его термах
            for arg in node.object.args:
                new_arg = self.replace_var_in_term(arg, old, new)
                new_args.append(new_arg)
            predicate = Predicate(node.object.name, new_args)
            #new_left = self.replace_vars(node.left, old, new)
            #new_right = self.replace_vars(node.right, old, new)
            return Node(str(predicate))
        # операции
        new_left = self.replace_vars(node.left, old, new)
        new_right = self.replace_vars(node.right, old, new)
        return Node(node.value, new_left, new_right)


    def replace_var_in_term(self, term, old, new):
        # переименование термов
        if isinstance(term, Var):
            # если это переменная, которую нужно заменить
            if term.name == old:
                # замена на новое имя
                return Var(new)
            else:
                # оставляем как есть
                return term
        elif isinstance(term, Functor):
            # рекурсивно обрабатываем аргументы функтора
            new_args = []
            for arg in term.args:
                new_arg = self.replace_var_in_term(arg, old, new)
                new_args.append(new_arg)
            # создаем новый функтор с обновленными аргументами
            return Functor(term.name, new_args)
        else:
            return term

    def to_CNF(self, node: Node):
        # приводим матрицу к КНФ
        if node is None:
            return None

        # рекурсивно преобразуем потомков
        left_cnf = self.to_CNF(node.left)
        right_cnf = self.to_CNF(node.right)

        # обрабатываем операторы
        if node.value == '∧':
            # просто возвращаем
            return Node('∧', left_cnf, right_cnf)

        elif node.value == '∨':
            # применяем дистрибутивность
            return self.distribute_or(left_cnf, right_cnf)

        else:
            # для всех других узлов (кванторы, предикаты, отрицания)
            return Node(node.value, left_cnf, right_cnf)

    def distribute_or(self, left, right):
        # применяем дистрибутивность
        # если левая часть - конъюнкция: (A ∧ B) ∨ C ≡ (A ∨ C) ∧ (B ∨ C)
        if left and left.value == '∧':
            a = left.left
            b = left.right
            c = right
            return Node('∧',self.distribute_or(a, c),self.distribute_or(b, c))

        # если правая часть - конъюнкция: A ∨ (B ∧ C) ≡ (A ∨ B) ∧ (A ∨ C)
        elif right and right.value == '∧':
            a = left
            b = right.left
            c = right.right
            return Node('∧',
                        self.distribute_or(a, b),
                        self.distribute_or(a, c))

        # если обе части - конъюнкции: (A ∧ B) ∨ (C ∧ D) ≡ (A ∨ C) ∧ (A ∨ D) ∧ (B ∨ C) ∧ (B ∨ D)
        elif (left and left.value == '∧') and (right and right.value == '∧'):
            a = left.left
            b = left.right
            c = right.left
            d = right.right
            return Node('∧', Node('∧',self.distribute_or(a, c),self.distribute_or(a, d)),
                        Node('∧', self.distribute_or(b, c),self.distribute_or(b, d)))

        else:
            # в поддеревьях нет конъюнкции
            return Node('∨', left, right)


    def take_out_quanters(self, node: Node):
        # выносим кванторы вперед
        if node is None:
            return None
        # если в узле квантор
        if '∀' in node.value or '∃' in node.value:
            quantifier = node.value
            subtree = self.take_out_quanters(node.left)
            return Node(quantifier, subtree, None)
        # если операция '∧', '∨'
        elif node.value in ['∧', '∨']:
            left_subtree = self.take_out_quanters(node.left)
            right_subtree = self.take_out_quanters(node.right)

            # собираем кванторы из обеих частей
            left_quants, left_matrix = self.collect_all_quantifiers(left_subtree)
            right_quants, right_matrix = self.collect_all_quantifiers(right_subtree)

            # создаем тело без кванторов
            new_matrix = Node(node.value, left_matrix, right_matrix)

            # объединяем с сохранением зависимостей
            all_quants = self.merge_quantifiers(left_quants, right_quants)

            # добавляем перед матрицей все кванторы
            result = new_matrix
            for quant in reversed(all_quants):
                result = Node(quant, result, None)

            return result

        else:
            left_processed = self.take_out_quanters(node.left)
            right_processed = self.take_out_quanters(node.right)
            return Node(node.value, left_processed, right_processed)

    def merge_quantifiers(self, left_quants, right_quants):
        # сохраняем исходные последовательности кванторов из каждой части
        # оОбъединяем их по принципу: независимые блоки ∃ сначала, затем остальные

        # находим префиксы независимых ∃ кванторов в каждой части
        left_indep_prefix = self.get_independent_prefix(left_quants)
        right_indep_prefix = self.get_independent_prefix(right_quants)

        # находим оставшиеся кванторы (с зависимостями)
        left_dependent = left_quants[len(left_indep_prefix):]
        right_dependent = right_quants[len(right_indep_prefix):]

        # объединяем: независимые ∃ из обеих частей сначала
        merged = left_indep_prefix + right_indep_prefix

        # затем добавляем зависимые части, сохраняя их внутренний порядок
        merged.extend(left_dependent)
        merged.extend(right_dependent)

        return merged

    def get_independent_prefix(self, quantifiers):
        # находим префиксы независимых ∃ кванторов
        independent = []
        for quant in quantifiers:
            if quant.startswith('∃'):
                independent.append(quant)
            else:
                # встретили ∀ - это конец независимого префикса
                break
        return independent

    def collect_all_quantifiers(self, node):
        # собираем все кванторы
        quantifiers = []
        current = node

        while current is not None and ('∀' in current.value or '∃' in current.value):
            quantifiers.append(current.value)
            current = current.left

        return quantifiers, current

    def build_prenex_form(self, node: Node):
        # главный метод - запуск всех этапов
        # исключаем импликации и эквиваленции
        formula = self.replacement_impl_equiv(node)
        # проталкивание отрицания к атомарным формулам
        formula = self.push_negation_to_atoms(formula)
        # переименование связанных переменных
        formula = self.rename_related_vars(formula)
        # выносим все кванторы вперед
        formula = self.take_out_quanters(formula)
        # матрицу приводи к КНФ
        formula = self.to_CNF(formula)
        self.used_names.clear()
        return formula