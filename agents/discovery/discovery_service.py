class TenderDiscoveryService:

    def __init__(self, executor):
        self.executor = executor

    def discover(self, query: str):
        """
        Execute tender discovery for a single query.

        Responsibilities
        ----------------
        - Execute the configured discovery executor.
        - Validate the executor response.
        - Return raw discovered opportunities.

        NOT responsible for
        -------------------
        - LiveHooah relevance scoring
        - Qualification
        - Ranking
        - Tender extraction
        - Deduplication
        - Google Sheets persistence

        Those responsibilities belong to the downstream pipeline.
        """

        result = self.executor.execute(query)

        if not result:
            return {
                "status": "invalid_response",
                "opportunities": [],
            }

        opportunities = result.get(
            "opportunities",
            [],
        )

        if not isinstance(opportunities, list):
            return {
                "status": "invalid_response",
                "opportunities": [],
            }

        return {
            **result,
            "opportunities": opportunities,
        }