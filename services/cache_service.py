import hashlib
import time
import threading
from collections import OrderedDict
from typing import Optional, Dict
from config import config
from utils.logger import logger


class LRUCache:
    # LRU (Least Recently Used) cache with TTL support and size limits
    
    def __init__(self):
        self._cache: OrderedDict[str, dict] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'sets': 0,
        }
    
    def _is_expired(self, entry: dict) -> bool:
        # Check if cache entry is expired
        return time.time() > entry['expires_at']
    
    def _evict_lru(self) -> None:
        # Evict least recently used item
        if self._cache:
            key, _ = self._cache.popitem(last=False)
            self._stats['evictions'] += 1
            logger.debug(f"LRU eviction: cache at max size ({config.MAX_CACHE_SIZE})")
    
    def get(self, key: str) -> Optional[dict]:
        # Get value from cache, returns None if not found/expired
        if not config.CACHE_ENABLED:
            return None
        
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                
                # Check expiration
                if self._is_expired(entry):
                    del self._cache[key]
                    self._stats['misses'] += 1
                    return None
                
                # Move to end (mark as recently used)
                self._cache.move_to_end(key)
                self._stats['hits'] += 1
                return entry['value']
            
            self._stats['misses'] += 1
            return None
    
    def set(self, key: str, value: dict, ttl: int = None) -> None:
        # Set value in cache with optional TTL
        if not config.CACHE_ENABLED:
            return
        
        if ttl is None:
            ttl = config.CACHE_TTL_SECONDS
        
        with self._lock:
            # Check if we need to evict
            if key not in self._cache and len(self._cache) >= config.MAX_CACHE_SIZE:
                self._evict_lru()
            
            # Add/update entry (move to end if exists)
            self._cache[key] = {
                'value': value,
                'expires_at': time.time() + ttl,
                'created_at': time.time()
            }
            
            # Move to end (mark as recently used)
            self._cache.move_to_end(key)
            self._stats['sets'] += 1
    
    def delete(self, key: str) -> None:
        # Delete value from cache
        with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    def clear(self) -> None:
        # Clear all cache entries
        with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")
    
    def size(self) -> int:
        # Get number of cache entries (excluding expired)
        with self._lock:
            # Remove expired entries first
            expired_keys = [k for k, v in self._cache.items() if self._is_expired(v)]
            for key in expired_keys:
                del self._cache[key]
            
            return len(self._cache)
    
    def cleanup_expired(self) -> int:
        # Remove all expired entries and return count removed
        with self._lock:
            expired_keys = [k for k, v in self._cache.items() if self._is_expired(v)]
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.info(f"Cache cleanup: Removed {len(expired_keys)} expired entries")
            
            return len(expired_keys)
    
    def get_stats(self) -> dict:
        # Get cache statistics
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0.0
            
            # Get oldest entry age
            oldest_age = None
            if self._cache:
                first_entry = next(iter(self._cache.values()))
                oldest_age = time.time() - first_entry['created_at']
            
            # Estimate memory usage (rough estimate)
            # Each entry has key (64 bytes hash) + value (~1KB avg) + metadata (~100 bytes)
            estimated_memory_mb = len(self._cache) * 1.2 / 1024  # ~1.2KB per entry
            
            return {
                'size': len(self._cache),
                'max_size': config.MAX_CACHE_SIZE,
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'hit_rate': round(hit_rate, 2),
                'evictions': self._stats['evictions'],
                'total_sets': self._stats['sets'],
                'oldest_entry_age_seconds': round(oldest_age, 2) if oldest_age else None,
                'estimated_memory_mb': round(estimated_memory_mb, 2),
                'ttl_seconds': config.CACHE_TTL_SECONDS
            }
    
    def reset_stats(self) -> None:
        # Reset statistics counters
        with self._lock:
            self._stats = {
                'hits': 0,
                'misses': 0,
                'evictions': 0,
                'sets': 0,
            }


def generate_cache_key(file_content: bytes) -> str:
    # Generate cache key from file content using SHA256 hash
    return hashlib.sha256(file_content).hexdigest()


# Global cache instance
cache = LRUCache()
