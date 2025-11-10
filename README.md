# Verum - 新闻溯源系统

一个基于 Streamlit 的新闻溯源分析平台，帮助用户追踪新闻来源、验证信息真实性。

## 功能特性

- 🔍 **智能搜索**: 支持新闻主题搜索和链接查询
- 🧠 **思考模式切换**: 深度思考（全面分析）和浅度思考（快速响应）两种模式
- ⚖️ **新闻真假判别**: 自动判别新闻真实性，提供判定结果和详细摘要
- 📅 **时间线生成**: 按时间线组织搜索结果，清晰展示事件发展脉络
- 💬 **社区讨论**: 聚合各大平台相关讨论
- 📚 **历史记录**: 保存搜索历史便于回溯

## 项目结构

```
verum-frontend/
├── app.py                          # 主入口（首页）
├── pages/
│   └── result.py              # 结果展示页面
├── components/                      # 可复用组件
│   ├── sidebar.py                   # 侧边栏组件
│   ├── search_box.py                # 搜索框组件
│   └── recommendations.py           # 推荐组件
├── models/
│   └── data_models.py               # 数据模型定义
├── api/
│   ├── mock_api.py                  # Mock API 层（历史、推荐等）
│   ├── api_client.py                # Query Engine API 客户端
│   └── README.md                     # API 使用说明
├── mock_data/
│   └── sample_data.py               # Mock 数据
├── utils/
│   └── state.py                     # Session State 管理
├── examples/                        # 使用示例
│   ├── README.md                    # 示例说明
│   └── query_frontend.html          # API 使用示例页面
├── @bettafish/                      # Git 子模块（BettaFish 引擎集合）
│   ├── QueryEngine/                 # 查询引擎（深度思考模式）
│   ├── MediaEngine/                 # 媒体引擎
│   ├── InsightEngine/               # 洞察引擎
│   ├── requirements.txt            # Submodule 依赖
│   └── config.py                    # Submodule 配置文件
├── @deepsearchagent_demo/           # Git 子模块（深度搜索代理演示）
│   ├── src/                         # 源代码
│   ├── requirements.txt            # Submodule 依赖
│   └── config.py                    # Submodule 配置文件
├── backend/                         # 后端服务
│   ├── api_server.py               # API 服务器主文件
│   ├── timeline_service.py         # 时间线服务
│   └── verification_service.py     # 新闻验证服务
├── .streamlit/
│   └── config.toml                  # Streamlit 配置
├── run.sh                           # Streamlit 启动脚本
├── run_api_server.sh                # API 服务启动脚本
└── requirements.txt                # 项目依赖
```

## 快速开始

### 1. 克隆项目并初始化 Submodule

项目依赖两个 Git Submodule，需要先初始化：

```bash
# 克隆项目（包含 submodule）
git clone --recurse-submodules https://github.com/your-repo/verum-frontend.git

# 如果已经克隆了项目，需要初始化 submodule
git submodule update --init --recursive
```

项目包含以下两个 submodule：

- **@bettafish**: 包含 QueryEngine、MediaEngine、InsightEngine 等核心引擎
- **@deepsearchagent_demo**: 包含深度搜索代理的演示代码

### 2. 设置 Submodule 依赖

#### 2.1 设置 @bettafish Submodule

进入 `@bettafish` 目录并安装依赖：

```bash
cd @bettafish
pip install -r requirements.txt
cd ..
```

**配置环境变量**（在项目根目录创建 `.env` 文件或在 `@bettafish` 目录创建 `.env` 文件）：

```bash
# Query Engine 配置（必需）
QUERY_ENGINE_API_KEY=your_api_key_here
QUERY_ENGINE_BASE_URL=https://api.deepseek.com  # 可选，默认值
QUERY_ENGINE_MODEL_NAME=deepseek-chat  # 可选，默认值

# Tavily 搜索 API（必需）
TAVILY_API_KEY=your_tavily_api_key_here

# 其他引擎配置（可选，根据需要使用）
INSIGHT_ENGINE_API_KEY=your_insight_api_key
MEDIA_ENGINE_API_KEY=your_media_api_key
```

#### 2.2 设置 @deepsearchagent_demo Submodule

进入 `@deepsearchagent_demo` 目录并安装依赖：

```bash
cd @deepsearchagent_demo
pip install -r requirements.txt
cd ..
```

**配置环境变量**（在项目根目录的 `.env` 文件中添加，或创建 `@deepsearchagent_demo/.env`）：

```bash
# DeepSearchAgent 配置（已在 @bettafish 配置中设置，可复用）
DEEPSEEK_API_KEY=your_deepseek_api_key
TAVILY_API_KEY=your_tavily_api_key
```

### 3. 安装主项目依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

在项目根目录创建 `.env` 文件（如果还没有），配置必要的 API 密钥：

```bash
# Query Engine API 配置（必需）
QUERY_ENGINE_API_KEY=your_api_key_here
QUERY_ENGINE_BASE_URL=https://api.deepseek.com  # 可选
QUERY_ENGINE_MODEL_NAME=deepseek-chat  # 可选

# Tavily 搜索 API（必需）
TAVILY_API_KEY=your_tavily_api_key_here

# API 服务地址（可选）
QUERY_API_BASE_URL=http://localhost:6001
```

### 5. 启动后端 API 服务

在运行前端之前，需要先启动后端 API 服务：

```bash
./run_api_server.sh
```

或者手动启动：

```bash
cd backend
python api_server.py
```

API 服务将在 `http://localhost:6001` 上运行。

### 6. 运行前端项目

在新的终端窗口中：

```bash
streamlit run app.py
```

或者使用启动脚本：

```bash
./run.sh
```

### 7. 访问应用

浏览器自动打开 `http://localhost:8501`

## 使用说明

### 首页

1. 选择思考模式：深度思考（更全面，耗时较长）或浅度思考（快速响应）
2. 在搜索框输入新闻主题或粘贴新闻链接
3. 点击"搜索"按钮或选择热点话题
4. 查看侧边栏历史记录

### 结果展示页

- **模块加载**:

  - 两个模块顺序加载：报告、外部讨论
  - 使用 MockAPI 的 `wait_for_*` 方法，类似 `query_api.wait_for_result`
  - 每个模块独立显示标题、进度条和状态文本
  - 模块完成后显示✅或❌标记
  - 所有模块完成后自动刷新显示最终结果
- **左侧**:

  - 新闻真假判别结果（判定结果和详细摘要）
  - AI 分析报告标签页
  - 新闻原文标签页（针对链接查询）
- **右侧**:

  - 新闻时间线（按日期组织的事件和参考文章）
  - 社交平台讨论链接

## API 接口说明

### Query Engine API（已接入）

基于异步任务模型的查询接口：

#### 1. 创建查询任务

```python
POST /api/query
{
  "query": "你的问题",
  "mode": "deep"  # 或 "quick"（可选，默认为 "deep"）
}

# 返回
{
  "success": true,
  "task_id": "query_1234567890",
  "task": {...}
}
```

#### 2. 获取任务状态

```python
GET /api/query/<task_id>/status

# 返回
{
  "success": true,
  "task": {
    "status": "pending|running|completed|error",
    "progress": 0-100
  }
}
```

#### 3. 获取查询结果

```python
GET /api/query/<task_id>

# 返回
{
  "success": true,
  "report": "报告内容（Markdown格式）",
  "verification": {
    "verdict": "真/假/部分真实/无法确定",
    "summary": "判别摘要"
  }
}
```

#### 4. 获取时间线数据

```python
GET /api/timeline/query/<task_id>

# 返回
{
  "success": true,
  "timeline": [...],
  "total_sources": 15,
  "date_range": {
    "start": "2025.08.08",
    "end": "2025.10.09"
  }
}
```

#### 5. 获取判别结果

```python
GET /api/verification/query/<task_id>

# 返回
{
  "success": true,
  "verification": {
    "verdict": "真/假/部分真实/无法确定",
    "summary": "判别摘要",
    "timestamp": "2025-11-09 12:00:00"
  }
}
```

### 其他接口（使用 Mock 数据）

- 获取历史记录
- 获取推荐新闻
- 外部讨论链接

## 技术栈

- **前端框架**: Streamlit 1.31.0
- **语言**: Python 3.11
- **数据处理**: Pandas
- **HTTP 请求**: Requests

## Query Engine API 服务

项目包含了一个独立的 Query Engine API 服务，基于 Flask 提供 REST API 接口。该服务依赖两个 submodule：

- **@bettafish/QueryEngine**: 用于深度思考模式（deep mode）
- **@deepsearchagent_demo**: 用于浅度思考模式（quick mode）

### 启动 API 服务

```bash
./run_api_server.sh
```

服务将在 `http://localhost:6001` 上运行

**注意**: 启动 API 服务前，请确保：

1. 已正确初始化并配置好两个 submodule（见"快速开始"部分）
2. 已设置必要的环境变量（`QUERY_ENGINE_API_KEY`、`TAVILY_API_KEY` 等）

### API 文档

详见 `backend/api_server.py` 和 `examples/README.md`

## 故障排除

### Submodule 相关问题

**问题**: 运行时报错 `ModuleNotFoundError: No module named 'QueryEngine'` 或类似错误

**解决方案**:

1. 确认 submodule 已正确初始化：

   ```bash
   git submodule status
   ```

   应该看到两个 submodule 都有提交哈希值
2. 如果 submodule 显示为空，重新初始化：

   ```bash
   git submodule update --init --recursive
   ```
3. 确认 submodule 的依赖已安装：

   ```bash
   cd @bettafish && pip install -r requirements.txt && cd ..
   cd @deepsearchagent_demo && pip install -r requirements.txt && cd ..
   ```

**问题**: API 服务启动失败，提示缺少 API Key

**解决方案**:

1. 确认已在项目根目录创建 `.env` 文件
2. 确认已设置以下必需的环境变量：
   - `QUERY_ENGINE_API_KEY`
   - `TAVILY_API_KEY`
3. 检查环境变量是否正确加载（可以在 Python 中测试）：
   ```python
   import os
   from dotenv import load_dotenv
   load_dotenv()
   print(os.getenv('QUERY_ENGINE_API_KEY'))
   ```

**问题**: Submodule 更新后代码不工作

**解决方案**:

```bash
# 更新所有 submodule 到最新版本
git submodule update --remote --recursive

# 或者更新特定 submodule
cd @bettafish
git pull origin main
cd ..
```

## 后续开发计划

- [X] 接入真实查询 API（Query Engine API 已完成）
- [X] 思考模式切换（深度/浅度）
- [X] 新闻真假判别功能
- [X] 时间线生成功能
- [ ] 接入其他引擎 API（讨论等）
- [ ] 添加用户认证系统
- [ ] 移动端适配优化
- [ ] 添加数据导出功能
- [ ] 多语言支持

## API 集成状态

- **查询功能**: ✅ 已接入真实 API (`api/api_client.py`)
- **思考模式切换**: ✅ 支持深度/浅度两种模式
- **新闻真假判别**: ✅ 已集成判别服务
- **时间线生成**: ✅ 已集成时间线服务
- **其他功能**: 🔄 使用 Mock 数据 (`api/mock_api.py`)

前端通过 `api/api_client.py` 调用后端查询服务，其他功能暂时使用 Mock 数据演示。

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License
