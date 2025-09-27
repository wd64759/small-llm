# 医疗专家系统 - LangGraph框架

## 系统概述

本系统使用LangGraph构建了一个完整的医疗专家系统，实现了多科室专家协作诊断的功能。系统采用模块化设计，支持并行分析、置信度评估和人工干预机制。

## 系统架构

### 核心组件

1. **意图识别Triage Agent Planner**
   - 分析患者症状描述
   - 识别医疗意图
   - 确定紧急程度
   - 推荐涉及科室

2. **多科室专家Agent**
   - **内科专家Agent**: 内科疾病诊断和分析
   - **外科专家Agent**: 外科疾病诊断和手术建议
   - **急症科Agent**: 紧急情况评估和处理

3. **置信评估节点**
   - 评估各科室分析的置信度
   - 判断是否需要人工干预
   - 提供不确定性分析

4. **综合诊断Agent**
   - 综合各科室分析结果
   - 提供最终诊断和治疗建议
   - 生成随访计划

5. **Human-in-loop节点**
   - 置信度<70%时触发
   - 支持人工审核和干预
   - 提供反馈机制

### 工作流程

```
用户输入 → 意图识别 → 置信度检查(<70%→人工干预) → 并行分析(内科/外科/急症科) → 置信评估 → 置信度检查(<70%→人工干预) → 综合诊断 → 输出结果
```

## 文件结构

```
evaluation/
├── medical_expert_system.py    # 核心系统实现
├── langgragh_eval.ipynb        # Jupyter演示notebook
└── README_medical_system.md    # 本文档
```

## 安装和配置

### 1. 环境要求

- Python 3.8+
- LangGraph
- LangChain
- OpenAI API

### 2. 安装依赖

```bash
pip install langgraph langchain langchain-openai
```

### 3. 配置环境变量

```bash
export OPENAI_API_KEY="your-openai-api-key"
```

## 使用方法

### 1. 基本使用

```python
from medical_expert_system import create_medical_workflow, MedicalState

# 创建工作流
workflow = create_medical_workflow()

# 准备输入
initial_state = {
    "messages": [],
    "user_input": "患者男性，45岁，主诉胸痛，疼痛持续30分钟，伴有出汗和呼吸困难",
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

# 执行工作流
result = workflow.invoke(initial_state)

# 查看结果
print(f"最终诊断: {result['final_diagnosis']['primary_diagnosis']}")
print(f"置信度: {result['confidence']}")
```

### 2. 使用Jupyter Notebook

1. 打开 `langgragh_eval.ipynb`
2. 运行所有单元格
3. 查看测试结果和分析

### 3. 交互式测试

```python
# 在notebook中运行交互式测试
interactive_test(workflow)
```

## 系统特性

### 1. 多科室并行分析

- 内科、外科、急症科专家同时分析
- 提高诊断效率和准确性
- 支持科室间协作

### 2. 置信度驱动决策

- 自动评估分析置信度
- 置信度<70%时触发人工干预
- 确保诊断质量

### 3. Human-in-loop机制

- 支持人工审核和干预
- 提供反馈机制
- 增强系统可靠性

### 4. 异常处理

- 完善的错误处理机制
- 系统容错能力
- 日志记录和监控

## 测试用例

系统包含以下测试用例：

1. **胸痛症状**: 患者男性，45岁，主诉胸痛，疼痛持续30分钟，伴有出汗和呼吸困难
2. **腹痛症状**: 患者女性，28岁，右下腹疼痛，伴有恶心呕吐，疼痛逐渐加重
3. **发热症状**: 患者儿童，5岁，发热38.5度，伴有咳嗽和流鼻涕，持续2天
4. **外伤症状**: 患者男性，30岁，车祸后右腿疼痛，无法行走，有开放性伤口

## 输出格式

### 意图识别结果

```json
{
    "intent": "胸痛",
    "confidence": 0.85,
    "urgency_level": "high",
    "departments": ["internal", "emergency"],
    "reasoning": "患者症状符合急性冠脉综合征表现"
}
```

### 专家分析结果

```json
{
    "department": "internal",
    "analysis": "患者症状高度怀疑急性心肌梗死",
    "confidence": 0.8,
    "recommendations": ["立即心电图检查", "心肌酶检测", "冠状动脉造影"],
    "risk_factors": ["年龄", "男性", "胸痛症状"]
}
```

### 综合诊断结果

```json
{
    "primary_diagnosis": "急性心肌梗死",
    "differential_diagnoses": ["心绞痛", "主动脉夹层", "肺栓塞"],
    "treatment_plan": ["立即住院", "抗血小板治疗", "冠状动脉造影"],
    "urgency_level": "critical",
    "follow_up": "定期心内科随访",
    "confidence": 0.82
}
```

## 扩展和定制

### 1. 添加新的专家Agent

```python
def create_new_specialist_agent():
    """创建新的专科专家Agent"""
    
    specialist_prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="你是一个专业的[专科名称]专家..."),
        MessagesPlaceholder(variable_name="messages"),
        HumanMessage(content="请从[专科名称]角度分析以下症状：{user_input}")
    ])
    
    def specialist_agent(state: MedicalState) -> MedicalState:
        # 实现专家逻辑
        return state
    
    return specialist_agent
```

### 2. 修改置信度阈值

```python
# 在路由函数中修改阈值
def route_after_triage(state: MedicalState) -> str:
    confidence = state.get("confidence", 0.0)
    
    if confidence < 0.8:  # 修改为80%
        return "human_intervention"
    else:
        return "parallel_analysis"
```

### 3. 自定义输出格式

```python
# 修改输出模型
class CustomDiagnosis(BaseModel):
    primary_diagnosis: str
    confidence: float
    # 添加自定义字段
```

## 故障排除

### 常见问题

1. **导入错误**
   - 确保所有依赖已安装
   - 检查Python路径

2. **API错误**
   - 验证OpenAI API Key
   - 检查网络连接

3. **工作流错误**
   - 检查状态格式
   - 验证节点连接

### 调试模式

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交Issue或联系开发团队。 