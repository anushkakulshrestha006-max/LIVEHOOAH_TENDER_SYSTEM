class SearchBudget:
    """
    Run-scoped budget for paid search backends.

    The budget contains no environment or global state.
    Its lifetime is controlled by the caller.
    """

    def __init__(self, serp_limit: int):
        if isinstance(serp_limit, bool):
            raise ValueError(
                "serp_limit must be a non-negative integer"
            )

        if not isinstance(serp_limit, int):
            raise ValueError(
                "serp_limit must be a non-negative integer"
            )

        if serp_limit < 0:
            raise ValueError(
                "serp_limit must be a non-negative integer"
            )

        self.serp_limit = serp_limit
        self.serp_used = 0
        self._serp_enabled = serp_limit > 0

    @property
    def serp_remaining(self):
        return max(
            self.serp_limit - self.serp_used,
            0,
        )

    def can_use_serp(self):
        return (
            self._serp_enabled
            and self.serp_used < self.serp_limit
        )

    def consume_serp(self):
        if not self.can_use_serp():
            return False

        self.serp_used += 1

        return True

    def disable_serp(self):
        self._serp_enabled = False


class ScopedSearchBudget:
    """
    Local SERP allowance backed by a shared run-scoped budget.

    Successful consumption counts against both this scope and
    the parent budget. Disabling SERP propagates to the parent
    so provider failures disable paid search for the whole run.
    """

    def __init__(
        self,
        parent,
        serp_limit: int,
    ):
        if isinstance(serp_limit, bool):
            raise ValueError(
                "serp_limit must be a non-negative integer"
            )

        if not isinstance(serp_limit, int):
            raise ValueError(
                "serp_limit must be a non-negative integer"
            )

        if serp_limit < 0:
            raise ValueError(
                "serp_limit must be a non-negative integer"
            )

        self.parent = parent
        self.serp_limit = serp_limit
        self.serp_used = 0

    @property
    def serp_remaining(self):
        return max(
            self.serp_limit - self.serp_used,
            0,
        )

    def can_use_serp(self):
        return (
            self.serp_used < self.serp_limit
            and self.parent.can_use_serp()
        )

    def consume_serp(self):
        if not self.can_use_serp():
            return False

        if not self.parent.consume_serp():
            return False

        self.serp_used += 1

        return True

    def disable_serp(self):
        self.parent.disable_serp()
