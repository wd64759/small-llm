# 大模型记忆权重设计方法

记忆权重设计是实现高效记忆系统的核心环节，它决定了哪些信息应该被优先保留和使用。以下是记忆权重的系统化设计方法：

## 一、基础权重维度

### 1. 静态权重因子
| 权重因子         | 说明                          | 典型权重值       |
|------------------|-----------------------------|----------------|
| **时间衰减**      | 越新的记忆权重越高              | `1/(1+时间差小时数)` |
| **交互频率**      | 被提及/使用次数越多权重越高      | `log(使用次数+1)`   |
| **用户显式标记**  | 用户明确要求记住的内容           | 手动设置为1.0      |
| **实体类型**      | 人物/地点等核心实体权重更高      | 人物:0.9, 地点:0.7 |

### 2. 动态计算示例
```python
import math
from datetime import datetime, timedelta

def calculate_basic_weight(memory_item):
    # 时间衰减 (最近1小时内的记忆保持完整权重)
    time_decay = 1 / (1 + (datetime.now() - memory_item.timestamp).total_seconds() / 3600)
    
    # 使用频率
    frequency_weight = math.log(1 + memory_item.access_count)
    
    # 类型权重
    type_weights = {"person": 0.9, "place": 0.7, "fact": 0.5}
    type_weight = type_weights.get(memory_item.type, 0.6)
    
    return 0.4 * time_decay + 0.3 * frequency_weight + 0.3 * type_weight
```

## 二、基于语义的权重增强

### 1. 相关性权重
```python
from sentence_transformers import SentenceTransformer

encoder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

def semantic_relevance(current_input, memory_content):
    # 计算当前输入与记忆内容的语义相似度
    input_embed = encoder.encode(current_input)
    memory_embed = encoder.encode(memory_content)
    return cosine_similarity([input_embed], [memory_embed])[0][0]
```

### 2. 话题聚类权重
```python
from sklearn.cluster import KMeans

def topic_based_weight(memories, n_clusters=5):
    # 对记忆内容进行话题聚类
    embeddings = encoder.encode([m.content for m in memories])
    kmeans = KMeans(n_clusters=n_clusters).fit(embeddings)
    
    # 给主流话题更高权重
    cluster_counts = Counter(kmeans.labels_)
    max_count = max(cluster_counts.values())
    return {
        idx: count / max_count 
        for idx, count in cluster_counts.items()
    }
```

## 三、高级权重策略

### 1. 基于LLM的元认知评估
```python
def llm_importance_assessment(memory_content):
    prompt = f"""请评估以下记忆内容的重要性(0.0-1.0)：
    评估标准：
    1. 对理解用户偏好关键程度
    2. 对维持对话连贯性作用
    3. 未来可能被提及的概率
    
    记忆内容：{memory_content}
    只需返回0.0到1.0之间的数字："""
    
    response = chat_model.invoke(prompt)
    return float(response.strip())
```

### 2. 强化学习动态调整
```python
class MemoryWeightOptimizer:
    def __init__(self):
        self.weights = {
            'time_decay': 0.4,
            'frequency': 0.3,
            'semantic': 0.3
        }
        self.learning_rate = 0.01
    
    def update_weights(self, used_memories, unused_memories):
        # 根据实际使用情况调整权重系数
        for mem in used_memories:
            self.weights['semantic'] += self.learning_rate
        for mem in unused_memories:
            self.weights['time_decay'] -= self.learning_rate
```

## 四、生产环境实现方案

### 1. 分层权重系统
```python
def composite_weight(memory_item, current_context):
    base = calculate_basic_weight(memory_item)
    semantic = semantic_relevance(current_context, memory_item.content)
    llm_score = llm_importance_assessment(memory_item.content)
    
    return 0.5 * base + 0.3 * semantic + 0.2 * llm_score
```

### 2. 记忆权重缓存
```python
class WeightedMemory:
    def __init__(self, max_size=1000):
        self.memories = []
        self.weight_cache = {}
        self.max_size = max_size
    
    def add_memory(self, content, metadata):
        if len(self.memories) >= self.max_size:
            self._remove_lowest_weight()
        self.memories.append({"content": content, "meta": metadata})
        self.weight_cache[id(content)] = self._calculate_weight(content)
    
    def get_top_k(self, k, context):
        scored = [(m, self._get_weight(m['content'], context)) 
                 for m in self.memories]
        return sorted(scored, key=lambda x: -x[1])[:k]
```

## 五、特定场景优化策略

### 1. 客服对话场景
```python
def customer_service_weight(memory):
    # 提升投诉记录、产品询问的权重
    if "投诉" in memory.content or "问题" in memory.content:
        return min(1.0, memory.base_weight * 1.5)
    # 降低寒暄内容的权重
    elif any(w in memory.content for w in ["你好","谢谢","再见"]):
        return memory.base_weight * 0.7
    return memory.base_weight
```

### 2. 教育辅导场景
```python
def education_weight(memory):
    # 提升知识点错误的记忆权重
    if memory.metadata.get('type') == 'misconception':
        return min(1.0, memory.base_weight * 2.0)
    # 提升反复讲解的内容权重
    elif memory.metadata.get('repeated', 0) > 1:
        return min(1.0, memory.base_weight * (1 + 0.2 * memory.metadata.repeated))
    return memory.base_weight
```

## 六、评估与调优方法

### 1. 权重效果评估指标
```python
def evaluate_weight_system(test_cases):
    precision = []
    recall = []
    for case in test_cases:
        # 计算系统选择的记忆
        selected = memory_system.retrieve(case['context'])
        # 计算与人工标注的理想记忆的重合度
        ideal = set(case['ideal_memories'])
        selected_set = set(m.content for m in selected)
        precision.append(len(ideal & selected_set) / len(selected_set))
        recall.append(len(ideal & selected_set) / len(ideal))
    return {
        "precision": np.mean(precision),
        "recall": np.mean(recall),
        "f1": 2 * (np.mean(precision) * np.mean(recall)) / (np.mean(precision) + np.mean(recall))
    }
```

记忆权重设计需要根据具体应用场景持续迭代优化，建议采用A/B测试框架比较不同权重策略的实际效果。好的权重系统应该能够：在token限制内最大化记忆效用、适应用户对话风格、动态调整重要性判断。