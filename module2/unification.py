from module2.base_object import Var, Functor, Predicate

# унификация двух предикатов (возвращает словарь с подстановкой, либо None)
def unify_predicates(predicate1, predicate2):
    if predicate1.name != predicate2.name:
        return None

    with open('../log.txt', 'a', encoding='utf-8') as file:
        file.write(f"Унифицируем предикаты {str(predicate1)} и {str(predicate2)}\n")

    # множество списков аргументов
    S = [predicate1.args, predicate2.args]

    k = 0
    S_k = S
    delta_k = {}    # пустая подстановка

    while not all_identical(S_k):
        # нахождение множества рассогласований
        E_k = find_disagreement_set(S_k)

        # поиск переменной и терма для подстановки
        found = False
        for elem1 in E_k:
            for elem2 in E_k:
                if elem1 != elem2 and isinstance(elem1, Var) and \
                    not elem1.is_constant() and not occurs_check(elem1, elem2):
                    # нашли пару для подстановки
                    x_i = elem1
                    t_j = elem2
                    with open('../log.txt', 'a', encoding='utf-8') as file:
                        file.write(f"Осуществляем подстановку: {x_i} -> {t_j}.\n")

                    # создание новой подстановки
                    delta_k_plus_1 = compose_substitutions({x_i: t_j}, delta_k)

                    # применяем новую подстановку ко всему множеству
                    S_k_plus_1 = [apply_substitution_to_list(args, delta_k_plus_1) for args in S_k]

                    k += 1
                    S_k = S_k_plus_1
                    delta_k = delta_k_plus_1
                    found = True
                    break
            if found:
                break

        if not found:
            constants = [elem for elem in E_k if isinstance(elem, Var) and elem.is_constant()]
            if len(constants) >= 2:
                # найдены разные константы => унификация невозможна
                with open('../log.txt', 'a', encoding='utf-8') as file:
                    file.write("Обнаружены разные константы, унификация невозможна\n")
                return None
            with open('../log.txt', 'a', encoding='utf-8') as file:
                file.write("Унификация невозможна\n")
            return None
    pr1_unified = apply_substitution_to_predicate(predicate1, delta_k)
    pr2_unified = apply_substitution_to_predicate(predicate2, delta_k)
    with open('../log.txt', 'a', encoding='utf-8') as file:
        file.write(f"Результат унификации: {pr1_unified} и {pr2_unified}\n")
    return delta_k


# проверка равенства всех элементов в S
def all_identical(S):
    if not S:
        return True
    first = S[0]
    return all(args_equal(first, other) for other in S[1:])


# проверка равенства двух списков аргументов
def args_equal(args1, args2):
    if len(args1) != len(args2):
        return False
    for a1, a2 in zip(args1, args2):
        if not terms_equal(a1, a2):
            return False
    return True


# проверка равенства двух термов
def terms_equal(term1, term2):
    return  term1 == term2


# нахождение множества рассогласований
def find_disagreement_set(S):
    if not S or len(S) < 2:
        return set()

    # первая позиция с рассогласованием
    max_len = min(len(args) for args in S)

    for i in range(max_len):
        # термы на позиции i из всех списков
        terms_at_pos = [args[i] for args in S]

        if not all_terms_equal(terms_at_pos):
            # все различные термы на данной позиции
            return set(terms_at_pos)
    return set()


# проверка всех термов на равенство
def all_terms_equal(terms):
    if not terms:
        return True
    first = terms[0]
    for i in range(1, len(terms)):
        if not terms_equal(first, terms[i]):
            return False
    return True


# проверка наличия переменной var в терме term
def occurs_check(var, term):
    if isinstance(term, Var):
        return var.name == term.name
    elif isinstance(term, Functor):
        return any(occurs_check(var, arg) for arg in term.args)
    return False


# композиция подстановок new_sub ∘ old_sub
def compose_substitutions(new_sub, old_sub):
    result = old_sub.copy()

    # применение старой подстановки к новой (key - старое значение, value - новое)
    for key, value in new_sub.items():
        result[key] = apply_substitution(value, old_sub)

    # удаление циклических подстановок (x на x)
    result = {k: v for k, v in result.items() if not (isinstance(k, Var) and isinstance(v, Var) and k.name == v.name)}
    return result


# применение подстановки к терму
def apply_substitution(term, substitution):
    if isinstance(term, Var):
        # если переменная есть в подстановке, возвращаем ее значение (то, на что её заменяем)
        for var, value in substitution.items():
            if var.name == term.name:
                return apply_substitution(value, substitution)
        return term
    elif isinstance(term, Functor):
        # для функтора рекурсивно применяем подстановку к аргументам
        new_args = [apply_substitution(arg, substitution) for arg in term.args]
        return Functor(term.name, new_args)
    return term


# применение подстановки к списку термов
def apply_substitution_to_list(term_list, substitution):
    return [apply_substitution(term, substitution) for term in term_list]


# применение подстановки к предикату
def apply_substitution_to_predicate(predicate, substitution):
    new_args = []
    for arg in predicate.args:
        new_arg = apply_substitution(arg, substitution)
        new_args.append(new_arg)

    new_predicate = Predicate(predicate.name, new_args)
    new_predicate.negation_flag = predicate.negation_flag
    return new_predicate


