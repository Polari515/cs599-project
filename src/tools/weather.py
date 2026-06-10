import os
import requests
from langchain_core.tools import tool
from typing import Dict
from datetime import datetime, timedelta
from utils.cache import Cache

cache = Cache(ttl=600)

CITY_CODE_MAP = {
    "北京": "101010100",
    "上海": "101020100",
    "广州": "101280101",
    "深圳": "101280601",
    "武汉": "101200101",
    "成都": "101270101",
    "杭州": "101210101",
    "南京": "101190101",
    "西安": "101110101",
    "重庆": "101040100",
    "天津": "101030100",
    "苏州": "101190401",
    "郑州": "101180101",
    "长沙": "101250101",
    "青岛": "101120201",
    "沈阳": "101070101",
    "大连": "101070201",
    "宁波": "101210401",
    "厦门": "101230201",
    "合肥": "101220101",
    "济南": "101120101",
    "哈尔滨": "101050101",
    "长春": "101060101",
    "福州": "101230101",
    "石家庄": "101090101",
    "太原": "101100101",
    "南宁": "101300101",
    "昆明": "101290101",
    "贵阳": "101260101",
    "南昌": "101240101",
    "无锡": "101190201",
    "佛山": "101280801",
    "东莞": "101281601",
    "珠海": "101280701",
    "中山": "101281701",
    "惠州": "101280901",
    "常州": "101190501",
    "嘉兴": "101210301",
    "绍兴": "101210501",
    "温州": "101210701",
    "台州": "101210801",
    "金华": "101210601",
    "徐州": "101190601",
    "南通": "101190301",
    "扬州": "101190701",
    "镇江": "101190801",
    "盐城": "101190901",
    "淮安": "101191001",
    "连云港": "101191101",
    "宿迁": "101191301",
    "泰州": "101191201",
}


def get_city_code(city_name: str) -> str:
    """获取城市代码，支持中文城市名"""
    city_name = city_name.strip()
    return CITY_CODE_MAP.get(city_name, city_name)


def generate_weather_tips(temp: int, condition: str, uvi: int) -> str:
    """根据天气数据生成穿搭建议提示"""
    tips = []
    
    if temp < 10:
        tips.append("天气寒冷，建议穿羽绒服或厚外套")
    elif temp < 18:
        tips.append("天气偏凉，建议穿毛衣或薄外套")
    elif temp < 25:
        tips.append("舒适温度，穿长袖衬衫或薄卫衣")
    elif temp < 30:
        tips.append("天气温暖，短袖T恤即可")
    else:
        tips.append("天气炎热，建议穿轻薄透气衣物")
    
    if "雨" in condition:
        tips.append("有雨，记得带伞")
    elif condition == "晴":
        if uvi >= 6:
            tips.append("紫外线强，注意防晒")
        else:
            tips.append("天气晴朗，适合外出")
    elif condition == "多云":
        tips.append("多云天气，体感舒适")
    
    return "；".join(tips)


@tool
def get_weather(city: str) -> Dict:
    """
    获取指定城市实时天气，返回结构化数据。
    
    参数:
        city: 城市名称（如"北京"、"上海"）
    
    返回:
        {
            "temp": 温度（摄氏度）,
            "condition": 天气状况（晴/雨/多云等）,
            "humidity": 相对湿度（%）,
            "wind_speed": 风速描述（微风/强风等）,
            "uvi": 紫外线指数,
            "tips": 穿搭建议提示
        }
    """
    api_key = os.getenv("HEWEATHER_KEY")
    
    if not api_key:
        return {
            "temp": 25,
            "condition": "晴",
            "humidity": 50,
            "wind_speed": "微风",
            "uvi": 3,
            "tips": "未配置和风天气API，使用默认天气数据"
        }
    
    cache_key = f"weather_{city}"
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    city_code = get_city_code(city)
    
    try:
        api_host = os.getenv("HEWEATHER_HOST")
        if not api_host:
            return {
                "temp": 25,
                "condition": "晴",
                "humidity": 50,
                "wind_speed": "微风",
                "uvi": 3,
                "tips": "未配置和风天气 API Host，请在 .env 中设置 HEWEATHER_HOST"
            }
        
        url = f"https://{api_host}/v7/weather/now?location={city_code}"
        headers = {
            "X-QW-Api-Key": api_key,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive"
        }
        
        response = requests.get(url, timeout=30, verify=True, headers=headers)
        
        if response.status_code >= 400:
            return {
                "temp": 25,
                "condition": "晴",
                "humidity": 50,
                "wind_speed": "微风",
                "uvi": 3,
                "tips": f"天气API请求失败: {response.status_code}"
            }
        
        data = response.json()
        
        if data.get("code") != "200":
            error_msg = data.get("msg", "未知错误")
            return {
                "temp": 25,
                "condition": "晴",
                "humidity": 50,
                "wind_speed": "微风",
                "uvi": 3,
                "tips": f"天气查询失败: {error_msg}"
            }
        
        now = data["now"]
        result = {
            "temp": int(now["temp"]),
            "condition": now["text"],
            "humidity": int(now["humidity"]),
            "wind_speed": now.get("windScale", "微风"),
            "uvi": int(now.get("uvIndex", 0)),
            "tips": generate_weather_tips(int(now["temp"]), now["text"], int(now.get("uvIndex", 0)))
        }
        
        cache.set(cache_key, result)
        return result
    
    except requests.exceptions.RequestException as e:
        return {
            "temp": 25,
            "condition": "晴",
            "humidity": 50,
            "wind_speed": "微风",
            "uvi": 3,
            "tips": f"天气数据获取失败: {str(e)}"
        }
