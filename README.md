# 智能穿搭助手

基于 LangGraph 的智能穿搭推荐系统，根据天气和衣橱为用户提供个性化穿搭建议。

## 项目简介

智能穿搭助手是一个基于 Agentic AI 的穿搭推荐系统，具有以下核心功能：
- 实时天气查询（和风天气 API）
- 衣橱管理（增删改查）
- 基于天气和场合的穿搭建议
- 多轮对话支持

## 方向

方向一：Agentic AI 原生开发

## 技术栈

- **AI IDE**: Trae CN
- **LLM**: DeepSeek API (deepseek-flash)
- **框架**: LangGraph, LangChain
- **工具**: 和风天气 API
- **存储**: JSON 文件
- **语言**: Python 3.10+
- **部署**: 本地运行 / Streamlit Cloud（可选）

## 开源项目引用

本项目使用了以下开源项目，感谢开源社区的贡献：

- **LangGraph** - Agent编排框架
  - GitHub: https://github.com/langchain-ai/langgraph
  - License: MIT License
  
- **LangChain** - LLM应用开发框架
  - GitHub: https://github.com/langchain-ai/langchain
  - License: MIT License
  
- **Streamlit** - Web应用框架
  - GitHub: https://github.com/streamlit/streamlit
  - License: Apache License 2.0
  
- **Pydantic** - 数据验证库
  - GitHub: https://github.com/pydantic/pydantic
  - License: MIT License
  
- **python-dotenv** - 环境变量管理
  - GitHub: https://github.com/theskumar/python-dotenv
  - License: BSD License

## 目录结构

```
cs599-project/
├── .env                      # 环境变量（API Keys）
├── requirements.txt          # 依赖列表
├── README.md                 # 项目说明
└── src/
    ├── main.py               # CLI 入口
    ├── web_app.py            # Streamlit 入口（增强版）
    ├── config.py             # 环境变量与配置
    ├── agents/
    │   ├── main_controller.py   # 主控 Agent：LangGraph StateGraph 定义 + 节点函数
    │   └── fashion_advisor.py   # 时尚顾问 Agent：搭配生成 Prompt + 调用
    ├── tools/
    │   ├── weather.py           # 天气工具：和风天气 API + 城市代码转换 + 缓存
    │   └── wardrobe.py          # 衣橱工具：JSON 读写 + 规则过滤检索
    ├── models/
    │   └── schemas.py           # Pydantic / TypedDict 模型定义
    ├── utils/
    │   ├── cache.py             # 天气缓存（TTL 10分钟）
    │   └── logger.py            # 日志记录
    └── storage/
        └── wardrobe.json        # 衣橱数据（运行时自动创建）
```

## 环境搭建

### 1. 依赖安装

```bash
cd cs599-project
pip install -r requirements.txt
```

### 2. 环境变量配置

编辑 `.env` 文件，填入您的 API Key：

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
HEWEATHER_KEY=your_heweather_api_key_here
```

**API Key 获取方式：**
- DeepSeek: https://platform.deepseek.com/
- 和风天气: https://dev.qweather.com/

### 3. 启动步骤

```bash
cd cs599-project
streamlit run src/web_app.py --server.headless true --server.runOnSave true
```

## 使用示例

```
欢迎使用智能穿搭助手！

您：今天天气怎么样
助手：当前天气：晴，温度 25°C，舒适温度，穿长袖衬衫或薄卫衣

您：帮我看看穿什么
助手：思考中...
当前天气：晴，温度 25°C
推荐搭配：白衬衫 + 牛仔裤 + 运动鞋
理由：25°C适合穿轻薄透气的衣物，白衬衫搭配牛仔裤休闲又时尚

您：今天下午有个面试，穿什么合适
助手：思考中...
当前天气：晴，温度 25°C
推荐搭配：白衬衫 + 深蓝西裤 + 黑皮鞋
理由：面试场合需要正式着装，白衬衫配西裤显得专业稳重
```

## 核心功能

### 1. 天气查询
- 实时获取指定城市天气
- 温度、湿度、风速、紫外线指数
- 自动生成穿搭提示

### 2. 衣橱管理
- 添加衣物（名称、类别、颜色、材质、温度范围、场合标签）
- 删除衣物
- 查看所有衣物
- 更新衣物信息

### 3. 穿搭建议
- 基于天气和场合的智能推荐
- 从衣橱中选择合适的衣物
- 提供搭配理由

## 项目状态

- [x] Proposal - 项目提案与架构设计
- [x] MVP - 核心功能实现（v0.1）
- [x] Final - 最终版本完成

## 许可证

MIT License
