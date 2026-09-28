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
