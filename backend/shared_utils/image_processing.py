import cv2
import numpy as np

def enhance_image_cv2(image):
    """
    Enhance image using OpenCV for better OCR results.
    Args:
        image: numpy array in BGR format
    Returns:
        enhanced image as numpy array in BGR format
    """
    try:
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Increase contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        contrast = clahe.apply(denoised)
        
        # Adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            contrast,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,  # block size
            2    # constant subtracted from mean
        )
        
        # Convert back to BGR for OCR
        return cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
    except Exception as e:
        raise RuntimeError(f"Image enhancement failed: {str(e)}")

def classify_text(text: str) -> dict:
    """
    Classify text as either a name or date of birth.
    Args:
        text: string to classify
    Returns:
        dict with 'name' and 'dob' fields
    """
    import re
    try:
        text = text.strip()
        if not text:
            return None
            
        result = {"name": "", "dob": None}
        
        # Case 1: Line contains both name and DOB
        dob_split = re.split(r'(?i)(?:DOB:?|D\.O\.B\.?:?)\s*', text)
        if len(dob_split) == 2:
            name = dob_split[0].strip().strip(',.') # Clean up name
            dob = dob_split[1].strip()
            if name:  # Only set name if we found one
                result["name"] = name
            result["dob"] = dob.strip('.')  # Remove trailing periods
            return result
            
        # Case 2: Standalone DOB patterns
        dob_match = re.match(r'(?i)^(?:DOB|D\.O\.B\.?|DATE\s+OF\s+BIRTH)[:\s]*(.+)$', text)
        if dob_match:
            # Extract just the date part
            date_part = dob_match.group(1).strip('.')
            result["dob"] = date_part
            return result
            
        # Case 3: Text looks like a name with trailing period
        if text.endswith('.'):
            text_without_period = text[:-1].strip()
            if re.search(r'^[A-Za-z,\s-]+$', text_without_period):
                result["name"] = text_without_period
                return result
                
        # Case 4: Text looks like a name
        if re.search(r'^[A-Za-z,.\s-]+$', text):
            name = text.strip(',.') # Remove trailing punctuation
            if ',' in name:  # Handle "Last, First" format
                parts = name.split(',')
                if len(parts) == 2:
                    name = f"{parts[1].strip()} {parts[0].strip()}"
            if len(name) > 1:  # Skip single letters
                result["name"] = name
                return result
                
        # Case 5: Text looks like a date (but not a year by itself)
        date_pattern = r'\b\d{1,2}[-/.]\d{1,2}(?:[-/.]\d{2,4})?\b'
        if re.search(date_pattern, text):
            if not re.match(r'^\d{4}$', text):  # Skip standalone years
                result["dob"] = text.strip('.')  # Remove trailing periods
                return result
                
        # Case 6: If nothing else matched and it's not just numbers
        if not re.match(r'^\d+$', text):
            result["name"] = text.strip('.')  # Remove trailing periods
            
        return result if (result["name"] or result["dob"]) else None
            
    except Exception as e:
        raise ValueError(f"Text classification failed: {str(e)}")


