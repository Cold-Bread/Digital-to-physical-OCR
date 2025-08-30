import cv2
import numpy as np
from PIL import Image, ImageEnhance

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

def enhance_image_pil(image):
    """
    Enhance image using PIL for better OCR results.
    Args:
        image: PIL Image object
    Returns:
        enhanced PIL Image object
    """
    try:
        # Convert to grayscale while keeping RGB format
        gray = ImageEnhance.Color(image).enhance(0.0)
        
        # Enhance contrast
        contrast = ImageEnhance.Contrast(gray).enhance(2.0)
        
        # Enhance sharpness
        sharp = ImageEnhance.Sharpness(contrast).enhance(1.5)
        
        # Enhance brightness
        bright = ImageEnhance.Brightness(sharp).enhance(1.2)
        
        return bright
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

def extract_text_regions(image, method='vertical_slice'):
    """
    Extract regions from an image for better OCR processing.
    Args:
        image: numpy array (CV2 image) or PIL Image
        method: str, 'vertical_slice' or 'overlap'
    Returns:
        list of numpy arrays (CV2 images)
    """
    try:
        # Convert PIL Image to CV2 if needed
        if not isinstance(image, np.ndarray):
            image = np.array(image)
        
        if method == 'vertical_slice':
            return _extract_vertical_slices(image)
        else:
            return _extract_overlapping_regions(image)
    except Exception as e:
        raise RuntimeError(f"Region extraction failed: {str(e)}")

def _extract_vertical_slices(image):
    """
    Split image into vertical slices based on text line detection.
    Returns list of CV2 images.
    """
    # Convert to grayscale if not already
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
        
    # Apply threshold to get binary image
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Get horizontal projection profile
    horizontal_proj = np.sum(binary, axis=1)
    
    # Find potential text line boundaries
    boundaries = []
    in_text = False
    min_gap = 5  # Minimum pixel gap between text lines
    
    for i, proj in enumerate(horizontal_proj):
        if not in_text and proj > 0:
            # Start of text line
            if not boundaries or i - boundaries[-1][1] >= min_gap:
                boundaries.append([i, i])
                in_text = True
        elif in_text and proj == 0:
            # End of text line
            boundaries[-1][1] = i
            in_text = False
    
    # Extract regions with padding
    regions = []
    padding = 5  # Pixels of padding above and below each line
    
    for start, end in boundaries:
        # Add padding but stay within image bounds
        y_start = max(0, start - padding)
        y_end = min(image.shape[0], end + padding)
        
        # Extract the region
        region = image[y_start:y_end, :]
        
        # Only keep regions that are likely to contain text
        if region.shape[0] > 10:  # Minimum height threshold
            regions.append(region)
    
    return regions

def _extract_overlapping_regions(image, region_height_factor=3):
    """
    Extract overlapping regions from an image.
    Returns list of CV2 images.
    """
    height = image.shape[0]
    regions = []
    
    # Create overlapping regions
    for i in range(0, height, height//(region_height_factor*2)):
        region_height = height//region_height_factor
        start = max(0, i - region_height//4)
        end = min(height, i + region_height)
        region = image[start:end, :]
        regions.append(region)
        
    return regions
