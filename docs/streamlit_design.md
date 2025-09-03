# AI 对话机器人 - Streamlit 应用

这是一个基于Streamlit构建的AI对话机器人界面，支持多种预定义机器人和工具调用。

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

在 `handcraft` 目录下创建 `.env` 文件：

```env
DASHSCOPE_API_KEY=your_api_key_here
DASHSCOPE_API_URL=your_api_url_here
```

### 3. 启动应用

方式一：使用启动脚本
```bash
python run_app.py
```

方式二：直接使用Streamlit
```bash
streamlit run streamlit_app.py
```

## 🎯 功能特性

### 左侧控制面板
- **预定义机器人选择**: 通用助手、天气助手、新闻助手、自定义
- **系统提示词设置**: 可自定义AI助手的系统提示词
- **模型选择**: 支持 qwen-max、qwen-turbo、qwen-plus
- **工具选择**: 可选择启用不同的工具
- **配置管理**: 实时显示当前配置状态

### 右侧对话界面
- **实时对话**: 支持多轮对话
- **工具调用显示**: 可视化显示工具调用过程
- **对话历史**: 保存完整的对话历史
- **统计信息**: 显示用户消息、助手回复、工具调用数量

### 可用工具
- **get_location**: 获取用户位置
- **get_weather**: 获取指定位置的天气信息
- **get_news**: 获取指定位置的新闻
- **calculate**: 执行数学计算

## 🎨 界面预览

```
┌─────────────────────────────────────────────────────────────┐
│                    AI 对话机器人                              │
├─────────────┬───────────────────────────────────────────────┤
│ 🤖 控制面板   │ 💬 对话界面                                    │
│             │                                               │
│ 选择机器人    │ 用户: 你好，帮我查一下今天的天气怎么样？         │
│ 系统提示词    │                                               │
│ 模型设置      │ 助手: 我来帮您查询天气信息...                  │
│ 工具选择      │ 🔧 工具调用: get_location                     │
│             │ 📄 结果: 北京                                  │
│ 🚀 创建机器人  │                                               │
│             │ 助手: 根据查询结果，北京今天天气晴朗...           │
│ 当前配置      │                                               │
│ 对话统计      │ 请输入您的问题...                             │
└─────────────┴───────────────────────────────────────────────┘
```

## 🔧 自定义配置

### 添加新的预定义机器人

在 `streamlit_app.py` 中的 `PREDEFINED_CHATBOTS` 字典中添加：

```python
"我的助手": {
    "model": "qwen-max",
    "system_prompt": "你是一个专业的...",
    "description": "专门处理..."
}
```

### 添加新的工具

在 `AVAILABLE_TOOLS` 字典中添加：

```python
"my_tool": {
    "name": "my_tool",
    "func": lambda param: f"处理结果: {param}",
    "description": "我的自定义工具",
    "parameters": {
        "type": "object",
        "properties": {
            "param": {
                "type": "string",
                "description": "参数描述"
            }
        },
        "required": ["param"]
    }
}
```

## 🐛 故障排除

### 常见问题

1. **API密钥错误**
   - 检查 `.env` 文件中的API密钥是否正确
   - 确保API密钥有足够的权限

2. **异步调用错误**
   - 确保安装了 `nest-asyncio` 包
   - 检查Python版本兼容性

3. **工具调用失败**
   - 检查工具函数是否正确实现
   - 确保工具参数格式正确

### 调试模式

启动时添加 `--logger.level debug` 参数：

```bash
streamlit run streamlit_app.py --logger.level debug
```

## 📝 更新日志

- **v1.0.0**: 初始版本，支持基本的对话和工具调用功能
- 支持多种预定义机器人配置
- 实时工具调用显示
- 完整的对话历史管理

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 📄 许可证

MIT License
