import streamlit as st
import asyncio
import json
import handcraft.chatbot as chatbot

# 预定义的对话机器人配置
PREDEFINED_CHATBOTS = {
    "通用助手": {
        "model": "qwen-max",
        "system_prompt": "You are a helpful assistant. You have access to tools that you can use to help answer questions. When you need information that can be obtained through tools, please use them.",
        "description": "一个通用的AI助手，可以回答问题并使用工具"
    }
}

# 可用的工具
AVAILABLE_TOOLS = {
    "get_location": {
        "name": "get_location",
        "func": lambda: "北京",
        "description": "Get user's location",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    "get_weather": {
        "name": "get_weather",
        "func": lambda location="北京": f"{location}今天天气晴朗",
        "description": "Get the weather for a specific location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The location to get the weather for"
                }
            },
            "required": ["location"]
        }
    },
    "get_news": {
        "name": "get_news",
        "func": lambda location="北京": f"{location}的新闻：今天天气晴朗",
        "description": "Get the latest news for a specific location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The location to get news for"
                }
            },
            "required": ["location"]
        }
    },
    "calculate": {
        "name": "calculate",
        "func": lambda expression: eval(expression),
        "description": "Perform mathematical calculations",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The mathematical expression to evaluate"
                }
            },
            "required": ["expression"]
        }
    }
}

def initialize_session_state():
    """初始化会话状态"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = None
    if 'selected_tools' not in st.session_state:
        st.session_state.selected_tools = []

def create_control_panel():
    """创建左侧控制面板"""
    st.sidebar.title("🤖 对话控制面板")
    
    # 选择预定义的对话机器人
    # st.sidebar.subheader("选择对话机器人")
    selected_bot = st.sidebar.selectbox(
        "预定义机器人:",
        list(PREDEFINED_CHATBOTS.keys()),
        help="选择一个预定义的对话机器人配置"
    )
    
    # 显示选中机器人的描述
    if selected_bot != "自定义":
        st.sidebar.info(f"**{selected_bot}**: {PREDEFINED_CHATBOTS[selected_bot]['description']}")
    
    # 系统提示词设置
    # st.sidebar.subheader("系统提示词")
    if selected_bot == "自定义":
        system_prompt = st.sidebar.text_area(
            "自定义系统提示词:",
            value="You are a helpful assistant.",
            height=200,
            help="设置AI助手的系统提示词"
        )
    else:
        system_prompt = st.sidebar.text_area(
            "系统提示词:",
            value=PREDEFINED_CHATBOTS[selected_bot]['system_prompt'],
            height=200,
            help="可以修改系统提示词"
        )
    
    # 模型选择
    # st.sidebar.subheader("模型设置")
    model = st.sidebar.selectbox(
        "选择模型:",
        ["qwen-max", "qwen-turbo", "qwen-plus"],
        index=0,
        help="选择要使用的AI模型"
    )
    
    # 工具选择
    # st.sidebar.subheader("可用工具")
    st.sidebar.write("选择要启用的工具:")
    
    selected_tools = []
    for tool_name, tool_info in AVAILABLE_TOOLS.items():
        if st.sidebar.checkbox(
            f"🔧 {tool_name}",
            value=tool_name in ["get_location", "get_weather"],  # 默认选中常用工具
            help=tool_info['description']
        ):
            selected_tools.append(tool_info)
    
    # 创建/更新聊天机器人按钮
    if st.sidebar.button("🚀 创建/更新聊天机器人", type="primary"):
        if selected_tools:
            st.session_state.chatbot = chatbot.Chatbot(
                model=model,
                system_prompt=system_prompt,
                tools=selected_tools,
                context=""
            )
            st.session_state.selected_tools = selected_tools
            st.session_state.messages = []  # 清空对话历史
            st.success("✅ 聊天机器人已创建/更新！")
        else:
            st.error("❌ 请至少选择一个工具！")
    
    # 显示当前配置
    if st.session_state.chatbot:
        st.sidebar.subheader("当前配置")
        st.sidebar.write(f"**模型**: {st.session_state.chatbot.model}")
        st.sidebar.write(f"**工具数量**: {len(st.session_state.selected_tools)}")
        st.sidebar.write("**已选工具**:")
        for tool in st.session_state.selected_tools:
            st.sidebar.write(f"  - {tool['name']}")
    
    # 清空对话按钮
    if st.sidebar.button("🗑️ 清空对话历史"):
        st.session_state.messages = []
        st.rerun()

def create_chat_interface():
    """创建右侧聊天界面"""
    st.title("💬 AI 对话界面")
    
    # 检查是否已创建聊天机器人
    if not st.session_state.chatbot:
        st.warning("⚠️ 请在左侧控制面板创建聊天机器人后再开始对话！")
        return
    
    # 显示对话历史
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "tool":
                st.write(f"🔧 **工具调用**: {message['name']}")
                st.write(f"📄 **结果**: {message['content']}")
            else:
                st.write(message["content"])
    
    # 用户输入
    if prompt := st.chat_input("请输入您的问题..."):
        # 添加用户消息
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # 显示用户消息
        with st.chat_message("user"):
            st.write(prompt)
        
        # 显示助手消息占位符
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            # 执行聊天（这里需要处理异步调用）
            try:
                # 使用Streamlit的异步支持
                import asyncio
                import nest_asyncio
                nest_asyncio.apply()
                
                # 运行聊天
                loop = asyncio.get_event_loop()
                loop.run_until_complete(st.session_state.chatbot.chat(prompt))
                
                # 获取最新的助手回复
                if st.session_state.chatbot.messages:
                    last_assistant_message = None
                    for msg in reversed(st.session_state.chatbot.messages):
                        if msg["role"] == "assistant" and msg.get("content"):
                            last_assistant_message = msg["content"]
                            break
                    
                    if last_assistant_message:
                        message_placeholder.write(last_assistant_message)
                        # 更新会话状态中的消息
                        st.session_state.messages.append({"role": "assistant", "content": last_assistant_message})
                
            except Exception as e:
                message_placeholder.error(f"❌ 发生错误: {str(e)}")
                st.error(f"详细错误信息: {str(e)}")
    
    # 显示对话统计
    if st.session_state.messages:
        st.sidebar.subheader("对话统计")
        user_messages = len([m for m in st.session_state.messages if m["role"] == "user"])
        assistant_messages = len([m for m in st.session_state.messages if m["role"] == "assistant"])
        tool_calls = len([m for m in st.session_state.messages if m["role"] == "tool"])
        
        st.sidebar.write(f"👤 用户消息: {user_messages}")
        st.sidebar.write(f"🤖 助手回复: {assistant_messages}")
        st.sidebar.write(f"🔧 工具调用: {tool_calls}")

def main():
    """主函数"""
    st.set_page_config(
        page_title="AI 对话机器人",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 初始化会话状态
    initialize_session_state()
    
    # 创建两列布局
    col1, col2 = st.columns([1, 3])
    
    with col1:
        create_control_panel()
    
    with col2:
        create_chat_interface()

if __name__ == "__main__":
    main()
