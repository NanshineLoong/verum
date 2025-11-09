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
│   ├── query_api.py                 # Query Engine API 客户端
│   └── api_server.py                # Query Engine API 服务器
├── mock_data/
│   └── sample_data.py               # Mock 数据
├── utils/
│   └── state.py                     # Session State 管理
├── examples/                        # 使用示例
│   ├── README.md                    # 示例说明
│   └── query_frontend.html          # API 使用示例页面
├── @bettafish/                      # Git 子模块（各种引擎）
├── .streamlit/
│   └── config.toml                  # Streamlit 配置
├── run.sh                           # Streamlit 启动脚本
├── run_query_api.sh                 # API 服务启动脚本
└── requirements.txt                 # 项目依赖
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行项目

```bash
streamlit run app.py
```

### 3. 配置 API 地址（可选）

如果 Query Engine API 服务运行在非默认地址，可以设置环境变量：

```bash
export QUERY_API_BASE_URL="http://your-api-server:6001"
```

默认地址：`http://localhost:6001`

### 4. 访问应用

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
- **语言**: Python 3.8+
- **数据处理**: Pandas
- **HTTP 请求**: Requests

## Query Engine API 服务

项目现在包含了一个独立的 Query Engine API 服务，基于 Flask 提供 REST API 接口。

### 启动 API 服务

```bash
./run_query_api.sh
```

服务将在 `http://localhost:6001` 上运行

### API 文档

详见 `api/query_engine_server.py` 和 `examples/README.md`

### 示例页面

访问 http://localhost:6001/examples/query_frontend.html 查看使用示例

## 后续开发计划

- [x] 接入真实查询 API（Query Engine API 已完成）
- [x] 思考模式切换（深度/浅度）
- [x] 新闻真假判别功能
- [x] 时间线生成功能
- [ ] 接入其他引擎 API（讨论等）
- [ ] 添加用户认证系统
- [ ] 移动端适配优化
- [ ] 添加数据导出功能
- [ ] 多语言支持

## API 集成状态

- **查询功能**: ✅ 已接入真实 API (`api/query_api.py`)
- **思考模式切换**: ✅ 支持深度/浅度两种模式
- **新闻真假判别**: ✅ 已集成判别服务
- **时间线生成**: ✅ 已集成时间线服务
- **其他功能**: 🔄 使用 Mock 数据 (`api/mock_api.py`)

前端通过 `api/query_api.py` 调用后端查询服务，其他功能暂时使用 Mock 数据演示。

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License
