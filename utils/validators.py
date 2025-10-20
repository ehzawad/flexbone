import io
from PIL import Image
from fastapi import UploadFile
from config import config
from utils.error_handlers import (
    InvalidFileFormatException,
    FileSizeExceededException,
    InvalidFileException
)
from utils.corruption_detector import detect_corruption, attempt_repair


def validate_file_signature(file_content: bytes) -> str:
    # Validate file by checking its magic number (file signature)
    for signature, format_type in config.FILE_SIGNATURES.items():
        if file_content.startswith(signature):
            return format_type
    
    raise InvalidFileFormatException(
        "Invalid image file. Please upload a valid image (JPG, PNG, GIF, WebP, or BMP)."
    )


def validate_file_extension(filename: str) -> str:
    # Validate file extension
    if not filename:
        raise InvalidFileFormatException("No filename provided.")
    
    extension = filename.lower().split('.')[-1]
    if extension not in config.ALLOWED_EXTENSIONS:
        raise InvalidFileFormatException(
            f"Unsupported file type '.{extension}'. Supported: JPG, PNG, GIF, WebP, BMP"
        )
    
    return extension


def validate_mime_type(content_type: str) -> None:
    # Validate MIME type (flexible for curl/browsers)
    # Allow application/octet-stream if other validations pass (for curl uploads)
    if content_type == 'application/octet-stream':
        return  # Will be validated by file signature
    
    if content_type not in config.ALLOWED_MIME_TYPES:
        raise InvalidFileFormatException(
            f"Unsupported file type. Please upload a valid image file (JPG, PNG, GIF, WebP, or BMP)."
        )


def validate_file_size(file_size: int) -> None:
    # Validate file size
    if file_size == 0:
        raise InvalidFileException("File is empty. Please upload a valid image.")
    
    if file_size > config.MAX_FILE_SIZE_BYTES:
        raise FileSizeExceededException(
            f"File too large ({file_size / 1024 / 1024:.1f}MB). Maximum size is {config.MAX_FILE_SIZE_MB}MB."
        )


def validate_image_integrity(file_content: bytes) -> tuple[dict, bytes]:
    # Validate that the file is a valid image and extract metadata
    try:
        # First, detect corruption
        corruption_check = detect_corruption(file_content)
        
        if corruption_check['is_corrupted']:
            # Attempt repair
            repaired_content = attempt_repair(file_content)
            # Re-check after repair
            try:
                corruption_check = detect_corruption(repaired_content)
                if corruption_check['is_corrupted']:
                    raise InvalidFileException(
                        f"Image file is corrupted and could not be repaired: {', '.join(corruption_check['issues'])}"
                    )
                file_content = repaired_content
            except Exception as e:
                raise InvalidFileException(f"Image file is corrupted beyond repair: {str(e)}")
        
        # Extract metadata
        img = Image.open(io.BytesIO(file_content))
        
        metadata = {
            "width": img.width,
            "height": img.height,
            "format": img.format,
            "mode": img.mode
        }
        
        return metadata, file_content
        
    except InvalidFileException:
        raise
    except Exception as e:
        raise InvalidFileException(f"Invalid or corrupted image file: {str(e)}")


async def validate_upload_file(file: UploadFile) -> tuple[bytes, dict]:
    # Comprehensive file validation with corruption detection and repair
    # Validate extension
    validate_file_extension(file.filename)
    
    # Validate MIME type
    validate_mime_type(file.content_type)
    
    # Read file content
    file_content = await file.read()
    
    # Validate file size
    validate_file_size(len(file_content))
    
    # Validate file signature
    validate_file_signature(file_content)
    
    # Validate image integrity, detect corruption, and get metadata
    # This may return repaired content if minor corruption was fixed
    metadata, file_content = validate_image_integrity(file_content)
    
    return file_content, metadata

