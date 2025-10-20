from pydantic import BaseModel, Field
from typing import Optional, List


class OCRResponse(BaseModel):
    # Response model for single image OCR
    success: bool
    text: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    processing_time_ms: int
    metadata: Optional[dict] = None


class BatchOCRResponse(BaseModel):
    # Response model for batch image OCR
    success: bool
    results: List[dict]
    total_images: int
    processing_time_ms: int
    failed_count: int = 0


class ErrorResponse(BaseModel):
    # Error response model
    success: bool = False
    error: str
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    # Health check response
    status: str
    service: str
    version: str

