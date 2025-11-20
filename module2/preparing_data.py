def collect_clauses(node):
    if node is None:
        return []

    if node.value == '∧':
        left_clauses = collect_clauses(node.left)
        right_clauses = collect_clauses(node.right)
        return left_clauses + right_clauses

    if node.value == '∨':
        left_literals = collect_clauses(node.left)
        right_literals = collect_clauses(node.right)
        return [left_literals[0] + right_literals[0]] if left_literals and right_literals else []

    if node.value == '¬':
        predicate = collect_clauses(node.left)
        if predicate and isinstance(predicate[0], list):
            for pred in predicate[0]:
                pred.set_negation_flag(True)
            return predicate
        elif predicate:
            predicate[0].set_negation_flag(True)
            return predicate
        return []

    if node.value.startswith('∀') or node.value.startswith('∃'):
        return collect_clauses(node.left)

    return [[node.object]]


def convert_tree_to_list(formula):
    disjuncts = collect_clauses(formula)
    print("Disjuncts:")
    for i, clause in enumerate(disjuncts):
        print(f"Clause {i}: {[str(pred) for pred in clause]}, {[pred.negation_flag for pred in clause]}")
    return disjuncts


