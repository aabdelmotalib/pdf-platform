"""
Redis Distributed Lock using Redlock Pattern
Ensures only one LibreOffice instance runs per worker at a time
"""

import time
import uuid
from typing import Optional
from redis import Redis
import os

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))


class RedisDistributedLock:
    """
    Simple distributed lock using Redis SET with NX and EX
    """
    
    def __init__(self, key: str, timeout: int = 120):
        """
        Initialize lock
        
        Args:
            key: Lock key name
            timeout: Lock timeout in seconds
        """
        self.redis = Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
        self.key = f"lock:{key}"
        self.timeout = timeout
        self.token = str(uuid.uuid4())
        self.is_locked = False
    
    def acquire(self, blocking: bool = True, max_wait: int = 300) -> bool:
        """
        Acquire the lock
        
        Args:
            blocking: Whether to wait for lock
            max_wait: Maximum seconds to wait for lock
        
        Returns:
            True if lock acquired, False if timeout
        """
        start_time = time.time()
        
        while True:
            # Try to acquire lock (atomic SET NX EX)
            result = self.redis.set(
                self.key,
                self.token,
                nx=True,  # Only set if not exists
                ex=self.timeout  # Expire after timeout seconds
            )
            
            if result:
                self.is_locked = True
                return True
            
            if not blocking:
                return False
            
            # Check timeout
            if time.time() - start_time > max_wait:
                return False
            
            # Wait before retry (exponential backoff)
            time.sleep(min(1.0, 0.1 * (1 + time.time() - start_time)))
    
    def release(self) -> bool:
        """
        Release the lock (only if token matches)
        
        Returns:
            True if released, False if token mismatch
        """
        if not self.is_locked:
            return False
        
        # Use Lua script for atomic read-check-delete
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        
        result = self.redis.eval(lua_script, 1, self.key, self.token)
        
        if result:
            self.is_locked = False
            return True
        
        return False
    
    def __enter__(self):
        """Context manager enter"""
        if not self.acquire(blocking=True):
            raise TimeoutError(f"Could not acquire lock {self.key}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release()


def get_libreoffice_lock(worker_id: Optional[str] = None) -> RedisDistributedLock:
    """
    Get a lock for LibreOffice execution
    
    Args:
        worker_id: Worker identifier (defaults to generic lock)
    
    Returns:
        RedisDistributedLock instance
    """
    key = "libreoffice:execution"
    if worker_id:
        key = f"libreoffice:{worker_id}"
    
    return RedisDistributedLock(key, timeout=300)  # 5 minute timeout for LibreOffice


class FileLock:
    """Simple file-based lock for testing without Redis"""
    
    def __init__(self, key: str, timeout: int = 120):
        """
        Initialize file lock
        
        Args:
            key: Lock key name
            timeout: Lock timeout in seconds
        """
        import tempfile
        self.lock_dir = os.path.join(tempfile.gettempdir(), "pdf_platform_locks")
        os.makedirs(self.lock_dir, exist_ok=True)
        
        self.key = key
        self.timeout = timeout
        self.lock_file = os.path.join(self.lock_dir, f"{key}.lock")
        self.is_locked = False
    
    def acquire(self, blocking: bool = True, max_wait: int = 300) -> bool:
        """Acquire the lock"""
        start_time = time.time()
        
        while True:
            try:
                # Try to create lock file exclusively
                fd = os.open(self.lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(fd)
                self.is_locked = True
                return True
            except FileExistsError:
                if not blocking:
                    return False
                
                if time.time() - start_time > max_wait:
                    return False
                
                time.sleep(0.5)
    
    def release(self) -> bool:
        """Release the lock"""
        if not self.is_locked:
            return False
        
        try:
            os.remove(self.lock_file)
            self.is_locked = False
            return True
        except FileNotFoundError:
            return False
    
    def __enter__(self):
        """Context manager enter"""
        if not self.acquire(blocking=True):
            raise TimeoutError(f"Could not acquire lock {self.key}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release()
