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
