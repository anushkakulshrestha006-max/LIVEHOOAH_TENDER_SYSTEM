class QueryBuilder:

    @staticmethod
    def build(query: str) -> str:

        if any(
            kw in query.lower()
            for kw in [
                "structural",
                "warehouse",
                "high-rise",
                "residential",
                "logistics",
                "industrial"
            ]
        ):
            return query

        return f"structural engineering consultancy tender: {query}"