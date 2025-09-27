class BaseAgent:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.tools = []

    def run(self, query: str):
        raise NotImplementedError("Subclasses must implement this method")

    def get_context(self, query: str, extra_params: dict = {}):
        # TODO: get context from long conversation history
        return query