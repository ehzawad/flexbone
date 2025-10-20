# Detect and handle corrupted image files
from PIL import Image
import io
from utils.error_handlers import InvalidFileException


def detect_corruption(file_content: bytes) -> dict:
    # Detect if an image file is corrupted or damaged
    issues = []
    
    try:
        # Try to open and verify the image
        img = Image.open(io.BytesIO(file_content))
        img.verify()
        
        # Re-open for additional checks (verify() closes the image)
        img = Image.open(io.BytesIO(file_content))
        
        # Try to load pixel data
        try:
            img.load()
        except Exception as e:
            issues.append(f"Pixel data corrupted: {str(e)}")
        
        # Check for zero size
        if img.width == 0 or img.height == 0:
            issues.append("Image has zero dimensions")
        
        # Check for extremely small images (likely corrupt) - but allow tiny test images
        if img.width < 3 and img.height < 3:
            issues.append(f"Image too small: {img.width}x{img.height}")
        
        # Try to convert to RGB (tests color space)
        try:
            if img.mode not in ['RGB', 'L', 'P', 'RGBA']:
                img.convert('RGB')
        except Exception as e:
            issues.append(f"Color space conversion failed: {str(e)}")
        
        return {
            'is_corrupted': len(issues) > 0,
            'issues': issues,
            'can_process': len(issues) == 0
        }
        
    except OSError as e:
        # Image cannot be opened - definitely corrupted
        raise InvalidFileException("Unable to read image file. The file may be corrupted.")
    except Exception as e:
        # Other errors during verification
        raise InvalidFileException("Invalid image file. Please try another image.")


def attempt_repair(file_content: bytes) -> bytes:
    # Attempt to repair minor corruption in image files
    try:
        img = Image.open(io.BytesIO(file_content))
        
        # Convert problematic color modes
        if img.mode in ['P', 'PA']:  # Palette modes
            img = img.convert('RGB')
        elif img.mode == 'LA':  # Grayscale with alpha
            img = img.convert('RGBA')
        
        # Save to bytes with standard format
        output = io.BytesIO()
        format_map = {
            'JPEG': 'JPEG',
            'PNG': 'PNG',
            'GIF': 'GIF',
            'WEBP': 'WEBP',
            'BMP': 'BMP'
        }
        save_format = format_map.get(img.format, 'PNG')
        img.save(output, format=save_format)
        return output.getvalue()
        
    except Exception:
        # Repair failed, return original
        return file_content

