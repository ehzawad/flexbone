import logging
import json
import sys
from datetime import datetime
from typing import Optional, Dict, Any


class CloudRunFormatter(logging.Formatter):
    # JSON formatter for Google Cloud Run structured logging
    
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'severity': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'endpoint'):
            log_obj['endpoint'] = record.endpoint
        if hasattr(record, 'processing_time_ms'):
            log_obj['processing_time_ms'] = record.processing_time_ms
        if hasattr(record, 'cache_hit'):
            log_obj['cache_hit'] = record.cache_hit
        
        # Add exception info if present
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_obj)


class LocalFormatter(logging.Formatter):
    # Human-readable formatter for local development
    
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        level = record.levelname
        message = record.getMessage()
        location = f"{record.module}.{record.funcName}:{record.lineno}"
        
        base_msg = f"[{timestamp}] {level:8s} {location:40s} {message}"
        
        # Add extra context if available
        extras = []
        if hasattr(record, 'endpoint'):
            extras.append(f"endpoint={record.endpoint}")
        if hasattr(record, 'processing_time_ms'):
            extras.append(f"time={record.processing_time_ms}ms")
        if hasattr(record, 'cache_hit'):
            extras.append(f"cached={record.cache_hit}")
        
        if extras:
            base_msg += f" | {' '.join(extras)}"
        
        if record.exc_info:
            base_msg += "\n" + self.formatException(record.exc_info)
        
        return base_msg


def setup_logger(name: str = __name__, level: str = "INFO") -> logging.Logger:
    # Setup logger with appropriate formatter based on environment
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    
    # Use JSON formatter for Cloud Run (detected by K_SERVICE env var)
    # Use local formatter for development
    import os
    if os.getenv('K_SERVICE'):
        formatter = CloudRunFormatter()
    else:
        formatter = LocalFormatter()
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


# Create default logger instance
logger = setup_logger("ocr_api")

