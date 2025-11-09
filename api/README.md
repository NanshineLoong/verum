# API 模块说明

本目录包含前端与后端的 API 接口层。

## 文件说明

### `api_server.py` - 后端 API 服务器

基于 Flask 的 Query Engine API 服务器，提供异步任务管理功能。

**运行方式：**

```bash
cd /Users/nanshine/PlayGround/verum-frontend
./run_query_api.sh
```

**服务端口：** `6001`

**API 端点：**

- `POST /api/query` - 创建查询任务
- `GET /api/query/<task_id>/status` - 获取任务状态
- `GET /api/query/<task_id>` - 获取任务结果
- `GET /api/verification/query/<task_id>` - 获取判别结果
- `GET /api/timeline/query/<task_id>` - 获取时间线数据

### `query_api.py` - API 客户端

连接后端 Query Engine API 的 Python 客户端。

**主要类：**

- `QueryAPIClient`: API 客户端类

**主要方法：**

```python
from api.query_api import query_api

# 创建查询任务（支持深度/浅度思考模式）
task_data = query_api.create_query_task("你的问题", mode="deep")  # 或 "quick"
task_id = task_data['task_id']

# 轮询任务状态
task_status = query_api.get_task_status(task_id)

# 获取任务结果
result = query_api.get_task_result(task_id)

# 或者使用同步等待方法（会自动轮询）
report = query_api.wait_for_result(
    task_id, 
    progress_callback=lambda status, progress: print(f"{status}: {progress}%")
)

# 获取判别结果
verification = query_api.get_verification(task_id)

# 获取时间线数据
timeline = query_api.get_timeline(task_id)
```

**配置：**

通过环境变量 `QUERY_API_BASE_URL` 配置 API 地址：

```bash
export QUERY_API_BASE_URL="http://localhost:6001"
```

### `mock_api.py` - Mock API

模拟其他未接入的后端接口，提供测试数据。

**提供的功能：**

- 历史记录
- 推荐新闻
- 溯源图数据
- 用户反馈
- 外部讨论链接

## 使用流程

### 1. 启动后端 API 服务

```bash
./run_query_api.sh
```

确保服务在 `http://localhost:6001` 运行。

### 2. 启动前端应用

```bash
streamlit run app.py
```

### 3. 测试查询功能

1. 在首页搜索框输入查询内容
2. 点击"搜索"按钮
3. 查看进度条显示任务状态
4. 等待分析完成后查看结果

## API 集成状态

### ✅ 已接入真实 API

- **查询分析**: 通过 `query_api.py` 调用后端服务
- **思考模式切换**: 支持深度思考（deep）和浅度思考（quick）两种模式
- **新闻真假判别**: 自动判别新闻真实性，提供判定结果和摘要
- **时间线生成**: 从搜索结果提取时间线，按日期组织事件

### 🔄 使用 Mock 数据

- 历史记录
- 推荐新闻
- 外部讨论

## 故障排查

### 问题：无法连接到 API 服务器

**解决方案：**

1. 检查 API 服务是否运行：`curl http://localhost:6001/`
2. 检查防火墙设置
3. 检查环境变量 `QUERY_API_BASE_URL` 是否正确

### 问题：任务执行失败

**解决方案：**

1. 检查 `@bettafish/.env` 中的 API 密钥配置
2. 查看 API 服务器日志
3. 确保 `QUERY_ENGINE_API_KEY` 和 `TAVILY_API_KEY` 已正确设置

### 问题：进度显示卡住

**解决方案：**

1. 刷新页面重试
2. 检查网络连接
3. 查看浏览器控制台是否有错误

## 新功能说明

### 思考模式切换

系统支持两种思考模式：

- **深度思考（deep）**: 使用 QueryEngine，进行更全面深入的分析，耗时较长，适合复杂查询
- **浅度思考（quick）**: 使用 DeepSearchAgent-Demo，快速响应，适合简单查询

在搜索框组件中可以选择模式，创建任务时会传递 `mode` 参数。

### 新闻真假判别

自动对查询结果进行真假判别，提供：

- **判定结果**: 真/假/部分真实/无法确定
- **判别摘要**: 详细的判别依据和分析

判别结果会在右侧栏展示，使用醒目的颜色标识。

### 时间线功能

从搜索结果中提取时间信息，按时间线组织：

- 按日期倒序展示（最新的在前）
- 每个日期下按相关度排序
- 显示参考文章、网站来源、相关度评分
- 提供时间范围和总文章数统计

时间线数据会在右侧栏展示，替代或补充原有的溯源图。

## 未来扩展

当其他后端 API 就绪时，可以参考 `query_api.py` 的实现方式：

1. 创建对应的 API 客户端类
2. 实现必要的 HTTP 请求方法
3. 在前端组件中替换对应的 `MockAPI` 调用
4. 保持数据模型接口一致

