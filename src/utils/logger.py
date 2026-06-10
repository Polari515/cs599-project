import logging
import os
from datetime import datetime


class Logger:
    """日志记录工具"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        
        log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")
        
        self.logger = logging.getLogger("smart-wardrobe")
        self.logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def info(self, message: str, **kwargs):
        """记录 INFO 级别日志"""
        self.logger.info(message, extra=kwargs)
    
    def debug(self, message: str, **kwargs):
        """记录 DEBUG 级别日志"""
        self.logger.debug(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """记录 WARNING 级别日志"""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """记录 ERROR 级别日志"""
        self.logger.error(message, extra=kwargs)
    
    def log_llm_call(self, input_tokens: int, output_tokens: int, duration: float):
        """记录 LLM 调用信息"""
        self.info(
            f"LLM调用完成 - 输入Token: {input_tokens}, 输出Token: {output_tokens}, 耗时: {duration:.2f}s"
        )
    
    def log_tool_call(self, tool_name: str, duration: float, success: bool):
        """记录工具调用信息"""
        status = "成功" if success else "失败"
        self.info(f"工具调用 - {tool_name}: {status}, 耗时: {duration:.2f}s")
    
    def log_request(self, session_id: str, user_input: str, intent: str):
        """记录用户请求"""
        self.info(f"用户请求 - Session: {session_id[:8]}, 意图: {intent}, 输入: {user_input[:50]}...")


logger = Logger()
