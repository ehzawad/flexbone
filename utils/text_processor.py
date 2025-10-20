import re


def clean_text(text: str) -> str:
    # Clean and format extracted text
    if not text:
        return ""
    
    # Remove multiple consecutive spaces
    text = re.sub(r' +', ' ', text)
    
    # Remove multiple consecutive newlines (keep max 2)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove spaces before punctuation
    text = re.sub(r'\s+([.,!?;:])', r'\1', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def normalize_line_breaks(text: str) -> str:
    # Normalize line breaks to consistent format
    # Convert all line breaks to \n
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    return text


def preprocess_text(text: str) -> str:
    # Complete text preprocessing pipeline
    text = normalize_line_breaks(text)
    text = clean_text(text)
    return text

