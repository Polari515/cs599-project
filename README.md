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

## 目录结构

```
cs599-project/
├── src/                     # 源代码目录
│   ├── agents/              # Agent 模块
│   │   ├── main_controller.py    # 主控 Agent（LangGraph StateGraph）
│   │   └── fashion_advisor.py    # 时尚顾问 Agent
│   ├── tools/               # 工具模块
│   │   ├── weather.py            # 天气查询工具
│   │   └── wardrobe.py           # 衣橱管理工具
│   ├── models/              # 数据模型
│   │   └── schemas.py            # Pydantic/TypedDict 模型
│   ├── utils/               # 工具函数
│   │   ├── cache.py              # TTL 缓存
│   │   └── logger.py             # 日志记录
│   ├── storage/             # 数据存储（运行时自动创建）
│   ├── config.py            # 配置管理
│   └── main.py              # CLI 入口
├── docs/                    # 项目文档
│   ├── spec.md              # 技术规格文档
│   ├── architecture.md      # 架构说明
│   └── CS599_大作业报告.docx   # 项目报告
├── .env                     # 环境变量配置
└── README.md                # 项目说明
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
cd src
python main.py
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

- [x] Proposal
- [x] MVP
- [ ] Final

## 许可证

MIT License
