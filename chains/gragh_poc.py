from langgraph.graph import StateGraph, END
from typing import Annotated, TypedDict

# 定义State
class AgentState(TypedDict):
    query: str
    rewritten_query: str
    rag_result: str
    market_result: str
    product_result: str
    position_result: str
    general_result: str
    domain_planner: str
    analysis_planner: str
    final_output: str

# 定义各节点函数（后续可替换为具体的LangChain Tool或AgentExecutor）
def context_rewriter(state: AgentState) -> AgentState:
    state["rewritten_query"] = f"[重写]{state['query']}"
    return state

def rag_enhancer(state: AgentState) -> AgentState:
    state["rag_result"] = f"[RAG增强]{state['rewritten_query']}"
    return state

def domain_planner(state: AgentState) -> AgentState:
    # 示例策略：简单关键词路由
    query = state["query"]
    if "市场" in query:
        state["domain_planner"] = "market"
    elif "产品" in query:
        state["domain_planner"] = "product"
    elif "持仓" in query:
        state["domain_planner"] = "position"
    elif "通识" in query:
        state["domain_planner"] = "general"
    else:
        state["domain_planner"] = "general"  # 默认路由到通识
    return state

# --- 各领域处理器 ---
def market_aggregator(state: AgentState) -> AgentState:
    state["market_result"] = "[市场分析完成]"
    return state

def product_aggregator(state: AgentState) -> AgentState:
    state["product_result"] = "[产品分析完成]"
    return state

def position_aggregator(state: AgentState) -> AgentState:
    state["position_result"] = "[持仓分析完成]"
    return state

def general_aggregator(state: AgentState) -> AgentState:
    state["general_result"] = "[金融通识完成]"
    return state

# --- 聚合后规划 ---
def analysis_planner(state: AgentState) -> AgentState:
    # 仅选择一个review路径
    if state.get("market_result"):
        state["analysis_planner"] = "im"
    elif state.get("product_result"):
        state["analysis_planner"] = "advisor"
    else:
        state["analysis_planner"] = "service"
    return state

def investment_manager_reviewer(state: AgentState) -> AgentState:
    state["final_output"] = f"[投资经理解读]{state['market_result']}"
    return state

def advisor_reviewer(state: AgentState) -> AgentState:
    state["final_output"] = f"[投研顾问解读]{state['product_result']}"
    return state

def service_reviewer(state: AgentState) -> AgentState:
    state["final_output"] = f"[客服解读]{state['position_result'] or state['general_result']}"
    return state

# --- 构建LangGraph ---
graph = StateGraph(AgentState)

# 基础流程
graph.add_node("rewriter", context_rewriter)
graph.add_node("rag", rag_enhancer)
graph.add_node("domain_planner", domain_planner)

# 多分支节点
graph.add_node("market", market_aggregator)
graph.add_node("product", product_aggregator)
graph.add_node("position", position_aggregator)
graph.add_node("general", general_aggregator)

# 汇总分析
graph.add_node("analysis_planner", analysis_planner)
graph.add_node("im", investment_manager_reviewer)
graph.add_node("advisor", advisor_reviewer)
graph.add_node("service", service_reviewer)

graph.set_entry_point("rewriter")
graph.add_edge("rewriter", "rag")
graph.add_edge("rag", "domain_planner")

# 并行领域执行（使用router）
graph.add_conditional_edges(
    "domain_planner",
    lambda x: x["domain_planner"],
    {
        "market": "market",
        "product": "product",
        "position": "position",
        "general": "general",
    }
)

# 汇总至分析规划器
graph.add_edge("market", "analysis_planner")
graph.add_edge("product", "analysis_planner")
graph.add_edge("position", "analysis_planner")
graph.add_edge("general", "analysis_planner")

# analysis_planner 选择路径
graph.add_conditional_edges(
    "analysis_planner",
    lambda x: x["analysis_planner"],
    {
        "im": "im",
        "advisor": "advisor",
        "service": "service",
    }
)

graph.add_edge("im", END)
graph.add_edge("advisor", END)
graph.add_edge("service", END)

# 构建可执行图
tool_graph = graph.compile()

if __name__ == "__main__":
    result = tool_graph.invoke({"query": "请分析当前市场和我持仓的产品风险"})
    print("\n最终输出:", result["final_output"])
