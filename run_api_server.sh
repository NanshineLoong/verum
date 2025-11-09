#!/bin/bash

# Query Engine API 服务启动脚本

echo "=========================================="
echo "  启动 Query Engine API 服务"
echo "=========================================="
echo ""

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 找不到 python3 命令"
    exit 1
fi

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# 检查必要的依赖
echo "📦 检查依赖..."
python3 -c "import flask, flask_cors, loguru" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  缺少必要的依赖，正在安装..."
    pip3 install -r requirements.txt
fi

# 检查 .env 文件
if [ ! -f "@bettafish/.env" ]; then
    echo ""
    echo "⚠️  警告: 未找到 @bettafish/.env 配置文件"
    echo "请确保设置以下环境变量："
    echo "  - QUERY_ENGINE_API_KEY"
    echo "  - TAVILY_API_KEY"
    echo ""
fi

# 启动 API 服务
echo ""
echo "🚀 启动 Query Engine API 服务..."
echo "📍 监听地址: http://0.0.0.0:6001"
echo "📄 示例页面: http://localhost:6001/examples/query_frontend.html"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

python3 api/api_server.py

