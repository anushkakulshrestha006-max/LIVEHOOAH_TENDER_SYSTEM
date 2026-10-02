from core.services.search_budget import SearchBudget


def test_search_budget_enforces_serp_limit():
    budget = SearchBudget(
        serp_limit=2
    )

    assert budget.serp_used == 0
    assert budget.serp_remaining == 2
    assert budget.can_use_serp() is True

    assert budget.consume_serp() is True

    assert budget.serp_used == 1
    assert budget.serp_remaining == 1
    assert budget.can_use_serp() is True

    assert budget.consume_serp() is True

    assert budget.serp_used == 2
    assert budget.serp_remaining == 0
    assert budget.can_use_serp() is False

    assert budget.consume_serp() is False

    assert budget.serp_used == 2
    assert budget.serp_remaining == 0


def test_search_budget_can_disable_serp_for_remainder_of_run():
    budget = SearchBudget(
        serp_limit=5
    )

    assert budget.consume_serp() is True
    assert budget.serp_used == 1

    budget.disable_serp()

    assert budget.can_use_serp() is False
    assert budget.consume_serp() is False

    assert budget.serp_used == 1
    assert budget.serp_remaining == 4


def test_zero_serp_limit_disables_serp_without_consumption():
    budget = SearchBudget(
        serp_limit=0
    )

    assert budget.can_use_serp() is False
    assert budget.consume_serp() is False
    assert budget.serp_used == 0
    assert budget.serp_remaining == 0

def test_scoped_search_budget_propagates_disable_to_parent():
    from core.services.search_budget import ScopedSearchBudget

    parent = SearchBudget(
        serp_limit=5
    )
    scope = ScopedSearchBudget(
        parent=parent,
        serp_limit=1,
    )

    assert scope.consume_serp() is True
    assert parent.serp_used == 1

    scope.disable_serp()

    assert parent.can_use_serp() is False
    assert parent.consume_serp() is False
    assert parent.serp_used == 1

def test_scoped_search_budget_enforces_local_limit_against_parent():
    from core.services.search_budget import ScopedSearchBudget

    parent = SearchBudget(
        serp_limit=5
    )
    scope = ScopedSearchBudget(
        parent=parent,
        serp_limit=1,
    )

    assert scope.can_use_serp() is True
    assert scope.consume_serp() is True

    assert scope.serp_used == 1
    assert scope.serp_remaining == 0
    assert scope.can_use_serp() is False
    assert scope.consume_serp() is False

    # Only the successful scoped request reaches the parent.
    assert parent.serp_used == 1
    assert parent.serp_remaining == 4
    assert parent.can_use_serp() is True
