# High Level Design

``` mermaid
graph TD
  %% 层次一
  query[用户请求]
  rewriter[基于历史对话的上下文重写]
  rag[RAG 信息增强]
  planner[领域规划 Multi-Path Planner]

  query --> rewriter --> rag --> planner

  %% 多个领域
  planner --> market[市场分析]
  planner --> product[产品分析]
  planner --> position[持仓分析]
  planner --> general[金融通识]

  %% 层次二：市场分析子领域
  market --> macro[宏观政策]
  market --> industry[行业分析]
  market --> index[指数分析]
  market --> company[公司解读]
  macro --> market_agg[市场分析汇总 aggregator+置信检查]
  industry --> market_agg
  index --> market_agg
  company --> market_agg

  %% 层次二：产品分析子领域
  product --> multifactor[多因子选品]
  product --> compare[产品对比]
  product --> stock_1[股票]
  product --> bond_1[债券]
  product --> fund_1[基金]
  multifactor --> stock_1
  multifactor --> bond_1
  multifactor --> fund_1
  compare --> stock_1
  compare --> bond_1
  compare --> fund_1

  %% 股票/债券/基金 关联市场分析
  stock_1 --> industry
  stock_1 --> company
  stock_1 --> macro
  bond_1 --> macro
  fund_1 --> index

  stock_1 --> product_agg[产品分析汇总 aggregator+置信检查]
  bond_1 --> product_agg
  fund_1 --> product_agg
  multifactor --> product_agg
  compare --> product_agg

  %% 层次二：持仓分析子领域
  position --> risk[持仓风险评估]
  position --> return[持仓收益分析]
  position --> goal[财富目标规划]

  risk --> stock_1
  risk --> bond_1
  risk --> fund_1
  return --> stock_1
  return --> bond_1
  return --> fund_1
  goal --> stock_1
  goal --> bond_1
  goal --> fund_1

  risk --> position_agg[持仓分析汇总 aggregator+置信检查]
  return --> position_agg
  goal --> position_agg

  general --> general_agg[金融通识 aggregator]

  %% 层次三：分析规划
  market_agg --> analysis_planner[分析 Planner]
  product_agg --> analysis_planner
  position_agg --> analysis_planner
  general_agg --> analysis_planner

  analysis_planner --> im[投资经理 reviewer]
  analysis_planner --> advisor[投研顾问 reviewer]
  analysis_planner --> service[客服解答 reviewer]

  im --> END
  advisor --> END
  service --> END
```
## 设计要点说明
- 使用可调度版本的LangGraph（支持条件流+并行） 
除了reviewer部分之外，所有的分支都利用LangGraph的conditional edge + parallel branch构建。
    ```python
    builder.add_conditional_edges(
        "planner",
        lambda state: state["selected_domains"],
        {
            "market": "market",
            "product": "product",
            ...
        }
    )
    ```

- 节点之间的依赖以state显式管理  
    例如：
    - 股票 → 行业分析，是 依赖关系（传递行业代码）
    - 多因子选品 → 股票，是 任务触发
   ```python 
    state = {
        "stock_tickers": ["600519"],
        "industry_code": "B12",
    ...
    }
    ```

- aggregator 节点应具备“中间解释能力”
每个 aggregator：
    - 输出一个“子结论”
    - 记录数据来源与置信度
    - 标记是否存在冲突（如宏观建议看多 vs 技术看空）
    ```json
    {
        "domain": "市场分析",
        "summary": "宏观环境支持反弹，行业强势",
        "confidence": 0.85,
        "conflicts": ["公司财务不佳"]
    }
    ```
- reviewers具备角色差异化目标（提示词结构和风格不同）

    | Reviewer | 职能目标           |
    | -------- | -------------- |
    | 投资经理     | 战略建议 + 实盘调仓建议  |
    | 投研顾问     | 投资逻辑、底层研究      |
    | 客服解答     | 面向客户解释 + 普通话术化 |

- 多轮规划能力
    - 对涉及投资相关问题，在用户初始问题后自动问回问题（clarify intent）
    - 规划阶段进行确认（是否要结合持仓）
    - 领域规划planner 后让用户选择继续“投资建议”、“调仓计划”等
    ```mermaid
    graph TD
        planner[领域规划Planner]
        planner --> next_decision{是否继续？}
        next_decision --> 调仓助手Agent
        next_decision --> 结束END
    ```

### 代码整合实现
 TODO：FinancialAnalyzeFundAgent

### 数据库
数据库连接：118.25.6.157
数据库名：jydb
用户名：root
密码：2wsx!QAZ

### RAG设计