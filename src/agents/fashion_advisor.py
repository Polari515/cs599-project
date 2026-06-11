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
1. 优先从提供的候选衣物列表中选择已有的衣物
2. 如果衣橱缺少某些类型的衣物，可以补充推荐合适的衣物（用【建议添加】标记）
3. 必须考虑当前天气状况和温度
4. 必须考虑用户指定的场合需求
5. 推荐搭配时必须给出具体理由
6. 回答要友好、专业且简洁
7. 在推荐方案中明确标注哪些是用户已有的（无需特别标记），哪些是建议添加的（用【建议添加】标记）

输出格式：
- 首先给出天气情况总结
- 然后列出推荐的搭配方案，明确标注【建议添加】的衣物
- 最后给出搭配理由

请用中文回复。
""")
    
    def _generate_missing_clothing(self, category: str, weather_temp: int) -> dict:
        """
        生成虚拟衣物建议
        
        参数:
            category: 衣物类别
            weather_temp: 当前温度
            
        返回:
            虚拟衣物字典
        """
        clothing_templates = {
            "上衣": [
                {"name": "白色T恤", "color": "白色", "material": "棉"},
                {"name": "条纹衬衫", "color": "蓝白条纹", "material": "棉"},
                {"name": "针织毛衣", "color": "米色", "material": "羊毛"},
                {"name": "薄款卫衣", "color": "灰色", "material": "棉混纺"},
                {"name": "POLO衫", "color": "藏蓝色", "material": "棉"},
            ],
            "裤子": [
                {"name": "牛仔裤", "color": "蓝色", "material": "牛仔布"},
                {"name": "休闲长裤", "color": "卡其色", "material": "棉"},
                {"name": "运动裤", "color": "黑色", "material": "聚酯纤维"},
                {"name": "西裤", "color": "黑色", "material": "羊毛混纺"},
                {"name": "短裤", "color": "灰色", "material": "棉"},
            ],
            "外套": [
                {"name": "牛仔外套", "color": "蓝色", "material": "牛仔布"},
                {"name": "风衣", "color": "卡其色", "material": "棉质混纺"},
                {"name": "羽绒服", "color": "黑色", "material": "羽绒"},
                {"name": "西装外套", "color": "藏蓝色", "material": "羊毛"},
                {"name": "针织开衫", "color": "米色", "material": "羊毛"},
            ],
            "鞋": [
                {"name": "运动鞋", "color": "白色", "material": "网布"},
                {"name": "皮鞋", "color": "黑色", "material": "真皮"},
                {"name": "休闲鞋", "color": "棕色", "material": "真皮"},
                {"name": "靴子", "color": "黑色", "material": "真皮"},
                {"name": "凉鞋", "color": "米色", "material": "皮革"},
            ],
            "配饰": [
                {"name": "围巾", "color": "灰色", "material": "羊毛"},
                {"name": "帽子", "color": "黑色", "material": "棉"},
                {"name": "手表", "color": "银色", "material": "金属"},
                {"name": "皮带", "color": "棕色", "material": "真皮"},
            ],
        }
        
        templates = clothing_templates.get(category, [])
        if not templates:
            return {"name": f"{category}", "color": "黑色", "material": "棉"}
        
        # 根据温度选择合适的衣物
        index = 0
        if weather_temp < 10:
            index = min(2, len(templates) - 1)  # 较厚衣物
        elif weather_temp > 25:
            index = min(4, len(templates) - 1)  # 较薄衣物
        
        return templates[index]
    
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
            show_missing_warning: 是否显示缺少衣物的警告提示（已废弃，保持兼容）
        
        返回:
            穿搭建议文本
        """
        weather_temp = weather_data.get("temp", 25)
        weather_summary = f"""当前天气：{weather_data['condition']}，温度 {weather_temp}°C，{weather_data['tips']}"""
        
        occasion_desc = {
            "casual": "休闲场合",
            "work": "工作场合",
            "interview": "面试场合",
            "date": "约会场合",
            "sports": "运动场合",
            "formal": "正式场合"
        }
        
        occasion_text = occasion_desc.get(occasion, "日常休闲")
        
        # 按分类统计已有衣物
        existing_categories = {}
        for item in wardrobe_candidates:
            category = item.get("category", "其他")
            if category not in existing_categories:
                existing_categories[category] = []
            existing_categories[category].append(item)
        
        # 定义穿搭所需的基本类别
        required_categories = ["上衣", "裤子", "外套", "鞋"]
        
        # 准备候选衣物列表（包含已有和虚拟衣物）
        enhanced_candidates = []
        
        # 添加已有衣物
        for category, items in existing_categories.items():
            for item in items:
                enhanced_candidates.append({
                    **item,
                    "is_virtual": False  # 标记为已有衣物
                })
        
        # 为缺少的类别生成虚拟衣物建议
        for category in required_categories:
            if category not in existing_categories and category != "外套":  # 外套根据温度决定是否需要
                # 检查是否有类似类别（如"鞋"和"鞋子"）
                has_similar = False
                for existing_cat in existing_categories:
                    if category in existing_cat or existing_cat in category:
                        has_similar = True
                        break
                
                if not has_similar:
                    # 生成虚拟衣物
                    virtual_clothing = self._generate_missing_clothing(category, weather_temp)
                    enhanced_candidates.append({
                        "name": virtual_clothing["name"],
                        "category": category,
                        "color": virtual_clothing["color"],
                        "material": virtual_clothing["material"],
                        "is_virtual": True  # 标记为虚拟衣物
                    })
        
        # 根据温度决定是否需要外套
        if "外套" not in existing_categories and weather_temp < 15:
            virtual_coat = self._generate_missing_clothing("外套", weather_temp)
            enhanced_candidates.append({
                "name": virtual_coat["name"],
                "category": "外套",
                "color": virtual_coat["color"],
                "material": virtual_coat["material"],
                "is_virtual": True
            })
        
        # 构建衣物信息文本，区分已有和虚拟衣物
        clothing_info = ""
        if wardrobe_candidates:
            clothing_info += "您已有的衣物：\n"
            for idx, item in enumerate(wardrobe_candidates, 1):
                clothing_info += f"{idx}. {item['name']} - {item['category']} - {item['color']} - {item['material']}\n"
        
        # 找出虚拟衣物用于说明
        virtual_items = [item for item in enhanced_candidates if item.get("is_virtual", False)]
        if virtual_items:
            clothing_info += "\n建议添加的衣物（为完善穿搭推荐）：\n"
            for idx, item in enumerate(virtual_items, 1):
                clothing_info += f"{idx}. {item['name']} - {item['category']} - {item['color']} - {item['material']}\n"
        
        # 生成穿搭建议
        human_prompt = HumanMessagePromptTemplate.from_template("""
天气情况：{weather_summary}
场合需求：{occasion_text}

候选衣物（标注【建议添加】的为虚拟推荐）：
{clothing_info}

请为我推荐一套合适的穿搭方案。在推荐时：
1. 优先使用用户已有的衣物
2. 如果使用了虚拟衣物，请在该衣物名称后标注【建议添加】
3. 给出搭配理由
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
            
            final_output = self.generate_outfit_suggestion(
                weather_data=weather_data,
                wardrobe_candidates=wardrobe_candidates,
                occasion=occasion,
                show_missing_warning=False  # 不显示缺少衣物警告
            )
            
            return {**state, "final_output": final_output, "error_info": None}
        
        except Exception as e:
            return {**state, "final_output": f"生成穿搭建议时出错：{str(e)}", "error_info": str(e)}
