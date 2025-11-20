from module2.base_object import Functor, Var
from module2.unification import unify_predicates, apply_substitution_to_predicate, args_equal
from module2.preparing_data import convert_tree_to_list

def resolution(tree_formulas):
    disjuncts = []
    for i in range(len(tree_formulas)):
        if i == len(tree_formulas) - 1:
            disjuncts = convert_tree_to_list(tree_formulas[i]) + disjuncts
            break
        disjuncts += convert_tree_to_list(tree_formulas[i])
    return resolution_method(disjuncts)

# метод резолюций
def resolution_method(disjuncts, max_iterations=1000):
    with open('../log.txt', 'w', encoding='utf-8') as file:
        file.write("Начало метода резолюций\n")

    #  все отсортированные дизъюнкты
    all_clauses = [sorted(clause.copy(), key=str) for clause in disjuncts]
    all_clauses_set = set()
    for clause in all_clauses:
        all_clauses_set.add(normalize_clause_key(clause))

    used_pairs = set()
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        new_clauses = []
        new_clauses_set = set()

        # сортировка сначала по длине, затем по строковому представлению
        all_clauses.sort(key=lambda c: (len(c), str([str(pred) for pred in c])))

        # построение индекса предикатов для текущей итерации
        predicate_index = build_predicate_index(all_clauses)

        # перебор всех пар дизъюнктов
        for i in range(len(all_clauses)):
            clause1 = all_clauses[i]

            # поиск потенциально контрарных дизъюнктов через индекс
            candidate_indices = find_contradictory_candidates(clause1, predicate_index, all_clauses)

            # сортировка кандидатов
            for j in sorted(candidate_indices):
                if i >= j or j >= len(all_clauses):
                    continue

                clause2 = all_clauses[j]

                # создание ключа для пары на основе нормализованных представлений
                key1 = normalize_clause_key(clause1)
                key2 = normalize_clause_key(clause2)
                pair_key = (min(key1, key2), max(key1, key2))

                if pair_key in used_pairs:
                    continue

                used_pairs.add(pair_key)

                # поиск контрарных литералов и выполнение резолюции
                resolvents = try_resolution(clause1, clause2)

                # сортировка резольвент
                resolvents.sort(key=lambda r: normalize_clause_key(r))

                for resolvent in resolvents:
                    if len(resolvent) == 0:
                        with open('../log.txt', 'a', encoding='utf-8') as file:
                            file.write("Найден пустой дизъюнкт. Доказательство завершено!\n")
                        return True, all_clauses + new_clauses

                    # проверка резольвенты на тавтологию
                    if not is_tautology(resolvent):
                        # проверка на повтор имеющейся резольвенты
                        resolvent_key = normalize_clause_key(resolvent)
                        if resolvent_key not in all_clauses_set and resolvent_key not in new_clauses_set:
                            # сортировка резольвенты перед добавлением
                            sorted_resolvent = sorted(resolvent, key=str)
                            new_clauses.append(sorted_resolvent)
                            new_clauses_set.add(resolvent_key)
                            with open('../log.txt', 'a', encoding='utf-8') as file:
                                file.write(f"Добавлена новая резольвента: {[str(pred) for pred in sorted_resolvent]}\n")

        # сортировка новых резольвент перед добавлением к общему списку
        new_clauses.sort(key=lambda c: normalize_clause_key(c))

        if not new_clauses:
            with open('../log.txt', 'a', encoding='utf-8') as file:
                file.write("Новых резольвент не найдено. Выводимость отсутствует\n")
            return False, all_clauses

        # добавление новых резольвент к общему списку
        all_clauses.extend(new_clauses)
        all_clauses_set.update(new_clauses_set)

    with open('../log.txt', 'a', encoding='utf-8') as file:
        file.write(f"Достигнут предел итераций ({max_iterations}). Доказательство не завершено\n")
    return False, all_clauses


# построение индекса предикатов для быстрого поиска контрарных пар
def build_predicate_index(clauses):
    index = {}
    for i, clause in enumerate(clauses):
        for pred in clause:
            key = (pred.name, pred.negation_flag)
            if key not in index:
                index[key] = set()
            index[key].add(i)

    # преобразование множеств в отсортированные списки
    for key in index:
        index[key] = sorted(index[key])

    return index


# поиск потенциально контрарных дизъюнктов через индекс
def find_contradictory_candidates(clause, index, all_clauses):
    candidates = set()
    for pred in clause:
        # поиск дизъюнктов, содержащих контрарные предикаты
        contradictory_key = (pred.name, not pred.negation_flag)
        if contradictory_key in index:
            # фильтруем индексы вхождений контрарного предиката так, чтобы они не выходили за границы списка
            valid_indices = {idx for idx in index[contradictory_key] if idx < len(all_clauses)}
            candidates.update(valid_indices)

    return sorted(candidates)


# нормализация дизъюнкта для сравнения (переименование переменных)
def normalize_clause_key(clause):
    variable_map = {}
    next_var_id = 1     # счетчик для генерации новых имен переменных

    # заменяет имена переменных в термах на vi
    def normalize_term(term):
        nonlocal next_var_id
        if isinstance(term, Var):
            if term.name not in variable_map:
                variable_map[term.name] = f"v{next_var_id}"
                next_var_id += 1
            return f"Var({variable_map[term.name]})"
        elif isinstance(term, Functor):
            args_str = ", ".join(normalize_term(arg) for arg in term.args)
            return f"Functor({term.name}, [{args_str}])"
        return str(term)

    # нормализует все аргументы предиката
    def normalize_predicate(pred):
        args_str = ", ".join(normalize_term(arg) for arg in pred.args)
        negation = "¬" if pred.negation_flag else ""
        return f"{negation}{pred.name}[{args_str}]"

    # сортировка предикатов
    sorted_predicates = sorted([normalize_predicate(pred) for pred in clause])
    return tuple(sorted_predicates)


# выполнение резолюции между двумя дизъюнктами (возвращает список резольвент)
def try_resolution(clause1, clause2):
    resolvents = []

    for i, pred1 in enumerate(clause1):
        for j, pred2 in enumerate(clause2):

            # поиск контрарных литералов
            if is_contradictory(pred1, pred2):
                '''with open('log.txt', 'a', encoding='utf-8') as file:
                                    file.write(f"Проверка пары дизъюнктов:\n")
                                    file.write(f"   Дизъюнкт {i}: {[str(pred) for pred in clause1]}\n")
                                    file.write(f"   Дизъюнкт {j}: {[str(pred) for pred in clause2]}\n")'''

                with open('../log.txt', 'a', encoding='utf-8') as file:
                    file.write(f"Найдены контрарные литералы: {str(pred1)} и {str(pred2)}\n")

                # попытка унификации
                substitution = unify_predicates(pred1, pred2)

                if substitution is not None:

                    # создание резольвенты
                    resolvent = create_resolvent(clause1, clause2, i, j, substitution)
                    resolvents.append(resolvent)

    return resolvents


# проверка предикатов на контрарность
def is_contradictory(pred1, pred2):
    return (pred1.name == pred2.name and
            pred1.negation_flag != pred2.negation_flag)


# создание резольвенты
def create_resolvent(clause1, clause2, idx1, idx2, substitution):
    resolvent_literals = []

    # добавление литералов из первого дизъюнкта (кроме участника пары контрарных)
    for i, pred in enumerate(clause1):
        if i != idx1:
            new_pred = apply_substitution_to_predicate(pred, substitution)
            resolvent_literals.append(new_pred)

    # добавление литералов из второго дизъюнкта (кроме участника пары контрарных)
    for j, pred in enumerate(clause2):
        if j != idx2:
            new_pred = apply_substitution_to_predicate(pred, substitution)
            resolvent_literals.append(new_pred)

    # удаление дубликатов
    unique_resolvent = remove_duplicates(resolvent_literals)

    return unique_resolvent


# удаление дубликатов предикатов из дизъюнкта
def remove_duplicates(clause):
    unique = []
    for pred in clause:
        if not any(predicates_equal(pred, existing) for existing in unique):
            unique.append(pred)
    return unique


# проверка дизъюнкта на тавтологию
def is_tautology(clause):
    for i in range(len(clause)):
        for j in range(i + 1, len(clause)):
            if (clause[i].name == clause[j].name and
                clause[i].negation_flag != clause[j].negation_flag and
                args_equal(clause[i].args, clause[j].args)):
                return True
    return False


# проверка дизъюнкта на наличие в списке дизъюнктов
def contains_clause(clauses_list, clause):
    for existing_clause in clauses_list:
        if clauses_equal(existing_clause, clause):
            return True
    return False


# проверка двух дизъюнктов на эквивалентность
def clauses_equal(clause1, clause2):
    if len(clause1) != len(clause2):
        return False

    # проверка наличия каждого предиката из clause1 в clause2
    for pred1 in clause1:
        found = False
        for pred2 in clause2:
            if predicates_equal(pred1, pred2):
                found = True
                break
        if not found:
            return False
    return True


# проверка предикатов на эквивалентность
def predicates_equal(pred1, pred2):
    return (pred1.name == pred2.name and
            pred1.negation_flag == pred2.negation_flag and
            args_equal(pred1.args, pred2.args))

