import time
import asyncio
from typing import List
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from config import config
from models import OCRResponse, BatchOCRResponse, ErrorResponse, HealthResponse
from utils.validators import validate_upload_file
from utils.text_processor import preprocess_text
from utils.error_handlers import (
    OCRAPIException,
    BatchSizeExceededException
)
from utils.logger import logger
from services.ocr_service import ocr_service
from services.cache_service import cache, generate_cache_key
from middleware.rate_limiter import get_limiter

# Background task for cache cleanup
async def cleanup_cache_periodically():
    # Background task to clean up expired cache entries every 5 minutes
    while True:
        await asyncio.sleep(config.CACHE_CLEANUP_INTERVAL)
        removed = cache.cleanup_expired()
        if removed > 0:
            logger.info(f"Cache cleanup: Removed {removed} expired entries")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Manage app lifespan - start/stop background tasks
    # Startup
    task = asyncio.create_task(cleanup_cache_periodically())
    yield
    # Shutdown
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

# Initialize FastAPI app
app = FastAPI(
    title="OCR Image Text Extraction API",
    description="Extract text from images using Google Cloud Vision API with intelligent caching",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize rate limiter
limiter = get_limiter()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(OCRAPIException)
async def ocr_exception_handler(request: Request, exc: OCRAPIException):
    # Handle custom OCR API exceptions
    logger.warning(f"OCR API exception: {exc.message}", extra={'endpoint': str(request.url.path)})
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.message,
            "detail": str(exc)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    # Handle unexpected exceptions gracefully
    # Log the actual error for debugging
    logger.error(f"Unexpected exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Unable to process request. Please try again or use a different image."
        }
    )


@app.get("/", include_in_schema=False)
async def root():
    # Serve homepage
    return FileResponse("static/index.html")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    # Serve favicon
    return FileResponse("static/favicon.ico")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    # Health check endpoint for Cloud Run
    return HealthResponse(
        status="healthy",
        service="OCR API",
        version="1.0.0"
    )


@app.post("/extract-text", response_model=OCRResponse)
async def extract_text(request: Request, image: UploadFile = File(...)):
    # Extract text from a single image (JPG, PNG, GIF, WebP, BMP, max 10MB)
    start_time = time.time()
    endpoint = "/extract-text"
    
    # Validate file
    file_content, image_metadata = await validate_upload_file(image)
    
    # Generate cache key
    cache_key = generate_cache_key(file_content)
    
    # Check cache (cached by image CONTENT hash, not filename!)
    cached_result = cache.get(cache_key)
    if cached_result:
        processing_time_ms = int((time.time() - start_time) * 1000)
        logger.info(f"Request processed (cached)", extra={
            'endpoint': endpoint,
            'processing_time_ms': processing_time_ms,
            'cache_hit': True
        })
        
        return OCRResponse(
            success=True,
            text=cached_result['text'],
            confidence=cached_result['confidence'],
            processing_time_ms=processing_time_ms,
            metadata={
                **cached_result.get('metadata', {}),
                'cached': True
            }
        )
    
    # Perform OCR (cache miss - call Vision API)
    ocr_result = ocr_service.extract_text_with_metadata(file_content, image_metadata)
    
    # Preprocess text
    cleaned_text = preprocess_text(ocr_result['text'])
    
    # Calculate processing time
    processing_time_ms = int((time.time() - start_time) * 1000)
    
    # Prepare response
    response_data = {
        'text': cleaned_text,
        'confidence': ocr_result['confidence'],
        'metadata': {
            'language': ocr_result.get('language'),
            'detected_languages': ocr_result.get('detected_languages', []),
            'image_width': image_metadata['width'],
            'image_height': image_metadata['height'],
            'image_format': image_metadata['format'],
            'has_text': ocr_result['has_text'],
            'cached': False
        }
    }
    
    # Cache result
    cache.set(cache_key, response_data)
    
    # Log request
    logger.info(f"Request processed (Vision API)", extra={
        'endpoint': endpoint,
        'processing_time_ms': processing_time_ms,
        'cache_hit': False,
        'has_text': ocr_result['has_text']
    })
    
    return OCRResponse(
        success=True,
        text=cleaned_text,
        confidence=ocr_result['confidence'],
        processing_time_ms=processing_time_ms,
        metadata=response_data['metadata']
    )


@app.post("/batch-extract", response_model=BatchOCRResponse)
async def batch_extract_text(request: Request, images: List[UploadFile] = File(...)):
    # Extract text from multiple images in batch (JPG, PNG, GIF, WebP, BMP, max 10MB each)
    start_time = time.time()
    endpoint = "/batch-extract"
    
    # Validate batch size
    if len(images) == 0:
        raise BatchSizeExceededException("No images provided. Please upload at least one image.")
    
    if len(images) > config.MAX_BATCH_SIZE:
        raise BatchSizeExceededException(
            f"Too many images ({len(images)}). Maximum is {config.MAX_BATCH_SIZE} images per batch."
        )
    
    results = []
    failed_count = 0
    cache_hits = 0
    vision_api_calls = 0
    
    async def process_single_image(img: UploadFile, index: int) -> dict:
        # Process a single image and return result
        nonlocal cache_hits, vision_api_calls
        try:
            # Validate file
            file_content, image_metadata = await validate_upload_file(img)
            
            # Generate cache key
            cache_key = generate_cache_key(file_content)
            
            # Check cache
            cached_result = cache.get(cache_key)
            if cached_result:
                cache_hits += 1
                return {
                    'index': index,
                    'filename': img.filename,
                    'success': True,
                    'text': cached_result['text'],
                    'confidence': cached_result['confidence'],
                    'metadata': {
                        **cached_result.get('metadata', {}),
                        'cached': True
                    }
                }
            
            # Perform OCR (cache miss)
            vision_api_calls += 1
            ocr_result = ocr_service.extract_text_with_metadata(file_content, image_metadata)
            
            # Preprocess text
            cleaned_text = preprocess_text(ocr_result['text'])
            
            response_data = {
                'text': cleaned_text,
                'confidence': ocr_result['confidence'],
                'metadata': {
                    'language': ocr_result.get('language'),
                    'detected_languages': ocr_result.get('detected_languages', []),
                    'image_width': image_metadata['width'],
                    'image_height': image_metadata['height'],
                    'image_format': image_metadata['format'],
                    'has_text': ocr_result['has_text'],
                    'cached': False
                }
            }
            
            # Cache result
            cache.set(cache_key, response_data)
            
            return {
                'index': index,
                'filename': img.filename,
                'success': True,
                'text': cleaned_text,
                'confidence': ocr_result['confidence'],
                'metadata': response_data['metadata']
            }
            
        except Exception as e:
            return {
                'index': index,
                'filename': img.filename,
                'success': False,
                'error': str(e),
                'text': '',
                'confidence': 0.0
            }
    
    # Process all images concurrently
    tasks = [process_single_image(img, i) for i, img in enumerate(images)]
    results = await asyncio.gather(*tasks)
    
    # Count failures
    failed_count = sum(1 for r in results if not r['success'])
    
    # Calculate total processing time
    processing_time_ms = int((time.time() - start_time) * 1000)
    
    # Log batch request
    logger.info(f"Batch request processed", extra={
        'endpoint': endpoint,
        'processing_time_ms': processing_time_ms,
        'total_images': len(images),
        'cache_hits': cache_hits,
        'vision_api_calls': vision_api_calls,
        'failed_count': failed_count
    })
    
    return BatchOCRResponse(
        success=True,
        results=results,
        total_images=len(images),
        processing_time_ms=processing_time_ms,
        failed_count=failed_count
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT)

