import json

class ToolCall:
    def __init__(self, name, index, arguments, result, timecost):
        self.name = name
        self.index = index
        self.arguments = arguments
        self.result = result
        self.timecost = timecost

    def to_dict(self):
        return {
            "name": self.name,
            "index": self.index,
            "arguments": self.arguments,
            "result": self.result,
            "timecost": self.timecost
        }

class LLMCall:
    def __init__(self, session_id):
        self.session_id = session_id
        self.tool_calls = []

    def complete(self, query, response, timecost, token_usage):
        self.query = query
        self.response = str(response)
        self.timecost = timecost
        self.token_usage = token_usage

    def add_tool_call(self, tool_call):
        self.tool_calls.append(tool_call)

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "query": self.query,
            "response": self.response,
            "timecost": self.timecost,
            "token_usage": self.token_usage,
            "tool_calls": [tool_call.to_dict() for tool_call in self.tool_calls]
        }

class ChatReport:
    def __init__(self):
        self.llm_calls = []
        self.total_tokens = 0

    def start_llm_call(self, session_id)->LLMCall:
        llm_call = LLMCall(session_id)
        self.llm_calls.append(llm_call)
        return llm_call

    def to_dict(self):
        return {
            "llm_calls": [llm_call.to_dict() for llm_call in self.llm_calls]
        }

    def save(self, file_path):
        with open(file_path, "w") as f:
            json.dump(self.to_dict(), f, indent=4)