# 智能穿搭助手 Agent - 技术规格文档（SPEC）
**版本**：v1.0  
**用途**：AI IDE 代码生成唯一事实来源（Source of Truth）

---

## 1. 功能规格（按优先级）

### 1.1 Must Have（MVP 必备）
- 天气查询：调用和风天气 API，获取温度、天气状况、湿度、风速、紫外线指数
- 基础穿搭建议：基于温度区间的通用穿衣规则（如 &lt;10°C 建议羽绒服）
- 自然语言 CLI 交互：用户输入自然语言，系统理解并响应
- 环境变量配置：所有 API Key 通过 `.env` 注入，禁止硬编码

### 1.2 Should Have（增强版）
- 衣橱管理：JSON 文件持久化，支持增删改查
- 个性化推荐：从衣橱中检索真实衣物，基于规则过滤（温度范围 + 场合标签）
- 场合适配：识别用户输入中的隐含场合（面试/约会/运动/工作），调整推荐策略
- 多轮对话：基于 `chat_history` 支持连续追问（如"那明天呢"、"换正式一点"）

### 1.3 Could Have（时间充裕时）
- 偏好记忆：记录用户不喜欢的颜色/材质、偏好风格，自动排除
- 历史搭配记录：保存用户确认过的搭配方案
- 推荐反馈：点赞/点踩调整权重
- 向量语义检索：替换规则过滤为 Embedding 检索

### 1.4 Won't Have（本次不做）
- 社交分享、多用户系统、图像识别录入、移动端 App

---

## 2. 架构规格

### 2.1 架构模式
**主从式智能体架构**：LangGraph StateGraph 编排，2-Agent + 2-Tool。

- **主控 Agent**：意图分类、路由调度、状态管理、工具调用
- **时尚顾问 Agent**：综合天气+衣橱+场合，调用 LLM 生成最终建议
- **天气工具**：和风天气 API 封装（含城市代码转换 + 10分钟缓存）
- **衣橱工具**：JSON 文件 CRUD + 规则过滤检索

### 2.2 模块职责

**主控 Agent（Main Controller）**
- 接收用户输入，通过 LLM（deepseek-chat, temp=0.3）进行意图分类
- 意图类型：`outfit`（穿搭建议）、`weather`（天气查询）、`wardrobe`（衣橱管理）
- 穿搭链路：调用天气工具 → 调用衣橱工具 → 调用时尚顾问 Agent → 返回
- 天气链路：调用天气工具 → 格式化返回
- 衣橱链路：解析增删改查 → 调用衣橱工具 → 返回操作结果
- 维护 `chat_history` 实现多轮上下文

**时尚顾问 Agent（Fashion Advisor）**
- 接收 `weather_data` + `wardrobe_candidates` + `occasion`
- 调用 LLM（deepseek-chat, temp=0.5）生成穿搭建议
- System Prompt 硬约束：只能从候选列表选衣物、禁止编造、必须考虑天气和场合、必须给出推荐理由

**天气工具（Weather Tool）**
- 输入：`city(str)`
- 内部：城市名称 → 城市代码（内置映射表 + GeoAPI 兜底）→ 和风天气 API → TTL 缓存（10分钟）
- 输出：`WeatherData`（含 `temp`, `condition`, `humidity`, `wind_speed`, `uvi`, `tips`）

**衣橱工具（Wardrobe Tool）**
- 数据文件：`storage/wardrobe.json`（不存在时自动初始化 `[]`）
- 检索规则：`suitable_temp_min &lt;= temp &lt;= suitable_temp_max` 且 `occasion` 在 `occasion_tags` 中
- 默认返回 8 条候选，不足时触发降级策略（放宽场合标签）

### 2.3 数据流（以"面试穿搭"为例）

1. 用户输入 → 主控 Agent → LLM 意图分类 → `intent="outfit"`, `occasion="interview"`
2. 主控 Agent → 天气工具 → 和风天气 API → 返回 25°C 晴 + 解读标签
3. 主控 Agent → 衣橱工具 → 规则过滤（温度覆盖25°C + 场合含interview/formal）→ 返回 [白衬衫, 深蓝西裤, 黑皮鞋]
4. 主控 Agent → 时尚顾问 Agent → LLM 综合生成 → "建议白衬衫+深蓝西裤+黑皮鞋，25°C晴天正式且舒适"
5. 返回用户，交互记录追加到 `chat_history`

---

## 3. 接口规格

### 3.1 内部工具 API（Python 函数签名）

所有工具使用 `@tool` 装饰器注册，返回 Dict 或 List[Dict]。

```python
# 工具一：获取天气
def get_weather(city: str) -&gt; dict:
    """
    返回: {
        "temp": int,           # 摄氏温度
        "condition": str,      # 晴/雨/多云
        "humidity": int,       # 相对湿度 %
        "wind_speed": str,     # 微风/强风
        "uvi": int,            # 紫外线指数
        "tips": str            # 穿搭解读，如"舒适温度，注意防晒"
    }
    """

# 工具二：检索衣橱
def search_wardrobe(
    temp: int,
    condition: str,
    occasion: str = "casual",
    limit: int = 8
) -&gt; list[dict]:
    """
    返回候选衣物列表，每个元素:
    {
        "id": str,              # UUID
        "name": str,
        "category": str,        # 上衣/裤子/外套/鞋
        "color": str,
        "material": str,
        "suitable_temp_min": int,
        "suitable_temp_max": int,
        "occasion_tags": list[str]   # ["work", "formal"]
    }
    """
    # 过滤规则: temp 在 [min, max] 内，且 occasion 在 occasion_tags 中

# 工具三：添加衣物
def add_clothing(
    name: str,
    category: str,
    color: str,
    material: str,
    suitable_temp_min: int = 0,
    suitable_temp_max: int = 40,
    occasion_tags: list[str] = None
) -&gt; dict:
    """
    自动生成 UUID 作为 id
    返回: {"success": bool, "id": str, "error": str}
    """

# 工具四：删除衣物
def delete_clothing(clothing_id: str) -&gt; dict:
    """返回: {"success": bool, "error": str}"""

# 工具五：查询所有衣物
def list_wardrobe() -&gt; list[dict]:
    """返回全部衣物列表，无过滤"""

# 工具六：更新衣物
def update_clothing(
    clothing_id: str,
    name: str = None,
    category: str = None,
    color: str = None,
    material: str = None,
    suitable_temp_min: int = None,
    suitable_temp_max: int = None,
    occasion_tags: list[str] = None
) -&gt; dict:
    """只更新提供的字段，不提供的保持原值。返回: {"success": bool, "error": str}"""
```

### 3.2 预留接口（增强版 / Could Have）

```python
# 工具七~九：偏好工具（本次不实现，预留）
def save_preference(preference_type: str, value: str) -> dict: ...
def get_preferences(preference_type: str = None) -> dict: ...
def delete_preference(preference_type: str, value: str) -> dict: ...
```

### 3.3 外部 API 依赖

**和风天气 API**

- 环境变量：`HEWEATHER_KEY`
- 请求：HTTP GET，带 `key` 和 `location`（城市代码）
- 响应：JSON，提取 `now.temp`, `now.text`, `now.humidity`, `now.windScale`, `now.uvIndex`
- 限流：免费版 QPM 限制，实现 10 分钟 TTL 缓存

**DeepSeek API**

- 环境变量：`DEEPSEEK_API_KEY`
- 接口：`https://api.deepseek.com/v1/chat/completions`（OpenAI 兼容）
- 模型：`deepseek-chat`（DeepSeek-V3）
- 意图分类：`temperature=0.3`，要求返回可解析 JSON
- 搭配生成：`temperature=0.5`，System Prompt 含硬约束

------

## 4. 状态管理（LangGraph State）

### 4.1 状态对象字段（TypedDict）

| 字段名                | 类型             | 说明                                                        | 写入节点                           |
| :-------------------- | :--------------- | :---------------------------------------------------------- | :--------------------------------- |
| `user_input`          | `str`            | 用户原始输入                                                | entry_node                         |
| `intent`              | `Optional[str]`  | 意图：`outfit`/`weather`/`wardrobe`/`preference`            | intent_classifier                  |
| `weather_data`        | `Optional[dict]` | 结构化天气 + 解读标签                                       | weather_tool_node                  |
| `occasion`            | `Optional[str]`  | 场合：`casual`/`work`/`interview`/`date`/`sports`/`formal`  | intent_classifier                  |
| `wardrobe_candidates` | `List[dict]`     | 候选衣物列表                                                | wardrobe_search_node               |
| `preferences`         | `Optional[dict]` | 用户偏好（增强版预留）                                      | preference_tool_node               |
| `final_output`        | `Optional[str]`  | 系统最终回复文本                                            | fashion_advisor_node / output_node |
| `chat_history`        | `List[dict]`     | 多轮对话历史，格式 `[{"role":"user","content":"..."}, ...]` | output_node                        |
| `error_info`          | `Optional[str]`  | 异常信息                                                    | error_handler                      |
| `session_id`          | `str`            | 会话唯一标识（UUID）                                        | entry_node                         |
| `timestamp`           | `str`            | 请求时间戳（ISO 格式）                                      | entry_node                         |

### 4.2 状态流转规则

- **entry_node**：初始化 `user_input`, `session_id`, `timestamp`，清空 `error_info`
- **intent_classifier**：读取 `user_input` + `chat_history`，写入 `intent`, `occasion`
- **weather_tool_node**：读取 `user_input` 中的城市（或默认），写入 `weather_data`
- **wardrobe_search_node**：读取 `weather_data.temp` + `occasion`，写入 `wardrobe_candidates`
- **fashion_advisor_node**：读取 `weather_data` + `wardrobe_candidates` + `occasion` + `preferences`，写入 `final_output`
- **output_node**：读取 `final_output`，追加到 `chat_history`，返回给用户

------

## 5. 数据模型

### 5.1 Clothing（Pydantic）

```python
class Clothing(BaseModel):
    id: str                    # UUID4
    name: str                  # 如"白衬衫"
    category: str              # 上衣/裤子/外套/鞋/配饰
    color: str                 # 如"白色"
    material: str              # 如"棉"
    suitable_temp_min: int = 0
    suitable_temp_max: int = 40
    occasion_tags: List[str] = ["casual"]
```

### 5.2 WeatherData（TypedDict）

```python
class WeatherData(TypedDict):
    temp: int
    condition: str
    humidity: int
    wind_speed: str
    uvi: int
    tips: str
```

### 5.3 衣橱 JSON 格式示例

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "白衬衫",
    "category": "上衣",
    "color": "白色",
    "material": "棉",
    "suitable_temp_min": 20,
    "suitable_temp_max": 35,
    "occasion_tags": ["work", "formal", "interview"]
  }
]
```

------

## 6. 非功能需求

| 类别       | 要求                                                         |
| :--------- | :----------------------------------------------------------- |
| **性能**   | 简单查询 < 5s，复杂查询 < 10s，单次 LLM < 3s，衣橱检索 < 500ms |
| **可用性** | API 失败时返回友好提示，不崩溃；城市不存在时提示检查拼写     |
| **安全**   | API Key 全部走环境变量，衣橱数据仅本地存储                   |
| **可扩展** | 存储层和检索层使用抽象接口，JSON 可替换为 SQLite/PostgreSQL，规则过滤可替换为向量检索 |
| **可观测** | 记录每次请求的天气 API 耗时、衣橱检索耗时、LLM 耗时、Token 消耗 |

------

## 7. 开发约束（给 AI IDE 的硬性要求）

1. **禁止硬编码密钥**：所有 API Key 必须 `os.getenv()` 读取，`.env` 文件不入版本库
2. **禁止编造衣物**：时尚顾问 Agent 的 Prompt 必须约束"只能从 `wardrobe_candidates` 中选择"
3. **意图分类必须返回 JSON**：LLM 输出必须是 `{"intent": "...", "occasion": "..."}` 格式，方便解析
4. **文件自动初始化**：`wardrobe.json` 不存在时自动创建空列表 `[]`，禁止因文件缺失报错
5. **异常不中断对话**：任何节点异常进入 `error_handler`，返回友好提示，StateGraph 继续运行到 `output_node`

------

## 8. 版本规划

表格

| 阶段       | 交付物               | 功能范围                                    |
| :--------- | :------------------- | :------------------------------------------ |
| **MVP**    | `main.py` + CLI      | 天气查询、基础穿搭建议、意图分类            |
| **增强版** | `app.py` + Streamlit | 衣橱 CRUD、规则过滤检索、场合适配、多轮对话 |
| **扩展**   | 预留接口实现         | 偏好记忆、向量检索、历史记录                |