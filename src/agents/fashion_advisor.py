import os
from typing import Dict, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.messages import ChatMessage
from models.schemas import AgentState


class FashionAdvisor:
    """时尚顾问 Agent - 基于天气和衣橱生成穿搭建议"""
    
    def __init__(self):
        api_key = os.getenv("DEEPSEEK_API_KEY")
        self.llm = ChatOpenAI(
            model="deepseek-v4-flash",
            temperature=0.5,
            api_key=api_key,
            base_url="https://api.deepseek.com/v1",
            max_tokens=1024
        )
        
        self.system_prompt = SystemMessagePromptTemplate.from_template("""
你是一位专业的时尚穿搭顾问。请根据以下信息为用户提供穿搭建议：

规则约束（必须严格遵守）：
1. 只能从提供的候选衣物列表中选择，**绝对禁止**编造衣物
2. 如果候选列表为空，直接告知用户衣橱为空，请先添加衣物
3. 必须考虑当前天气状况和温度
4. 必须考虑用户指定的场合需求
5. 推荐搭配时必须给出具体理由
6. 回答要友好、专业且简洁

输出格式：
- 首先给出天气情况总结
- 然后列出推荐的搭配方案（上衣 + 裤子/裙子 + 外套 + 鞋）
- 最后给出搭配理由

请用中文回复。
""")
    
    def generate_outfit_suggestion(
        self,
        weather_data: Dict,
        wardrobe_candidates: List[Dict],
        occasion: Optional[str] = "casual",
        show_missing_warning: bool = True
    ) -> str:
        """
        生成穿搭建议
        
        参数:
            weather_data: 天气数据
            wardrobe_candidates: 候选衣物列表
            occasion: 场合（casual/work/interview/date/sports/formal）
            show_missing_warning: 是否显示缺少衣物的警告提示
        
        返回:
            穿搭建议文本
        """
        if not wardrobe_candidates:
            return "您的衣橱目前是空的，请先添加一些衣物，我才能为您提供穿搭建议。"
        
        # 按分类统计衣物
        category_counts = {}
        for item in wardrobe_candidates:
            category = item.get("category", "其他")
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # 检查是否有足够的衣物类型（支持别名匹配）
        category_aliases = {
            "上衣": ["上衣"],
            "裤子": ["裤子"],
            "外套": ["外套"],
            "鞋子": ["鞋", "鞋子"]  # 支持"鞋"和"鞋子"两种写法
        }
        
        missing_categories = []
        for cat, aliases in category_aliases.items():
            has_category = any(category_counts.get(alias, 0) > 0 for alias in aliases)
            if not has_category:
                missing_categories.append(cat)
        
        weather_summary = f"""当前天气：{weather_data['condition']}，温度 {weather_data['temp']}°C，{weather_data['tips']}"""
        
        occasion_desc = {
            "casual": "休闲场合",
            "work": "工作场合",
            "interview": "面试场合",
            "date": "约会场合",
            "sports": "运动场合",
            "formal": "正式场合"
        }
        
        occasion_text = occasion_desc.get(occasion, "日常休闲")
        
        clothing_info = "\n候选衣物列表：\n"
        for idx, item in enumerate(wardrobe_candidates, 1):
            clothing_info += f"{idx}. {item['name']} - {item['category']} - {item['color']} - {item['material']}\n"
        
        # 如果缺少关键衣物类型，给出提示（仅在 show_missing_warning=True 时）
        if missing_categories and show_missing_warning:
            suggestion = f"{weather_summary}\n\n"
            suggestion += f"根据您的衣橱情况，当前缺少以下类型的衣物：{', '.join(missing_categories)}\n\n"
            suggestion += "目前您拥有的衣物：\n"
            for cat, count in category_counts.items():
                suggestion += f"- {cat}：{count} 件\n"
            suggestion += "\n建议您添加一些缺少的衣物类型，以便为您提供更完整的穿搭建议。\n"
            
            # 如果有部分衣物可用，尝试给出部分建议
            if category_counts:
                suggestion += "\n基于您现有的衣物，给您一些搭配灵感：\n"
                human_prompt = HumanMessagePromptTemplate.from_template("""
天气情况：{weather_summary}
场合需求：{occasion_text}

候选衣物：
{clothing_info}

注意：用户的衣橱可能缺少某些类型的衣物（如裤子、鞋子等）。
请基于现有衣物给出最佳搭配建议，如果无法组成完整穿搭，请说明缺少什么。
不要编造不存在的衣物。
""")
                
                messages = [
                    self.system_prompt.format(),
                    human_prompt.format(
                        weather_summary=weather_summary,
                        occasion_text=occasion_text,
                        clothing_info=clothing_info
                    )
                ]
                
                response = self.llm.invoke(messages)
                suggestion += response.content
            
            return suggestion
        
        # 衣物足够或不显示警告，直接生成建议
        human_prompt = HumanMessagePromptTemplate.from_template("""
天气情况：{weather_summary}
场合需求：{occasion_text}

候选衣物：
{clothing_info}

请为我推荐一套合适的穿搭方案。
""")
        
        messages = [
            self.system_prompt.format(),
            human_prompt.format(
                weather_summary=weather_summary,
                occasion_text=occasion_text,
                clothing_info=clothing_info
            )
        ]
        
        response = self.llm.invoke(messages)
        return response.content
    
    def __call__(self, state: AgentState) -> AgentState:
        """
        LangGraph 节点调用接口
        
        参数:
            state: AgentState 状态对象
        
        返回:
            更新后的状态对象
        """
        try:
            weather_data = state.get("weather_data", {})
            wardrobe_candidates = state.get("wardrobe_candidates", [])
            occasion = state.get("occasion", "casual")
            
            # 检查是否已经提示过缺少衣物（通过查看聊天历史）
            # 聊天历史包含在 state 中，可能是 "chat_history" 或 "messages"
            chat_history = state.get("chat_history", [])
            if not chat_history:
                chat_history = state.get("messages", [])
            
            has_shown_warning = False
            for msg in chat_history:
                content = ""
                
                # 处理字典格式的消息
                if isinstance(msg, dict):
                    content = msg.get("content", "")
                # 处理 BaseMessage 对象
                elif hasattr(msg, 'content'):
                    content = msg.content
                
                # 检查是否包含衣物不足的提示关键词
                if "缺少" in content and "衣物" in content and ("建议您添加" in content or "添加一些" in content):
                    has_shown_warning = True
                    break
            
            # 如果已经提示过，就不再显示警告
            show_missing_warning = not has_shown_warning
            
            final_output = self.generate_outfit_suggestion(
                weather_data=weather_data,
                wardrobe_candidates=wardrobe_candidates,
                occasion=occasion,
                show_missing_warning=show_missing_warning
            )
            
            return {**state, "final_output": final_output, "error_info": None}
        
        except Exception as e:
            return {**state, "final_output": f"生成穿搭建议时出错：{str(e)}", "error_info": str(e)}
