#!/bin/bash

# Verum 启动脚本

echo "🚀 启动 Verum 新闻溯源系统..."

# 检查依赖
if ! command -v streamlit &> /dev/null
then
    echo "⚠️  未检测到 streamlit，正在安装依赖..."
    pip install -r requirements.txt
fi

# 运行应用
streamlit run app.py

