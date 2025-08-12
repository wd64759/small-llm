from dotenv import load_dotenv
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_openai import ChatOpenAI
import os

from langgraph.graph import StateGraph, END, START

from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, ToolMessage
from operator import add as add_messages
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.tools import tool

load_dotenv()

llm = ChatOpenAI(
    **{'model': "qwen-plus",
     'api_key': os.getenv("DASHSCOPE_API_KEY"),
     'base_url': os.getenv("DASHSCOPE_API_URL"),
     'temperature': 0,
     "extra_body": {
         'enable_thinking': False
     }}
)

embeddings = DashScopeEmbeddings(model="text-embedding-v3", dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"))

pdf_path = "/Users/dongwei/Desktop/方舟项目/pdd财报.pdf"
if not os.path.isfile(pdf_path):
    raise FileNotFoundError("pdd.pdf not found")

pdf_loader = PyPDFLoader(pdf_path)
try:
    pages = pdf_loader.load()
    print(f"Loaded pages with {len(pages)} pages")
except FileNotFoundError as e:
    print(f"Error loading PDF: {pdf_path}, {e}")
    raise

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)

pages_split = text_splitter.split_documents(pages)
collection_name = "financial_papers"

vector_store = Chroma.from_documents(
        persist_directory="chroma_db",
        collection_name=collection_name,
        embedding=embeddings,
        documents=pages_split
)
retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 5})

@tool
def retriever_tool(query: str) -> str:
    """this tool searches and returns the information from the internal documents"""
    docs = retriever.invoke(query)

    if not docs:
        return "I found no relevant information in internal doc"

    results = []
    for i, doc in enumerate(docs):
        results.append(f"Document {i+1}: \n{doc}")
    return "\n\n".join(results)

tools = [retriever_tool]
llm = llm.bind_tools(tools)

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

def should_continue(state: AgentState) -> bool:
    """checks if the agent should continue"""
    result = state["messages"][-1]
    return hasattr(result, 'tool_calls') and len(result.tool_calls) > 0

system_prompt="""
你是一个文本查询助手，利用文本检索工具返回的信息回答用户问题。所有的回答必须严格依据工具返回的内容，回答需要标注文档引用位置和关键原文的内容。
"""
tools_dict = {tool.name: tool for tool in tools}

def call_llm(state: AgentState) -> AgentState:
    """function to call llm"""
    messages = list(state["messages"])
    messages = [system_prompt] + messages
    messages = llm.invoke(messages)
    return {"messages": [messages]}

def take_action(state: AgentState) -> AgentState:
    """function to take action"""
    tool_calls = state["messages"][-1].tool_calls
    results = []
    for t in tool_calls:
        print(f"calling: {t['name']} with query: {t['args'].get('query', 'no query')}")

        if not t['name'] in tools_dict:
            print(f"no tool called {t['name']}")
            result = "Incorrect tool called"
        else:
            print(f"tool called {t['name']} >> {t['args']})")
            result = tools_dict[t['name']].invoke(t['args'].get('query',''))
            print(f"result length: {len(str(result))}")
            # print(f"tool result: {result}")
        results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))
    return {"messages": results}

graph = StateGraph(AgentState)
graph.add_node('llm', call_llm)
graph.add_node('retriever_agent', take_action)

graph.add_conditional_edges("llm", should_continue, {
    True: "retriever_agent",
    False: END
})

graph.add_edge('retriever_agent', 'llm')
graph.add_edge(START, "llm")

rag_agent = graph.compile()

def running():
    while True:
        user_input = input("> ")
        if user_input == "exit":
            break

        inputs = [HumanMessage(content=user_input)]
        result = rag_agent.invoke({"messages": inputs})
        print("\n====ANSWER====")
        print(result['messages'][-1].content)

if __name__ == "__main__":
    running()