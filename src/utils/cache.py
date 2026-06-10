from typing import Any, Optional
from datetime import datetime, timedelta
import threading
import time


class CacheEntry:
    """缓存条目"""
    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.expire_at = datetime.now() + timedelta(seconds=ttl)
    
    def is_expired(self) -> bool:
        return datetime.now() > self.expire_at


class Cache:
    """简单的 TTL 缓存实现"""
    
    def __init__(self, ttl: int = 600):
        """
        初始化缓存
        
        参数:
            ttl: 默认过期时间（秒），默认为 10 分钟
        """
        self.ttl = ttl
        self._cache = {}
        self._lock = threading.Lock()
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """启动后台清理线程，定期清理过期缓存"""
        def cleanup():
            while True:
                time.sleep(60)
                self._cleanup_expired()
        import threading
        thread = threading.Thread(target=cleanup, daemon=True)
        thread.start()
    
    def _cleanup_expired(self):
        """清理所有过期的缓存条目"""
        with self._lock:
            expired_keys = [k for k, entry in self._cache.items() if entry.is_expired()]
            for key in expired_keys:
                del self._cache[key]
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值，如果过期返回 None"""
        with self._lock:
            entry = self._cache.get(key)
            if entry and not entry.is_expired():
                return entry.value
            elif entry:
                del self._cache[key]
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置缓存值"""
        with self._lock:
            self._cache[key] = CacheEntry(value, ttl or self.ttl)
    
    def delete(self, key: str):
        """删除缓存值"""
        with self._lock:
            self._cache.pop(key, None)
    
    def clear(self):
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()
    
    def get_size(self) -> int:
        """获取缓存条目数量"""
        with self._lock:
            return len(self._cache)
