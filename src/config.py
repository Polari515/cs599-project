import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """应用配置类"""
    
    # LLM 配置
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL = "deepseek-v4-flash"
    
    # 天气 API 配置
    HEWEATHER_KEY = os.getenv("HEWEATHER_KEY")
    
    # 缓存配置
    WEATHER_CACHE_TTL = 600
    
    # 存储配置
    STORAGE_DIR = os.path.join(os.path.dirname(__file__), "storage")
    WARDROBE_FILE = os.path.join(STORAGE_DIR, "wardrobe.json")
    
    # LLM 参数
    INTENT_CLASSIFIER_TEMPERATURE = 0.3
    FASHION_ADVISOR_TEMPERATURE = 0.5
    
    # 衣橱检索配置
    DEFAULT_SEARCH_LIMIT = 8
    
    @classmethod
    def ensure_storage(cls):
        """确保存储目录存在"""
        if not os.path.exists(cls.STORAGE_DIR):
            os.makedirs(cls.STORAGE_DIR)
        
        if not os.path.exists(cls.WARDROBE_FILE):
            import json
            with open(cls.WARDROBE_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f)
    
    @classmethod
    def validate(cls):
        """验证配置是否完整"""
        if not cls.DEEPSEEK_API_KEY:
            print("警告：未配置 DEEPSEEK_API_KEY，将使用模拟数据")
        
        if not cls.HEWEATHER_KEY:
            print("警告：未配置 HEWEATHER_KEY，将使用默认天气数据")
        
        cls.ensure_storage()
