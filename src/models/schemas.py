from typing import TypedDict, Optional, List, Dict
from pydantic import BaseModel, Field
from uuid import uuid4


class WeatherData(TypedDict):
    """结构化天气数据"""
    temp: int
    condition: str
    humidity: int
    wind_speed: str
    uvi: int
    tips: str


class Clothing(BaseModel):
    """衣物数据模型"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    category: str
    color: str
    material: str
    suitable_temp_min: int = Field(default=0, ge=-20, le=50)
    suitable_temp_max: int = Field(default=40, ge=-20, le=50)
    occasion_tags: List[str] = Field(default_factory=lambda: ["casual"])

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "白衬衫",
                "category": "上衣",
                "color": "白色",
                "material": "棉",
                "suitable_temp_min": 20,
                "suitable_temp_max": 35,
                "occasion_tags": ["work", "formal", "interview"]
            }
        }
    }


class AgentState(TypedDict):
    """LangGraph 全局状态对象"""
    user_input: str
    intent: Optional[str]
    weather_data: Optional[WeatherData]
    occasion: Optional[str]
    wardrobe_candidates: List[Dict]
    preferences: Optional[Dict]
    final_output: Optional[str]
    chat_history: List[Dict]
    error_info: Optional[str]
    session_id: str
    timestamp: str


class IntentResult(BaseModel):
    """意图分类结果"""
    intent: str
    occasion: Optional[str] = None
    city: Optional[str] = None
