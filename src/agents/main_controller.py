import os
import json
import re
import uuid
from datetime import datetime
from typing import Dict, Optional, List
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import ChatMessage
from models.schemas import AgentState, IntentResult
from tools.weather import get_weather
from tools.wardrobe import search_wardrobe, list_wardrobe, add_clothing, delete_clothing, update_clothing
from agents.fashion_advisor import FashionAdvisor


class MainController:
    """主控 Agent - LangGraph StateGraph 编排"""
    
    def __init__(self):
        self._init_llm()
        self._init_tools()
        self._build_graph()
    
    def _init_llm(self):
        """初始化 LLM 客户端"""
        api_key = os.getenv("DEEPSEEK_API_KEY")
        self.llm = ChatOpenAI(
            model="deepseek-v4-flash",
            temperature=0.3,
            api_key=api_key,
            base_url="https://api.deepseek.com/v1",
            max_tokens=512
        )
    
    def _init_tools(self):
        """初始化工具"""
        self.fashion_advisor = FashionAdvisor()
    
    def _build_graph(self):
        """构建 StateGraph"""
        self.graph = StateGraph(AgentState)
        
        self.graph.add_node("entry_node", self.entry_node)
        self.graph.add_node("intent_classifier", self.intent_classifier)
        self.graph.add_node("weather_tool_node", self.weather_tool_node)
        self.graph.add_node("wardrobe_search_node", self.wardrobe_search_node)
        self.graph.add_node("wardrobe_crud_node", self.wardrobe_crud_node)
        self.graph.add_node("fashion_advisor_node", self.fashion_advisor_node)
        self.graph.add_node("output_node", self.output_node)
        self.graph.add_node("error_handler", self.error_handler)
        
        self.graph.set_entry_point("entry_node")
        
        self.graph.add_edge("entry_node", "intent_classifier")
        
        self.graph.add_conditional_edges(
            "intent_classifier",
            self.route_by_intent,
            {
                "weather": "weather_tool_node",
                "wardrobe": "wardrobe_crud_node",
                "outfit": "weather_tool_node",
                "error": "error_handler"
            }
        )
        
        self.graph.add_conditional_edges(
            "weather_tool_node",
            self.route_after_weather,
            {
                "output_node": "output_node",
                "wardrobe_search_node": "wardrobe_search_node",
                "error_handler": "error_handler"
            }
        )
        self.graph.add_conditional_edges(
            "wardrobe_search_node",
            self.route_after_search,
            {
                "fashion_advisor_node": "fashion_advisor_node",
                "error_handler": "error_handler"
            }
        )
        self.graph.add_edge("wardrobe_crud_node", "output_node")
        self.graph.add_edge("fashion_advisor_node", "output_node")
        self.graph.add_edge("error_handler", "output_node")
        self.graph.add_edge("output_node", END)
        
        self.app = self.graph.compile()
    
    def entry_node(self, state: AgentState) -> AgentState:
        """接收输入，初始化状态"""
        return {
            **state,
            "session_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "error_info": None,
            "wardrobe_candidates": []
        }
    
    def intent_classifier(self, state: AgentState) -> AgentState:
        """LLM 意图分类 + 场合提取"""
        user_input = state.get("user_input", "")

        # 对明确的高频问句先走规则，避免 LLM 把天气查询误判成穿搭建议。
        rule_based_result = self._classify_intent_by_rules(user_input)
        if rule_based_result:
            return {**state, **rule_based_result}
        
        system_prompt = """
你是一个意图分类器，请严格按照以下规则分析用户输入并返回 JSON 格式结果。

意图类型判断规则：
1. weather（天气查询）：包含"天气"、"温度"、"冷"、"热"、"晴"、"雨"、"雪"等天气相关词汇
2. outfit（穿搭建议）：包含"穿什么"、"搭配"、"建议穿"等穿搭相关词汇
3. wardrobe（衣橱管理）：包含"添加"、"删除"、"查看"、"衣橱"等词汇

优先级：天气查询 > 衣橱管理 > 穿搭建议

意图类型示例：
- "今天天气怎么样" → weather
- "今天穿什么" → outfit
- "添加衣服" → wardrobe
- "北京温度" → weather
- "面试穿什么" → outfit
- "查看衣橱" → wardrobe

场合类型（仅在意图为 outfit 时填写）：
- casual: 休闲
- work: 工作
- interview: 面试
- date: 约会
- sports: 运动
- formal: 正式

城市名称（如果用户提到城市）：

输出格式：{"intent": "...", "occasion": "...", "city": "..."}
注意：occasion 和 city 可以为 null，如果不确定就填 null。
"""
        
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_input)
        ]
        
        try:
            response = self.llm.invoke(messages)
            print("\n" + "="*50)
            print(f"【调试信息】LLM 原始响应: {response.content}")
            print("="*50)
            result = json.loads(response.content)
            
            intent = result.get("intent", "outfit")
            occasion = result.get("occasion")
            city = result.get("city")
            print(f"【调试信息】意图分类结果: intent={intent}, occasion={occasion}, city={city}")
            print("="*50 + "\n")
            
            if occasion and occasion not in ["casual", "work", "interview", "date", "sports", "formal"]:
                occasion = "casual"
            
            return {
                **state,
                "intent": intent,
                "occasion": occasion,
                "_city": city
            }
        
        except json.JSONDecodeError:
            return {
                **state,
                "intent": "outfit",
                "occasion": "casual",
                "_city": None,
                "error_info": "意图解析失败，默认按穿搭建议处理"
            }
        except Exception as e:
            return {
                **state,
                "intent": "outfit",
                "occasion": "casual",
                "_city": None,
                "error_info": f"意图分类错误：{str(e)}"
            }

    def _classify_intent_by_rules(self, user_input: str) -> Optional[Dict]:
        """对明确表达做本地分类，减少对 LLM 的依赖。"""
        normalized = user_input.strip()
        if not normalized:
            return None

        weather_keywords = ["天气", "温度", "气温", "冷", "热", "晴", "雨", "雪", "下雨", "下雪", "几度", "多少度"]
        wardrobe_keywords = ["添加", "删除", "查看", "衣橱", "衣柜", "修改", "更新", "列表"]
        outfit_keywords = ["穿什么", "搭配", "建议穿", "怎么穿", "穿搭", "面试", "约会", "正式", "工作", "休闲", "运动"]

        if any(keyword in normalized for keyword in weather_keywords):
            return {
                "intent": "weather",
                "occasion": None,
                "_city": self._extract_city(normalized),
                "error_info": None,
            }

        if any(keyword in normalized for keyword in wardrobe_keywords):
            return {
                "intent": "wardrobe",
                "occasion": None,
                "_city": None,
                "error_info": None,
            }

        if any(keyword in normalized for keyword in outfit_keywords):
            return {
                "intent": "outfit",
                "occasion": self._infer_occasion(normalized),
                "_city": self._extract_city(normalized),
                "error_info": None,
            }

        return None

    def _extract_city(self, user_input: str) -> Optional[str]:
        """从输入中粗略提取城市名。"""
        city_match = re.search(r"([\u4e00-\u9fa5]{2,6})(?:天气|温度|气温)", user_input)
        if city_match:
            return city_match.group(1)
        return None

    def _infer_occasion(self, user_input: str) -> Optional[str]:
        """从常见描述中推断场合。"""
        occasion_map = {
            "面试": "interview",
            "约会": "date",
            "正式": "formal",
            "工作": "work",
            "通勤": "work",
            "运动": "sports",
            "休闲": "casual",
        }

        for keyword, occasion in occasion_map.items():
            if keyword in user_input:
                return occasion

        return "casual"
    
    def route_by_intent(self, state: AgentState) -> str:
        """根据意图路由到不同节点"""
        intent = state.get("intent")
        if intent == "weather":
            return "weather"
        elif intent == "wardrobe":
            return "wardrobe"
        elif intent == "outfit":
            return "outfit"
        else:
            return "error"
    
    def weather_tool_node(self, state: AgentState) -> AgentState:
        """调用天气工具"""
        city = state.get("_city") or "武汉"
        
        try:
            # 使用 invoke 方法调用工具
            weather_data = get_weather.invoke({"city": city})
            return {**state, "weather_data": weather_data, "error_info": None}
        except Exception as e:
            import traceback
            error_msg = f"天气查询失败：{str(e)}\n{traceback.format_exc()}"
            return {**state, "weather_data": None, "error_info": error_msg}
    
    def route_after_weather(self, state: AgentState) -> str:
        """天气查询后的路由"""
        intent = state.get("intent")
        if intent == "weather":
            return "output_node"
        elif intent == "outfit":
            return "wardrobe_search_node"
        else:
            return "error_handler"
    
    def wardrobe_search_node(self, state: AgentState) -> AgentState:
        """调用衣橱检索"""
        weather_data = state.get("weather_data", {})
        occasion = state.get("occasion", "casual")
        
        temp = weather_data.get("temp", 25)
        condition = weather_data.get("condition", "晴")
        
        try:
            # 使用 invoke 方法调用工具
            candidates = search_wardrobe.invoke({
                "temp": temp,
                "condition": condition,
                "occasion": occasion,
                "limit": 8
            })
            return {**state, "wardrobe_candidates": candidates, "error_info": None}
        except Exception as e:
            return {**state, "wardrobe_candidates": [], "error_info": f"衣橱检索失败：{str(e)}"}
    
    def route_after_search(self, state: AgentState) -> str:
        """衣橱检索后的路由"""
        if state.get("error_info"):
            return "error_handler"
        return "fashion_advisor_node"
    
    def wardrobe_crud_node(self, state: AgentState) -> AgentState:
        """执行衣橱增删改查"""
        user_input = state.get("user_input", "")
        
        try:
            if "添加" in user_input or "新增" in user_input:
                result = self._parse_add_clothing(user_input)
                return {**state, "final_output": result, "error_info": None}
            elif "删除" in user_input:
                result = self._parse_delete_clothing(user_input)
                return {**state, "final_output": result, "error_info": None}
            elif "查看" in user_input or "列表" in user_input:
                items = list_wardrobe.invoke({})
                if items:
                    result = "您的衣橱有以下衣物：\n" + "\n".join(
                        [f"{i+1}. {item['name']} ({item['category']}, {item['color']})" for i, item in enumerate(items)]
                    )
                else:
                    result = "您的衣橱是空的，请添加一些衣物。"
                return {**state, "final_output": result, "error_info": None}
            elif "修改" in user_input or "更新" in user_input:
                result = self._parse_update_clothing(user_input)
                return {**state, "final_output": result, "error_info": None}
            else:
                return {**state, "final_output": "请告诉我您想对衣橱进行什么操作（添加/删除/查看/修改）", "error_info": None}
        
        except Exception as e:
            return {**state, "final_output": f"衣橱操作失败：{str(e)}", "error_info": str(e)}
    
    def _parse_add_clothing(self, user_input: str) -> str:
        """解析添加衣物命令"""
        # 检查是否包含具体衣物信息
        if "添加" in user_input:
            # 尝试从输入中提取衣物信息
            info = user_input.replace("添加", "").strip()
            if info:
                # 简单解析：名称，分类，颜色，材质
                parts = info.split("，")
                if len(parts) >= 2:
                    name = parts[0].strip()
                    category = parts[1].strip() if len(parts) > 1 else "上衣"
                    color = parts[2].strip() if len(parts) > 2 else "黑色"
                    material = parts[3].strip() if len(parts) > 3 else "棉"
                    
                    result = add_clothing.invoke({
                        "name": name,
                        "category": category,
                        "color": color,
                        "material": material,
                        "suitable_temp_min": 10,
                        "suitable_temp_max": 35,
                        "occasion_tags": ["casual"]
                    })
                    
                    if result.get("success"):
                        return f"已成功添加衣物：{name}"
                    else:
                        return f"添加失败：{result.get('error', '未知错误')}"
        
        return "请告诉我衣物信息（格式：名称，分类，颜色，材质）\n例如：牛仔裤，裤子，蓝色，牛仔布"

    def _parse_delete_clothing(self, user_input: str) -> str:
        """解析删除衣物命令"""
        items = list_wardrobe.invoke({})
        if not items:
            return "衣橱是空的，没有可删除的衣物。"
        
        # 尝试从输入中提取要删除的衣物名称
        name = user_input.replace("删除", "").strip()
        if name:
            for item in items:
                if item["name"] == name:
                    result = delete_clothing.invoke({"clothing_id": item["id"]})
                    if result.get("success"):
                        return f"已删除衣物：{name}"
                    else:
                        return f"删除失败：{result.get('error', '未知错误')}"
        
        names = [item["name"] for item in items]
        return f"当前衣橱有：{', '.join(names)}\n请告诉我要删除哪一件？"
    
    def _parse_update_clothing(self, user_input: str) -> str:
        """解析更新衣物命令"""
        items = list_wardrobe.invoke({})
        if not items:
            return "衣橱是空的，没有可修改的衣物。"
        
        names = [item["name"] for item in items]
        return f"当前衣橱有：{', '.join(names)}\n请告诉我要修改哪一件？"
    
    def fashion_advisor_node(self, state: AgentState) -> AgentState:
        """调用时尚顾问 Agent"""
        return self.fashion_advisor(state)
    
    def error_handler(self, state: AgentState) -> AgentState:
        """捕获异常，返回友好提示"""
        error_info = state.get("error_info", "未知错误")
        return {
            **state,
            "final_output": f"抱歉，遇到了一些问题：{error_info}\n请稍后重试或换一种方式提问。",
            "error_info": error_info
        }
    
    def output_node(self, state: AgentState) -> AgentState:
        """组装回复，更新对话历史"""
        final_output = state.get("final_output", "")
        
        if not final_output:
            weather_data = state.get("weather_data")
            if weather_data:
                final_output = f"当前天气：{weather_data['condition']}，温度 {weather_data['temp']}°C\n{weather_data['tips']}"
            else:
                final_output = "抱歉，暂时无法提供服务。"
        
        chat_history = state.get("chat_history", [])
        new_history = chat_history + [
            {"role": "user", "content": state.get("user_input", "")},
            {"role": "assistant", "content": final_output}
        ]
        
        return {**state, "chat_history": new_history, "final_output": final_output}
    
    def invoke(self, user_input: str, chat_history: Optional[List[Dict]] = None) -> AgentState:
        """调用图执行"""
        initial_state: AgentState = {
            "user_input": user_input,
            "intent": None,
            "weather_data": None,
            "occasion": None,
            "wardrobe_candidates": [],
            "preferences": None,
            "final_output": None,
            "chat_history": chat_history or [],
            "error_info": None,
            "session_id": "",
            "timestamp": ""
        }
        
        result = self.app.invoke(initial_state)
        return result
