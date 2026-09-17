class BaseProvider:
    def call(self, prompt: str):
        raise NotImplementedError