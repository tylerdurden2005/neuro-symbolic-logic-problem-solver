from pydoc import replace

from module2.base_object import Var, Functor, Predicate, Node
class Prenexer:
    def __init__(self):
        self.used_names = set()
    def replacement_impl_equiv(self, node: Node):
        # Убираем импликации и эквиваленции в формуле
        if node is None:
            return None

        new_left = self.replacement_impl_equiv(node.left)
        new_right = self.replacement_impl_equiv(node.right)
        # Заменяем операторы
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
            # Для всех других операторов возвращаем узел с обработанными потомками
            return Node(node.value, new_left, new_right)

    def push_negation_to_atoms(self, node):
        # Проталкивание отрицания к атомарным формулам
        if node is None:
            return None
        # Если это отрицание
        if node.value == '¬':
            child = node.left
            # Двойное отрицание: ¬¬A ≡ A
            if child.value == '¬':
                return self.push_negation_to_atoms(child.left)

            # Закон де Моргана: ¬(A ∧ B) ≡ ¬A ∨ ¬B
            elif child.value == '∧':
                left_neg = Node('¬', child.left)
                right_neg = Node('¬', child.right)
                new_left = self.push_negation_to_atoms(left_neg)
                new_right = self.push_negation_to_atoms(right_neg)
                return Node('∨', new_left, new_right)

            # Закон де Моргана: ¬(A ∨ B) ≡ ¬A ∧ ¬B
            elif child.value == '∨':
                left_neg = Node('¬', child.left)
                right_neg = Node('¬', child.right)
                new_left = self.push_negation_to_atoms(left_neg)
                new_right = self.push_negation_to_atoms(right_neg)
                return Node('∧', new_left, new_right)

            # Для кванторов: ¬∀x P(x) ≡ ∃x ¬P(x)
            elif '∀' in child.value:
                new_quant = child.value.replace('∀', '∃')
                new_body = Node('¬', child.left)
                return Node(new_quant, self.push_negation_to_atoms(new_body))

            # Для кванторов: ¬∃x P(x) ≡ ∀x ¬P(x)
            elif '∃' in child.value:
                new_quant = child.value.replace('∃', '∀')
                new_body = Node('¬', child.left)
                return Node(new_quant, self.push_negation_to_atoms(new_body))
            else:
                # Предикаты
                return node

        # Обрабатываем кванторы, как встреченные узлы
        elif '∀' in node.value or '∃' in node.value:
            new_body = self.push_negation_to_atoms(node.left)
            return Node(node.value, new_body)

        # Обрабатываем бинарные операторы, как встреченные узлы
        elif node.value in ['∧', '∨']:
            new_left = self.push_negation_to_atoms(node.left)
            new_right = self.push_negation_to_atoms(node.right)
            return Node(node.value, new_left, new_right)
        else:
            # Предикаты
            return node

    def generate_unique_name(self):
        # Генератор имени переменной
        base_chars = "xyzwtuv"
        for char in base_chars:
            if char not in self.used_names:
                return char
        # Если все одиночные символы заняты, добавляем индексы
        counter = 1
        while True:
            for char in base_chars:
                candidate = f"{char}{counter}"
                if candidate not in self.used_names:
                    return candidate
            counter += 1

    def rename_related_vars(self, node: Node):
        # Переименование связанных переменных
        if node is None:
            return None

        # Если узел - квантор
        if '∀' in node.value or '∃' in node.value:
            quantifier_char = node.value[0]
            var_name = node.value[1:]

            # Проверяем, использовалось ли уже это имя переменной в формуле
            if var_name in self.used_names:
                # Конфликт имен - генерируем новое имя
                new_name = self.generate_unique_name()
                # Заменяем имя переменной в кванторе
                node.value = quantifier_char + new_name
                self.used_names.add(new_name)
                # Заменяем все вхождения этой переменной в поддереве квантора
                if node.left:
                    node.left = self.replace_vars(node.left, var_name, new_name)
            else:
                # Имя не использовалось, добаляется в множество использоанных
                self.used_names.add(var_name)
            # Обрабатываем поддерево
            node.left = self.rename_related_vars(node.left)
        else:
            node.left = self.rename_related_vars(node.left)
            node.right = self.rename_related_vars(node.right)
        return node

    def replace_vars(self, node: Node, old, new):
        # Вспомогательная функция замены переменной в поддереве квантора
        if node is None:
            return None
        # Если встретили квантор с именем переменной, которую меняем
        if ('∀' in node.value or '∃' in node.value) and node.value[1:] == old:
            return node
        #
        if '∀' in node.value or '∃' in node.value:
            new_left = self.replace_vars(node.left, old, new)
            return Node(node.value, new_left, node.right)
        # Если узел - предикат
        if node.object is not None and isinstance(node.object, Predicate):
            new_args = []
            # Делаем замену в его термах
            for arg in node.object.args:
                new_arg = self.replace_var_in_term(arg, old, new)
                new_args.append(new_arg)
            predicate = Predicate(node.object.name, new_args)
            #new_left = self.replace_vars(node.left, old, new)
            #new_right = self.replace_vars(node.right, old, new)
            return Node(str(predicate))
        # Операции
        new_left = self.replace_vars(node.left, old, new)
        new_right = self.replace_vars(node.right, old, new)
        return Node(node.value, new_left, new_right)


    def replace_var_in_term(self, term, old, new):
        # Переименование термов
        if isinstance(term, Var):
            # Если это переменная, которую нужно заменить
            if term.name == old:
                # Замена на новое имя
                return Var(new)
            else:
                # Оставляем как есть
                return term
        elif isinstance(term, Functor):
            # Рекурсивно обрабатываем аргументы функтора
            new_args = []
            for arg in term.args:
                new_arg = self.replace_var_in_term(arg, old, new)
                new_args.append(new_arg)
            # Создаем новый функтор с обновленными аргументами
            return Functor(term.name, new_args)
        else:
            return term

    def to_CNF(self, node: Node):
        # Приводим матрицу к КНФ
        if node is None:
            return None

        # Рекурсивно преобразуем потомков
        left_cnf = self.to_CNF(node.left)
        right_cnf = self.to_CNF(node.right)

        # Обрабатываем операторы
        if node.value == '∧':
            # Просто возвращаем
            return Node('∧', left_cnf, right_cnf)

        elif node.value == '∨':
            # Применяем дистрибутивность
            return self.distribute_or(left_cnf, right_cnf)

        else:
            # Для всех других узлов (кванторы, предикаты, отрицания)
            return Node(node.value, left_cnf, right_cnf)

    def distribute_or(self, left, right):
        # Применяем дистрибутивность
        # Если левая часть - конъюнкция: (A ∧ B) ∨ C ≡ (A ∨ C) ∧ (B ∨ C)
        if left and left.value == '∧':
            a = left.left
            b = left.right
            c = right
            return Node('∧',self.distribute_or(a, c),self.distribute_or(b, c))

        # Если правая часть - конъюнкция: A ∨ (B ∧ C) ≡ (A ∨ B) ∧ (A ∨ C)
        elif right and right.value == '∧':
            a = left
            b = right.left
            c = right.right
            return Node('∧',
                        self.distribute_or(a, b),
                        self.distribute_or(a, c))

        # Если обе части - конъюнкции: (A ∧ B) ∨ (C ∧ D) ≡ (A ∨ C) ∧ (A ∨ D) ∧ (B ∨ C) ∧ (B ∨ D)
        elif (left and left.value == '∧') and (right and right.value == '∧'):
            a = left.left
            b = left.right
            c = right.left
            d = right.right
            return Node('∧', Node('∧',self.distribute_or(a, c),self.distribute_or(a, d)),
                        Node('∧', self.distribute_or(b, c),self.distribute_or(b, d)))

        else:
            # В поддеревьях нет конъюнкции
            return Node('∨', left, right)


    def take_out_quanters(self, node: Node):
        # Выносим кванторы вперед
        if node is None:
            return None
        # Если в узле квантор
        if '∀' in node.value or '∃' in node.value:
            quantifier = node.value
            subtree = self.take_out_quanters(node.left)
            return Node(quantifier, subtree, None)
        # Если операция '∧', '∨'
        elif node.value in ['∧', '∨']:
            left_subtree = self.take_out_quanters(node.left)
            right_subtree = self.take_out_quanters(node.right)

            # Собираем кванторы из обеих частей
            left_quants, left_matrix = self.collect_all_quantifiers(left_subtree)
            right_quants, right_matrix = self.collect_all_quantifiers(right_subtree)

            # Создаем тело без кванторов
            new_matrix = Node(node.value, left_matrix, right_matrix)

            # Объединяем с сохранением зависимостей
            all_quants = self.merge_quantifiers(left_quants, right_quants)

            # Добавляем перед матрицей все кванторы
            result = new_matrix
            for quant in reversed(all_quants):
                result = Node(quant, result, None)

            return result

        else:
            left_processed = self.take_out_quanters(node.left)
            right_processed = self.take_out_quanters(node.right)
            return Node(node.value, left_processed, right_processed)

    def merge_quantifiers(self, left_quants, right_quants):
        # Сохраняем исходные последовательности кванторов из каждой части
        # Объединяем их по принципу: независимые блоки ∃ сначала, затем остальные

        # Находим префиксы независимых ∃ кванторов в каждой части
        left_indep_prefix = self.get_independent_prefix(left_quants)
        right_indep_prefix = self.get_independent_prefix(right_quants)

        # Находим оставшиеся кванторы (с зависимостями)
        left_dependent = left_quants[len(left_indep_prefix):]
        right_dependent = right_quants[len(right_indep_prefix):]

        # Объединяем: независимые ∃ из обеих частей сначала
        merged = left_indep_prefix + right_indep_prefix

        # Затем добавляем зависимые части, сохраняя их внутренний порядок
        merged.extend(left_dependent)
        merged.extend(right_dependent)

        return merged

    def get_independent_prefix(self, quantifiers):
        # Находим префиксы независимых ∃ кванторов
        independent = []
        for quant in quantifiers:
            if quant.startswith('∃'):
                independent.append(quant)
            else:
                # встретили ∀ - это конец независимого префикса
                break
        return independent

    def collect_all_quantifiers(self, node):
        # Собираем все кванторы
        quantifiers = []
        current = node

        while current is not None and ('∀' in current.value or '∃' in current.value):
            quantifiers.append(current.value)
            current = current.left

        return quantifiers, current

    def build_prenex_form(self, node: Node):
        # Главный метод - запуск всех этапов
        # Исключаем импликации и эквиваленции
        formula = self.replacement_impl_equiv(node)
        # Проталкивание отрицания к атомарным формулам
        formula = self.push_negation_to_atoms(formula)
        # Переименование связанных переменных
        formula = self.rename_related_vars(formula)
        # Выносим все кванторы вперед
        formula = self.take_out_quanters(formula)
        # Матрицу приводи к КНФ
        formula = self.to_CNF(formula)
        self.used_names.clear()
        return formula