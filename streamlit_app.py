from mcp import ClientSession, StdioServerParameters, stdio_client
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

PREDEFINED_MODELS = {
    "qwen-max": "qwen-max",
    "qwen-turbo": "qwen-turbo",
    "qwen-plus": "qwen-plus"
}

def initialize_session_state():
    """初始化会话状态"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = None
    if 'selected_tools' not in st.session_state:
        st.session_state.selected_tools = []
    if 'debug_info' not in st.session_state:
        st.session_state.debug_info = {
            'chat_reports': [],
            'llm_messages': [],
            'cot_info': []
        }

async def get_available_tools():
    """获取可用的工具"""
    std_params = StdioServerParameters(
        command="/Users/dongwei/Library/Caches/pypoetry/virtualenvs/langchain-project-y8rcUVU--py3.12/bin/python",
        args=["handcraft/mcp_tools.py"]
    )
    async with stdio_client(std_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            list_tools = await session.list_tools()
            tools = [chatbot.MCPTool(name=tool.name, description=tool.description, parameters=tool.inputSchema) for tool in list_tools.tools]
            return tools

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
        list(PREDEFINED_MODELS.keys()),
        index=0,
        help="选择要使用的AI模型"
    )

    depth_thinking = st.sidebar.checkbox("深度思考", value=True, help="启用深度思考")
    debug_enabled = st.sidebar.checkbox("调试", value=True, help="启用调试模式")
    
    # 工具选择
    # st.sidebar.subheader("可用工具")
    st.sidebar.write("选择挂载工具:")
    
    selected_tools = []
    tools = asyncio.run(get_available_tools())
    for tool in tools:
        if st.sidebar.checkbox(
            f"🔧 {tool.name}",
            value=tool.name in ["get_location"],  # 默认选中常用工具
            help=tool.description
        ):
            selected_tools.append(tool)
    
    # 创建/更新聊天机器人按钮
    if st.sidebar.button("🚀 创建/更新聊天机器人", type="primary"):
        if selected_tools:
            st.session_state.chatbot = chatbot.Chatbot(
                model=PREDEFINED_MODELS[model],
                system_prompt=system_prompt,
                tools=selected_tools,
                context="",
                depth_thinking=depth_thinking,
                debug=debug_enabled
            )
            st.session_state.selected_tools = selected_tools
            st.session_state.messages = []  # 清空对话历史
            st.success("✅ 聊天机器人已创建/更新！")
        else:
            st.error("❌ 请至少选择一个工具！")
    
    # 清空对话按钮
    if st.sidebar.button("🗑️ 清空对话历史"):
        st.session_state.messages = []
        st.session_state.debug_info = {
            'chat_reports': [],
            'llm_messages': [],
            'cot_info': []
        }
        st.rerun()

def create_chat_interface():
    """创建右侧聊天界面"""
    st.title("💬 AI 对话界面")
    
    # 检查是否已创建聊天机器人
    if not st.session_state.chatbot:
        st.warning("⚠️ 请在左侧控制面板创建聊天机器人后再开始对话！")
        return
    else:
        st.markdown(":green-badge[" + st.session_state.chatbot.model + "] " + "".join([f":violet-badge[:material/check: {tool.name}] " for tool in st.session_state.selected_tools]))

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
                
                # 运行聊天并获取报告
                loop = asyncio.get_event_loop()
                chat_report = loop.run_until_complete(st.session_state.chatbot.chat(prompt))
                
                # 保存调试信息
                st.session_state.debug_info['chat_reports'].append(chat_report.to_dict())
                st.session_state.debug_info['llm_messages'].append({
                    'prompt': prompt,
                    'messages': st.session_state.chatbot.messages.copy()
                })
                
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

def create_debug_area():
    """创建调试区域"""
    st.markdown("---")
    st.subheader("🔍 调试信息")
    
    # 创建tab
    tab1, tab2, tab3 = st.tabs(["📝 Messages", "📊 Chat Reports", "🧠 COT Info"])
    
    with tab1:
        st.markdown("### LLM Messages 内容")
        if st.session_state.debug_info['llm_messages']:
            for i, msg_data in enumerate(st.session_state.debug_info['llm_messages']):
                with st.expander(f"对话 #{i+1}: {msg_data['prompt'][:50]}..."):
                    st.markdown("**用户输入:**")
                    st.code(msg_data['prompt'], language="text")
                    
                    st.markdown("**完整 Messages:**")
                    st.json(msg_data['messages'])
        else:
            st.info("暂无消息记录")
    
    with tab2:
        st.markdown("### Chat Reports 历史")
        if st.session_state.debug_info['chat_reports']:
            # 准备表格数据
            table_data = []
            
            for report_idx, report in enumerate(st.session_state.debug_info['chat_reports']):
                for llm_call in report.get('llm_calls', []):
                    # LLM Call 行
                    llm_row = {
                        "对话": f"#{report_idx + 1}",
                        "类型": "LLM Call",
                        "查询": llm_call.get('query', '')[:50] + "..." if len(llm_call.get('query', '')) > 50 else llm_call.get('query', ''),
                        "耗时": llm_call.get('timecost', ''),
                        "Token使用": llm_call.get('token_usage', {}).get('total_tokens', 0),
                        "工具调用数": len(llm_call.get('tool_calls', [])),
                        "响应": llm_call.get('response', '')[:80] + "..." if len(llm_call.get('response', '')) > 80 else llm_call.get('response', '')
                    }
                    table_data.append(llm_row)
                    
                    # Tool Call 行
                    for tool_call in llm_call.get('tool_calls', []):
                        tool_row = {
                            "对话": f"#{report_idx + 1}",
                            "类型": "Tool Call",
                            "查询": tool_call.get('name', ''),
                            "耗时": f"{tool_call.get('timecost', 0):.2f}s",
                            "Token使用": 0,  # 改为数字0而不是字符串"-"
                            "工具调用数": 0,  # 改为数字0而不是字符串"-"
                             "响应": str(tool_call.get('result', ''))[:80] + "..." if len(str(tool_call.get('result', ''))) > 80 else str(tool_call.get('result', ''))
                        }
                        table_data.append(tool_row)
            
            if table_data:
                # 创建表格
                import pandas as pd
                df = pd.DataFrame(table_data)
                
                # 显示表格
                st.dataframe(
                    df,
                    width='stretch',  # 替换 use_container_width=True
                    hide_index=True,
                    column_config={
                        "对话": st.column_config.TextColumn("对话", width="small"),
                        "类型": st.column_config.TextColumn("类型", width="small"),
                        "查询": st.column_config.TextColumn("查询/工具名", width="small"),
                        "耗时": st.column_config.TextColumn("耗时", width="small"),
                        "Token使用": st.column_config.NumberColumn("Token", width="small", format="%d"),
                        "工具调用数": st.column_config.NumberColumn("工具数", width="small", format="%d"),
                        "响应": st.column_config.TextColumn("响应/结果", width="large")
                    }
                )
                
                # 添加统计信息
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("总对话数", len(st.session_state.debug_info['chat_reports']))
                with col2:
                    llm_calls_count = sum(len(report.get('llm_calls', [])) for report in st.session_state.debug_info['chat_reports'])
                    st.metric("LLM调用数", llm_calls_count)
                with col3:
                    tool_calls_count = sum(len(tool_call.get('tool_calls', [])) for report in st.session_state.debug_info['chat_reports'] for tool_call in report.get('llm_calls', []))
                    st.metric("工具调用数", tool_calls_count)
                with col4:
                    total_tokens = sum(
                        llm_call.get('token_usage', {}).get('total_tokens', 0) 
                        for report in st.session_state.debug_info['chat_reports'] 
                        for llm_call in report.get('llm_calls', [])
                    )
                    st.metric("总Token数", total_tokens)
            else:
                st.info("暂无聊天报告数据")
        else:
            st.info("暂无聊天报告")
    
    with tab3:
        st.markdown("### Chain of Thought (COT) 推理信息")
        
        # 从 chat_reports 中提取推理信息
        reasoning_data = []
        for report_idx, report in enumerate(st.session_state.debug_info['chat_reports']):
            for llm_call_idx, llm_call in enumerate(report.get('llm_calls', [])):
                reasoning_content = llm_call.get('reasoning_content', '')
                if reasoning_content and reasoning_content.strip():
                    reasoning_data.append({
                        '对话': f"#{report_idx + 1}",
                        'LLM调用': f"#{llm_call_idx + 1}",
                        '推理内容': reasoning_content,
                        '查询': llm_call.get('query', '')[:100] + "..." if len(llm_call.get('query', '')) > 100 else llm_call.get('query', ''),
                        '响应': llm_call.get('response', '')[:100] + "..." if len(llm_call.get('response', '')) > 100 else llm_call.get('response', ''),
                        '耗时': llm_call.get('timecost', ''),
                        'Token使用': llm_call.get('token_usage', {}).get('total_tokens', 0)
                    })
        
        if reasoning_data:
            # 显示统计信息
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("包含推理的LLM调用", len(reasoning_data))
            with col2:
                total_reasoning_tokens = sum(item['Token使用'] for item in reasoning_data)
                st.metric("推理相关Token", total_reasoning_tokens)
            with col3:
                avg_reasoning_length = sum(len(item['推理内容']) for item in reasoning_data) / len(reasoning_data)
                st.metric("平均推理长度", f"{avg_reasoning_length:.0f}字符")
            
            st.markdown("---")
            
            # 显示推理内容
            for i, item in enumerate(reasoning_data):
                with st.expander(f"推理 #{i+1} - 对话{item['对话']} LLM调用{item['LLM调用']}"):
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        st.markdown("**查询内容:**")
                        st.text_area("查询内容", item['查询'], height=100, key=f"query_{i}", disabled=True, label_visibility="collapsed")
                        
                        st.markdown("**响应内容:**")
                        st.text_area("响应内容", item['响应'], height=100, key=f"response_{i}", disabled=True, label_visibility="collapsed")
                    
                    with col2:
                        st.markdown("**推理过程:**")
                        st.text_area("推理过程", item['推理内容'], height=200, key=f"reasoning_{i}", disabled=True, label_visibility="collapsed")
                        
                        st.markdown("**性能指标:**")
                        st.write(f"⏱️ 耗时: {item['耗时']}")
                        st.write(f"🔢 Token使用: {item['Token使用']}")
                        st.write(f"📝 推理长度: {len(item['推理内容'])} 字符")
        else:
            st.info("暂无推理信息")
            st.markdown("""
            **说明:**
            - 推理信息来自LLM的 `reasoning_content` 字段
            - 如果模型不支持推理内容输出，此区域将显示为空
            - 当前使用的模型可能不支持推理过程展示
            """)

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
    
    # 添加调试区域
    create_debug_area()

if __name__ == "__main__":
    main()
