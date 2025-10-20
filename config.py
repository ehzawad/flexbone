import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Application configuration
    
    # GCP Settings
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "ehz-stuff")
    
    # File Upload Settings
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
    # Tested and verified formats only
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "bmp"}
    ALLOWED_MIME_TYPES = {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/gif",
        "image/webp",
        "image/bmp"
    }
    
    # File signatures (magic numbers) for validation
    # File signatures (magic numbers) - tested formats only
    FILE_SIGNATURES = {
        b'\xFF\xD8\xFF': 'jpg',
        b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A': 'png',
        b'\x47\x49\x46\x38\x37\x61': 'gif',
        b'\x47\x49\x46\x38\x39\x61': 'gif',
        b'\x52\x49\x46\x46': 'webp',  # RIFF (WebP container)
        b'\x42\x4D': 'bmp'
    }
    
    # Rate Limiting (set to 0 to disable)
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "0"))  # 0 = disabled for testing
    BATCH_RATE_LIMIT_PER_MINUTE = int(os.getenv("BATCH_RATE_LIMIT_PER_MINUTE", "0"))  # 0 = disabled for testing
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "false").lower() == "true"
    
    # Caching (1 hour TTL with auto-cleanup)
    CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))  # 1 hour
    CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    CACHE_CLEANUP_INTERVAL = int(os.getenv("CACHE_CLEANUP_INTERVAL", "300"))  # Cleanup every 5 minutes
    MAX_CACHE_SIZE = int(os.getenv("MAX_CACHE_SIZE", "1000"))  # Maximum cache entries (LRU eviction)
    
    # Batch Processing
    MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", "10"))
    
    # Server Settings
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8080"))


config = Config()

