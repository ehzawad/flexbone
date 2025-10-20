class OCRAPIException(Exception):
    # Base exception for OCR API
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class InvalidFileFormatException(OCRAPIException):
    # Raised when file format is invalid
    def __init__(self, message: str = "Unsupported file format. Please upload JPG, PNG, GIF, WebP, or BMP."):
        super().__init__(message, status_code=415)


class FileSizeExceededException(OCRAPIException):
    # Raised when file size exceeds limit
    def __init__(self, message: str = "File too large. Maximum size is 10MB."):
        super().__init__(message, status_code=413)


class InvalidFileException(OCRAPIException):
    # Raised when file is invalid or corrupted
    def __init__(self, message: str = "Invalid or corrupted image file. Please try another image."):
        super().__init__(message, status_code=400)


class OCRProcessingException(OCRAPIException):
    # Raised when OCR processing fails
    def __init__(self, message: str = "OCR processing failed"):
        super().__init__(message, status_code=500)


class BatchSizeExceededException(OCRAPIException):
    # Raised when batch size exceeds limit
    def __init__(self, message: str = "Too many images. Maximum is 10 images per batch."):
        super().__init__(message, status_code=400)

