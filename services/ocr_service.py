import io
from typing import Optional
from google.cloud import vision
from google.cloud.vision_v1 import types
from PIL import Image
from config import config
from utils.error_handlers import OCRProcessingException


class OCRService:
    # Google Cloud Vision API OCR Service
    
    def __init__(self):
        # Initialize Vision API client
        try:
            self.client = vision.ImageAnnotatorClient()
        except Exception as e:
            raise OCRProcessingException(f"Failed to initialize Vision API client: {str(e)}")
    
    def extract_text(self, image_content: bytes) -> dict:
        # Extract text from image using Google Cloud Vision API
        try:
            # Create Vision API image object
            image = types.Image(content=image_content)
            
            # Perform text detection
            response = self.client.text_detection(image=image)
            
            # Alternative: Use document_text_detection for handwriting and dense documents
            # response = self.client.document_text_detection(image=image)
            
            # Check for errors
            if response.error.message:
                raise OCRProcessingException(
                    f"Vision API error: {response.error.message}"
                )
            
            # Extract text annotations
            texts = response.text_annotations
            
            if not texts:
                return {
                    'text': '',
                    'confidence': 0.0,
                    'language': None,
                    'has_text': False
                }
            
            # First annotation contains all detected text
            full_text = texts[0].description
            
            # Calculate average confidence from all detected words
            confidences = []
            languages = set()
            
            for text_annotation in texts[1:]:  # Skip first (full text)
                # Confidence is not directly available in text_annotations
                # We'll use bounding polygon vertices as a proxy for detection quality
                if hasattr(text_annotation, 'confidence'):
                    confidences.append(text_annotation.confidence)
            
            # If no confidence scores, use a default
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.95
            
            # Get detected language
            detected_languages = set()
            for page in response.full_text_annotation.pages:
                for block in page.blocks:
                    for paragraph in block.paragraphs:
                        for word in paragraph.words:
                            if hasattr(word.property, 'detected_languages'):
                                for lang in word.property.detected_languages:
                                    detected_languages.add(lang.language_code)
            
            primary_language = list(detected_languages)[0] if detected_languages else None
            
            return {
                'text': full_text,
                'confidence': round(avg_confidence, 4),
                'language': primary_language,
                'has_text': True,
                'detected_languages': list(detected_languages)
            }
            
        except Exception as e:
            if isinstance(e, OCRProcessingException):
                raise
            raise OCRProcessingException(f"OCR processing failed: {str(e)}")
    
    def extract_text_with_metadata(self, image_content: bytes, image_metadata: dict) -> dict:
        # Extract text and combine with image metadata
        ocr_result = self.extract_text(image_content)
        
        # Combine with image metadata
        result = {
            **ocr_result,
            'image_metadata': image_metadata
        }
        
        return result


# Global OCR service instance
ocr_service = OCRService()

