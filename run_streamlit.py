#!/usr/bin/env python3
"""
启动Streamlit应用的脚本
"""

import subprocess
import sys
import os

def main():
    """启动Streamlit应用"""
    # 确保在正确的目录中
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # 检查环境变量文件
    if not os.path.exists('.env'):
        print("⚠️  警告: 未找到.env文件")
        print("请确保在项目根目录下创建.env文件，包含以下内容:")
        print("DASHSCOPE_API_KEY=your_api_key_here")
        print("DASHSCOPE_API_URL=your_api_url_here")
        print()
    
    # 启动Streamlit应用
    try:
        print("🚀 启动AI对话机器人应用...")
        print("📱 应用将在浏览器中打开: http://localhost:8501")
        print("⏹️  按 Ctrl+C 停止应用")
        print()
        
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 应用已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

if __name__ == "__main__":
    main()
