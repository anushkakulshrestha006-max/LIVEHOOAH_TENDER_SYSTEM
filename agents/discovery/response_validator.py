class ResponseValidator:

    @staticmethod
    def validate(result):

        if not isinstance(result, dict):
            return False

        if "opportunities" not in result:
            return False

        if not isinstance(result["opportunities"], list):
            return False

        return True