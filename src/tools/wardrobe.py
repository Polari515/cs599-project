import json
import os
from typing import List, Dict, Optional
from langchain_core.tools import tool
from uuid import uuid4
from models.schemas import Clothing

STORAGE_PATH = os.path.join(os.path.dirname(__file__), '..', 'storage', 'wardrobe.json')


def ensure_storage_exists():
    """确保存储目录和文件存在，不存在则创建"""
    storage_dir = os.path.dirname(STORAGE_PATH)
    if not os.path.exists(storage_dir):
        os.makedirs(storage_dir)
    
    if not os.path.exists(STORAGE_PATH):
        with open(STORAGE_PATH, 'w', encoding='utf-8') as f:
            json.dump([], f)


def load_wardrobe() -> List[Dict]:
    """加载衣橱数据"""
    ensure_storage_exists()
    try:
        with open(STORAGE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_wardrobe(items: List[Dict]):
    """保存衣橱数据"""
    ensure_storage_exists()
    with open(STORAGE_PATH, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


@tool
def add_clothing(
    name: str,
    category: str,
    color: str,
    material: str,
    suitable_temp_min: int = 0,
    suitable_temp_max: int = 40,
    occasion_tags: Optional[List[str]] = None
) -> Dict:
    """
    添加衣物到衣橱
    
    参数:
        name: 衣物名称（如"白衬衫"）
        category: 类别（上衣/裤子/外套/鞋/配饰）
        color: 颜色（如"白色"）
        material: 材质（如"棉"）
        suitable_temp_min: 适合的最低温度（默认0）
        suitable_temp_max: 适合的最高温度（默认40）
        occasion_tags: 适合的场合标签列表（默认["casual"]）
    
    返回:
        {"success": bool, "id": str, "error": str}
    """
    try:
        clothing = Clothing(
            id=str(uuid4()),
            name=name,
            category=category,
            color=color,
            material=material,
            suitable_temp_min=suitable_temp_min,
            suitable_temp_max=suitable_temp_max,
            occasion_tags=occasion_tags or ["casual"]
        )
        
        wardrobe = load_wardrobe()
        wardrobe.append(clothing.model_dump())
        save_wardrobe(wardrobe)
        
        return {"success": True, "id": clothing.id, "error": ""}
    except Exception as e:
        return {"success": False, "id": "", "error": str(e)}


@tool
def delete_clothing(clothing_id: str) -> Dict:
    """
    删除衣橱中的衣物
    
    参数:
        clothing_id: 衣物ID
    
    返回:
        {"success": bool, "error": str}
    """
    try:
        wardrobe = load_wardrobe()
        filtered = [item for item in wardrobe if item["id"] != clothing_id]
        
        if len(filtered) == len(wardrobe):
            return {"success": False, "error": "未找到该衣物"}
        
        save_wardrobe(filtered)
        return {"success": True, "error": ""}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def list_wardrobe() -> List[Dict]:
    """
    返回所有衣物列表
    
    返回:
        所有衣物的列表
    """
    return load_wardrobe()


@tool
def update_clothing(
    clothing_id: str,
    name: Optional[str] = None,
    category: Optional[str] = None,
    color: Optional[str] = None,
    material: Optional[str] = None,
    suitable_temp_min: Optional[int] = None,
    suitable_temp_max: Optional[int] = None,
    occasion_tags: Optional[List[str]] = None
) -> Dict:
    """
    更新衣物信息
    
    参数:
        clothing_id: 衣物ID
        name: 新名称（可选）
        category: 新类别（可选）
        color: 新颜色（可选）
        material: 新材质（可选）
        suitable_temp_min: 新的最低温度（可选）
        suitable_temp_max: 新的最高温度（可选）
        occasion_tags: 新的场合标签（可选）
    
    返回:
        {"success": bool, "error": str}
    """
    try:
        wardrobe = load_wardrobe()
        found = False
        
        for item in wardrobe:
            if item["id"] == clothing_id:
                if name is not None:
                    item["name"] = name
                if category is not None:
                    item["category"] = category
                if color is not None:
                    item["color"] = color
                if material is not None:
                    item["material"] = material
                if suitable_temp_min is not None:
                    item["suitable_temp_min"] = suitable_temp_min
                if suitable_temp_max is not None:
                    item["suitable_temp_max"] = suitable_temp_max
                if occasion_tags is not None:
                    item["occasion_tags"] = occasion_tags
                found = True
                break
        
        if not found:
            return {"success": False, "error": "未找到该衣物"}
        
        save_wardrobe(wardrobe)
        return {"success": True, "error": ""}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def search_wardrobe(
    temp: int,
    condition: str,
    occasion: str = "casual",
    limit: int = 8
) -> List[Dict]:
    """
    基于规则过滤检索衣橱
    
    参数:
        temp: 当前温度（摄氏度）
        condition: 天气状况（晴/雨/多云等）
        occasion: 场合（casual/work/interview/date/sports/formal），默认casual
        limit: 返回数量限制，默认8
    
    返回:
        候选衣物列表，每个元素包含id, name, category, color, material,
        suitable_temp_min, suitable_temp_max, occasion_tags
    """
    wardrobe = load_wardrobe()
    
    if not wardrobe:
        return []
    
    primary_candidates = []
    secondary_candidates = []
    
    for item in wardrobe:
        temp_min = item.get("suitable_temp_min", 0)
        temp_max = item.get("suitable_temp_max", 40)
        tags = item.get("occasion_tags", ["casual"])
        
        temp_match = temp_min <= temp <= temp_max
        occasion_match = occasion in tags
        
        if temp_match and occasion_match:
            primary_candidates.append(item)
        elif temp_match:
            secondary_candidates.append(item)
    
    candidates = primary_candidates[:limit]
    
    if len(candidates) < limit:
        remaining = limit - len(candidates)
        candidates.extend(secondary_candidates[:remaining])
    
    return candidates
