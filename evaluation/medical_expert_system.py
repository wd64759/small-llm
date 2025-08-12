"""
医疗专家系统 - LangGraph框架

本系统使用LangGraph构建医疗专家系统，包含以下组件：
- 意图识别Triage Agent Planner
- 内科专家Agent
- 外科专家Agent
- 急症科Agent
- 置信评估节点
- 综合诊断Agent
- Human-in-loop节点（置信度<70%时触发）
"""

import os
import json
from typing import Dict, List, Any, TypedDict, Annotated, Literal
from datetime import datetime
import logging

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

# LangChain imports
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv  

load_dotenv()

api_key = os.getenv('DASHSCOPE_API_KEY')
api_url = os.getenv('DASHSCOPE_API_URL')
default_model = os.getenv('DEFAULT_LLM_MODEL')
default_temperature = float(os.getenv('API_TEMPERATURE',0.1))

print(f"API Key: {api_key}")
print(f"API URL: {api_url}")
print(f"Model: {default_model}")
print(f"Temperature: {default_temperature}")

# 定义状态结构
class MedicalState(TypedDict):
    """医疗专家系统状态"""
    messages: Annotated[List, "对话消息历史"]
    user_input: Annotated[str, "用户输入"]
    intent: Annotated[Dict, "意图识别结果"]
    confidence: Annotated[float, "置信度"]
    triage_result: Annotated[Dict, "分诊结果"]
    internal_analysis: Annotated[Dict, "内科专家分析"]
    surgical_analysis: Annotated[Dict, "外科专家分析"]
    emergency_analysis: Annotated[Dict, "急症科分析"]
    confidence_assessment: Annotated[Dict, "置信评估结果"]
    final_diagnosis: Annotated[Dict, "综合诊断结果"]
    human_intervention: Annotated[bool, "是否需要人工干预"]
    human_feedback: Annotated[str, "人工反馈"]
    current_step: Annotated[str, "当前步骤"]

# 定义输出模型
class IntentResult(BaseModel):
    """意图识别结果"""
    intent: str = Field(description="识别出的意图")
    confidence: float = Field(description="置信度0-1")
    urgency_level: str = Field(description="紧急程度：low/medium/high/critical")
    departments: List[str] = Field(description="需要涉及的科室")
    reasoning: str = Field(description="推理过程")

class AnalysisResult(BaseModel):
    """专家分析结果"""
    department: str = Field(description="科室名称")
    analysis: str = Field(description="分析内容")
    confidence: float = Field(description="置信度0-1")
    recommendations: List[str] = Field(description="建议")
    risk_factors: List[str] = Field(description="风险因素")

class ConfidenceAssessment(BaseModel):
    """置信评估结果"""
    overall_confidence: float = Field(description="总体置信度")
    confidence_breakdown: Dict[str, float] = Field(description="各科室置信度")
    uncertainty_factors: List[str] = Field(description="不确定性因素")
    needs_human_review: bool = Field(description="是否需要人工审核")
    reasoning: str = Field(description="评估推理")

class FinalDiagnosis(BaseModel):
    """综合诊断结果"""
    primary_diagnosis: str = Field(description="主要诊断")
    differential_diagnoses: List[str] = Field(description="鉴别诊断")
    treatment_plan: List[str] = Field(description="治疗方案")
    urgency_level: str = Field(description="紧急程度")
    follow_up: str = Field(description="随访建议")
    confidence: float = Field(description="最终置信度")

def create_llm(model_name: str = default_model):
    """创建LLM实例"""
    return ChatOpenAI(
        model=model_name,
        temperature=default_temperature,
        api_key=api_key,
        base_url=api_url
    )

llm = create_llm()
parser = JsonOutputParser()

def create_triage_agent():
    """创建意图识别分诊Agent"""
    
    triage_prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="""
你是一个专业的医疗分诊专家。你的任务是分析患者的症状描述，识别医疗意图，确定紧急程度，并推荐需要涉及的科室。

请根据以下信息进行分析：
1. 症状描述和严重程度
2. 患者年龄、性别等基本信息
3. 症状持续时间
4. 相关病史
5. 紧急程度评估

输出格式要求：
- intent: 识别出的意图（如：胸痛、腹痛、发热、外伤等）
- confidence: 置信度（0-1之间）
- urgency_level: 紧急程度（low/medium/high/critical）
- departments: 需要涉及的科室列表
- reasoning: 推理过程
"""),
        MessagesPlaceholder(variable_name="messages"),
        HumanMessage(content="请分析以下患者症状：{user_input}")
    ])
    
    def triage_agent(state: MedicalState) -> MedicalState:
        """意图识别分诊Agent"""
        try:
            # 构建消息历史
            messages = state.get("messages", [])
            user_input = state["user_input"]
            
            # 执行意图识别
            chain = triage_prompt | llm | parser
            result = chain.invoke({
                "messages": messages,
                "user_input": user_input
            })
            
            # 更新状态
            state["intent"] = result
            state["confidence"] = result.get("confidence", 0.0)
            state["current_step"] = "triage_completed"
            
            logger.info(f"Triage completed: {result}")
            
        except Exception as e:
            logger.error(f"Error in triage agent: {e}")
            state["intent"] = {
                "intent": "unknown",
                "confidence": 0.0,
                "urgency_level": "medium",
                "departments": ["internal"],
                "reasoning": f"Error in triage: {str(e)}"
            }
            state["confidence"] = 0.0
        
        return state
    
    return triage_agent

def create_internal_agent():
    """创建内科专家Agent"""
    
    internal_prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="""
你是一个经验丰富的内科专家。你的任务是分析患者的症状，提供内科角度的诊断分析和建议。

请重点关注：
1. 内科疾病的诊断可能性
2. 需要进一步检查的项目
3. 药物治疗建议
4. 生活方式建议
5. 风险因素评估

输出格式要求：
- department: "internal"
- analysis: 详细分析内容
- confidence: 置信度（0-1之间）
- recommendations: 建议列表
- risk_factors: 风险因素列表
"""),
        MessagesPlaceholder(variable_name="messages"),
        HumanMessage(content="请从内科角度分析以下症状：{user_input}")
    ])
    
    def internal_agent(state: MedicalState) -> MedicalState:
        """内科专家Agent"""
        try:
            messages = state.get("messages", [])
            user_input = state["user_input"]
            
            chain = internal_prompt | llm | parser
            result = chain.invoke({
                "messages": messages,
                "user_input": user_input
            })
            
            state["internal_analysis"] = result
            state["current_step"] = "internal_analysis_completed"
            
            logger.info(f"Internal analysis completed: {result}")
            
        except Exception as e:
            logger.error(f"Error in internal agent: {e}")
            state["internal_analysis"] = {
                "department": "internal",
                "analysis": f"Error in internal analysis: {str(e)}",
                "confidence": 0.0,
                "recommendations": [],
                "risk_factors": []
            }
        
        return state
    
    return internal_agent

def create_surgical_agent():
    """创建外科专家Agent"""
    
    surgical_prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="""
你是一个经验丰富的外科专家。你的任务是分析患者的症状，提供外科角度的诊断分析和建议。

请重点关注：
1. 外科疾病的诊断可能性
2. 是否需要手术治疗
3. 手术风险评估
4. 术前准备建议
5. 术后护理建议

输出格式要求：
- department: "surgical"
- analysis: 详细分析内容
- confidence: 置信度（0-1之间）
- recommendations: 建议列表
- risk_factors: 风险因素列表
"""),
        MessagesPlaceholder(variable_name="messages"),
        HumanMessage(content="请从外科角度分析以下症状：{user_input}")
    ])
    
    def surgical_agent(state: MedicalState) -> MedicalState:
        """外科专家Agent"""
        try:
            messages = state.get("messages", [])
            user_input = state["user_input"]
            
            chain = surgical_prompt | llm | parser
            result = chain.invoke({
                "messages": messages,
                "user_input": user_input
            })
            
            state["surgical_analysis"] = result
            state["current_step"] = "surgical_analysis_completed"
            
            logger.info(f"Surgical analysis completed: {result}")
            
        except Exception as e:
            logger.error(f"Error in surgical agent: {e}")
            state["surgical_analysis"] = {
                "department": "surgical",
                "analysis": f"Error in surgical analysis: {str(e)}",
                "confidence": 0.0,
                "recommendations": [],
                "risk_factors": []
            }
        
        return state
    
    return surgical_agent

def create_emergency_agent():
    """创建急症科Agent"""
    
    emergency_prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="""
你是一个经验丰富的急症科专家。你的任务是分析患者的症状，评估紧急程度，提供急症处理建议。

请重点关注：
1. 生命体征评估
2. 紧急程度分级
3. 是否需要立即处理
4. 急救措施建议
5. 转运建议

输出格式要求：
- department: "emergency"
- analysis: 详细分析内容
- confidence: 置信度（0-1之间）
- recommendations: 建议列表
- risk_factors: 风险因素列表
"""),
        MessagesPlaceholder(variable_name="messages"),
        HumanMessage(content="请从急症科角度分析以下症状：{user_input}")
    ])
    
    def emergency_agent(state: MedicalState) -> MedicalState:
        """急症科Agent"""
        try:
            messages = state.get("messages", [])
            user_input = state["user_input"]
            
            chain = emergency_prompt | llm | parser
            result = chain.invoke({
                "messages": messages,
                "user_input": user_input
            })
            
            state["emergency_analysis"] = result
            state["current_step"] = "emergency_analysis_completed"
            
            logger.info(f"Emergency analysis completed: {result}")
            
        except Exception as e:
            logger.error(f"Error in emergency agent: {e}")
            state["emergency_analysis"] = {
                "department": "emergency",
                "analysis": f"Error in emergency analysis: {str(e)}",
                "confidence": 0.0,
                "recommendations": [],
                "risk_factors": []
            }
        
        return state
    
    return emergency_agent

def create_confidence_assessment():
    """创建置信评估节点"""
    
    confidence_prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="""
你是一个专业的医疗置信度评估专家。你的任务是评估各个科室专家的分析结果的置信度，并决定是否需要人工干预。

评估标准：
1. 各科室分析的置信度
2. 分析结果的一致性
3. 信息完整性
4. 不确定性因素
5. 是否需要人工审核

如果总体置信度<70%，需要人工干预。

输出格式要求：
- overall_confidence: 总体置信度（0-1之间）
- confidence_breakdown: 各科室置信度字典
- uncertainty_factors: 不确定性因素列表
- needs_human_review: 是否需要人工审核（布尔值）
- reasoning: 评估推理
"""),
        MessagesPlaceholder(variable_name="messages"),
        HumanMessage(content="""
请评估以下分析结果的置信度：

意图识别结果：{intent}
内科分析：{internal_analysis}
外科分析：{surgical_analysis}
急症科分析：{emergency_analysis}

请提供置信度评估。
""")
    ])
    
    def confidence_assessment(state: MedicalState) -> MedicalState:
        """置信评估节点"""
        try:
            messages = state.get("messages", [])
            intent = state.get("intent", {})
            internal_analysis = state.get("internal_analysis", {})
            surgical_analysis = state.get("surgical_analysis", {})
            emergency_analysis = state.get("emergency_analysis", {})
            
            chain = confidence_prompt | llm | parser
            result = chain.invoke({
                "messages": messages,
                "intent": json.dumps(intent, ensure_ascii=False),
                "internal_analysis": json.dumps(internal_analysis, ensure_ascii=False),
                "surgical_analysis": json.dumps(surgical_analysis, ensure_ascii=False),
                "emergency_analysis": json.dumps(emergency_analysis, ensure_ascii=False)
            })
            
            state["confidence_assessment"] = result
            state["confidence"] = result.get("overall_confidence", 0.0)
            state["human_intervention"] = result.get("needs_human_review", False)
            state["current_step"] = "confidence_assessment_completed"
            
            logger.info(f"Confidence assessment completed: {result}")
            
        except Exception as e:
            logger.error(f"Error in confidence assessment: {e}")
            state["confidence_assessment"] = {
                "overall_confidence": 0.0,
                "confidence_breakdown": {},
                "uncertainty_factors": [f"Error in confidence assessment: {str(e)}"],
                "needs_human_review": True,
                "reasoning": f"Error in confidence assessment: {str(e)}"
            }
            state["confidence"] = 0.0
            state["human_intervention"] = True
        
        return state
    
    return confidence_assessment

def create_human_intervention():
    """创建人工干预节点"""
    
    def human_intervention(state: MedicalState) -> MedicalState:
        """人工干预节点"""
        try:
            # 这里应该集成实际的人工干预界面
            # 目前使用模拟的人工反馈
            
            # 检查是否需要人工干预
            if state.get("human_intervention", False) or state.get("confidence", 0.0) < 0.7:
                logger.info("Human intervention required")
                
                # 模拟人工反馈（实际应用中应该从UI获取）
                human_feedback = "人工审核：建议进一步检查，症状描述不够详细"
                
                state["human_feedback"] = human_feedback
                state["current_step"] = "human_intervention_completed"
                
                # 更新置信度（人工干预后）
                state["confidence"] = min(1.0, state.get("confidence", 0.0) + 0.2)
                
            else:
                state["human_feedback"] = ""
                state["current_step"] = "human_intervention_skipped"
            
        except Exception as e:
            logger.error(f"Error in human intervention: {e}")
            state["human_feedback"] = f"Error in human intervention: {str(e)}"
        
        return state
    
    return human_intervention

def create_final_diagnosis_agent():
    """创建综合诊断Agent"""
    
    final_diagnosis_prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="""
你是一个资深的医疗诊断专家。你的任务是综合各个科室的分析结果，提供最终的诊断和治疗建议。

请综合考虑：
1. 各科室的分析结果
2. 置信度评估
3. 人工干预反馈（如果有）
4. 患者整体情况
5. 治疗优先级

输出格式要求：
- primary_diagnosis: 主要诊断
- differential_diagnoses: 鉴别诊断列表
- treatment_plan: 治疗方案列表
- urgency_level: 紧急程度
- follow_up: 随访建议
- confidence: 最终置信度
"""),
        MessagesPlaceholder(variable_name="messages"),
        HumanMessage(content="""
请基于以下信息提供综合诊断：

意图识别：{intent}
内科分析：{internal_analysis}
外科分析：{surgical_analysis}
急症科分析：{emergency_analysis}
置信评估：{confidence_assessment}
人工反馈：{human_feedback}

请提供综合诊断结果。
""")
    ])
    
    def final_diagnosis_agent(state: MedicalState) -> MedicalState:
        """综合诊断Agent"""
        try:
            messages = state.get("messages", [])
            intent = state.get("intent", {})
            internal_analysis = state.get("internal_analysis", {})
            surgical_analysis = state.get("surgical_analysis", {})
            emergency_analysis = state.get("emergency_analysis", {})
            confidence_assessment = state.get("confidence_assessment", {})
            human_feedback = state.get("human_feedback", "")
            
            chain = final_diagnosis_prompt | llm | parser
            result = chain.invoke({
                "messages": messages,
                "intent": json.dumps(intent, ensure_ascii=False),
                "internal_analysis": json.dumps(internal_analysis, ensure_ascii=False),
                "surgical_analysis": json.dumps(surgical_analysis, ensure_ascii=False),
                "emergency_analysis": json.dumps(emergency_analysis, ensure_ascii=False),
                "confidence_assessment": json.dumps(confidence_assessment, ensure_ascii=False),
                "human_feedback": human_feedback
            })
            
            state["final_diagnosis"] = result
            state["current_step"] = "final_diagnosis_completed"
            
            logger.info(f"Final diagnosis completed: {result}")
            
        except Exception as e:
            logger.error(f"Error in final diagnosis agent: {e}")
            state["final_diagnosis"] = {
                "primary_diagnosis": "诊断错误",
                "differential_diagnoses": [],
                "treatment_plan": ["请咨询医生"],
                "urgency_level": "medium",
                "follow_up": "请及时就医",
                "confidence": 0.0
            }
        
        return state
    
    return final_diagnosis_agent

# 路由函数
def route_after_triage(state: MedicalState) -> str:
    """分诊后的路由逻辑"""
    confidence = state.get("confidence", 0.0)
    
    if confidence < 0.7:
        return "human_intervention"
    else:
        return "parallel_analysis"

def route_after_confidence_assessment(state: MedicalState) -> str:
    """置信评估后的路由逻辑"""
    confidence = state.get("confidence", 0.0)
    
    if confidence < 0.7:
        return "human_intervention"
    else:
        return "final_diagnosis"

def route_after_human_intervention(state: MedicalState) -> str:
    """人工干预后的路由逻辑"""
    # 如果已经完成了并行分析，直接进入最终诊断
    if state.get("internal_analysis") and state.get("surgical_analysis") and state.get("emergency_analysis"):
        return "final_diagnosis"
    else:
        return "parallel_analysis"

# 并行分析节点
def create_parallel_analysis():
    """创建并行分析节点"""
    
    def parallel_analysis(state: MedicalState) -> MedicalState:
        """并行执行各科室分析"""
        try:
            # 创建各科室Agent
            internal_agent = create_internal_agent()
            surgical_agent = create_surgical_agent()
            emergency_agent = create_emergency_agent()
            
            # 并行执行分析（这里简化为顺序执行）
            state = internal_agent(state)
            state = surgical_agent(state)
            state = emergency_agent(state)
            
            state["current_step"] = "parallel_analysis_completed"
            
            logger.info("Parallel analysis completed")
            
        except Exception as e:
            logger.error(f"Error in parallel analysis: {e}")
        
        return state
    
    return parallel_analysis

def create_medical_workflow():
    """创建医疗专家系统工作流"""
    
    # 创建工作流图
    workflow = StateGraph(MedicalState)
    
    # 添加节点
    workflow.add_node("triage", create_triage_agent())
    workflow.add_node("human_intervention", create_human_intervention())
    workflow.add_node("parallel_analysis", create_parallel_analysis())
    workflow.add_node("confidence_assessment", create_confidence_assessment())
    workflow.add_node("final_diagnosis", create_final_diagnosis_agent())
    
    # 设置入口点
    workflow.set_entry_point("triage")
    
    # 添加条件边
    workflow.add_conditional_edges(
        "triage",
        route_after_triage,
        {
            "human_intervention": "human_intervention",
            "parallel_analysis": "parallel_analysis"
        }
    )
    
    workflow.add_conditional_edges(
        "human_intervention",
        route_after_human_intervention,
        {
            "parallel_analysis": "parallel_analysis",
            "final_diagnosis": "final_diagnosis"
        }
    )
    
    workflow.add_edge("parallel_analysis", "confidence_assessment")
    
    workflow.add_conditional_edges(
        "confidence_assessment",
        route_after_confidence_assessment,
        {
            "human_intervention": "human_intervention",
            "final_diagnosis": "final_diagnosis"
        }
    )
    
    workflow.add_edge("final_diagnosis", END)
    
    return workflow.compile()

def test_medical_workflow():
    """测试医疗专家系统工作流"""
    
    # 创建工作流
    workflow = create_medical_workflow()
    
    # 测试用例
    test_cases = [
        {
            "description": "胸痛症状",
            "input": "患者男性，45岁，主诉胸痛，疼痛持续30分钟，伴有出汗和呼吸困难"
        },
        {
            "description": "腹痛症状",
            "input": "患者女性，28岁，右下腹疼痛，伴有恶心呕吐，疼痛逐渐加重"
        },
        {
            "description": "发热症状",
            "input": "患者儿童，5岁，发热38.5度，伴有咳嗽和流鼻涕，持续2天"
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n=== 测试用例: {test_case['description']} ===")
        
        # 初始化状态
        initial_state = {
            "messages": [],
            "user_input": test_case["input"],
            "intent": {},
            "confidence": 0.0,
            "triage_result": {},
            "internal_analysis": {},
            "surgical_analysis": {},
            "emergency_analysis": {},
            "confidence_assessment": {},
            "final_diagnosis": {},
            "human_intervention": False,
            "human_feedback": "",
            "current_step": "start"
        }
        
        try:
            # 执行工作流
            result = workflow.invoke(initial_state)
            results.append({
                "test_case": test_case,
                "result": result
            })
            
            # 打印结果摘要
            print(f"最终诊断: {result.get('final_diagnosis', {}).get('primary_diagnosis', 'N/A')}")
            print(f"置信度: {result.get('confidence', 0.0):.2f}")
            print(f"是否需要人工干预: {result.get('human_intervention', False)}")
            
        except Exception as e:
            print(f"测试失败: {e}")
            results.append({
                "test_case": test_case,
                "error": str(e)
            })
    
    return results

if __name__ == "__main__":
    test_results = test_medical_workflow()
    print(f"\n测试完成，共执行 {len(test_results)} 个测试用例") 