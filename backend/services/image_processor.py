import cv2
import pytesseract
from PIL import Image
import numpy as np
import re
from typing import List, Optional, Dict
import os
import logging
from decouple import config

from models.battery import BatteryCellResponse
from services.claude_vision_service import ClaudeVisionService

logger = logging.getLogger(__name__)

class ImageProcessor:
    def __init__(self):
        # Configure Tesseract path if needed
        tesseract_cmd = config('TESSERACT_CMD', default='tesseract')
        if tesseract_cmd != 'tesseract':
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        
        # Initialize Claude Vision Service
        self.claude_service = ClaudeVisionService()
        
        logger.info(f"ImageProcessor initialized - Claude AI available: {self.claude_service.is_available()}")
    
    async def process_image(self, image_path: str) -> List[BatteryCellResponse]:
        """
        處理單張圖片並提取電池資訊
        優先使用 Claude AI，如果不可用則使用傳統 OCR
        """
        image_filename = os.path.basename(image_path)
        
        try:
            # 優先使用 Claude AI 進行圖片識別
            if self.claude_service.is_available():
                logger.info(f"Using Claude AI to analyze {image_filename}")
                batteries = await self.claude_service.analyze_battery_image(image_path, image_filename)
                
                if batteries:
                    logger.info(f"Claude AI successfully identified {len(batteries)} batteries in {image_filename}")
                    # 為每個電池添加識別方法標記
                    for battery in batteries:
                        if hasattr(battery, 'recognition_method'):
                            battery.recognition_method = "Claude AI"
                    return batteries
                else:
                    logger.warning(f"Claude AI failed to identify batteries in {image_filename}, falling back to OCR")
            
            # 使用傳統 OCR 方法作為備用
            logger.info(f"Using traditional OCR to analyze {image_filename}")
            return await self.process_image_with_ocr(image_path)
            
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {str(e)}")
            return []
    
    async def process_image_with_ocr(self, image_path: str) -> List[BatteryCellResponse]:
        """使用傳統 OCR 方法處理圖片"""
        image_filename = os.path.basename(image_path)
        
        try:
            # Load and preprocess image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Cannot load image: {image_path}")
            
            processed_image = self.preprocess_image(image)
            
            # Extract text using OCR
            text = pytesseract.image_to_string(processed_image, config='--psm 6')
            logger.debug(f"OCR extracted text from {image_filename}: {text[:100]}...")
            
            # Extract battery information from text
            batteries = self.extract_battery_info(text, image_filename)
            
            # 為每個電池添加識別方法標記
            for battery in batteries:
                if hasattr(battery, 'recognition_method'):
                    battery.recognition_method = "Traditional OCR"
            
            logger.info(f"Traditional OCR identified {len(batteries)} batteries in {image_filename}")
            return batteries
            
        except Exception as e:
            logger.error(f"Error processing image with OCR {image_path}: {str(e)}")
            return []
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """預處理圖片以提高OCR準確率"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(enhanced, (1, 1), 0)
        
        # Threshold to get better text contrast
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return thresh
    
    def extract_battery_info(self, text: str, image_file: str) -> List[BatteryCellResponse]:
        """從OCR文字中提取電池資訊"""
        batteries = []
        
        # Regular expressions for extracting battery information
        patterns = {
            'serial_number': r'([A-Z]\d{6})',  # Format like C044160
            'model': r'(\d{4}[A-Z]\d)',       # Format like 6754E4
            'energy': r'(\d+\.?\d*)\s*Wh',    # Format like 36.74Wh
            'capacity': r'(\d+\.?\d*)\s*Ah',  # Format like 10.8Ah
            'voltage': r'(\d+\.?\d*)\s*V'     # Format like 3.40V
        }
        
        # Find all matches for each pattern
        matches = {}
        for key, pattern in patterns.items():
            matches[key] = re.findall(pattern, text, re.IGNORECASE)
        
        # Determine the number of batteries (use the maximum count from any field)
        max_count = max(len(matches[key]) for key in matches)
        
        # Create battery objects
        for i in range(max_count):
            try:
                battery = BatteryCellResponse(
                    serial_number=matches['serial_number'][i] if i < len(matches['serial_number']) else f"UNKNOWN_{i+1}",
                    model=matches['model'][i] if i < len(matches['model']) else "UNKNOWN",
                    energy=float(matches['energy'][i]) if i < len(matches['energy']) else 0.0,
                    capacity=float(matches['capacity'][i]) if i < len(matches['capacity']) else 0.0,
                    voltage=float(matches['voltage'][i]) if i < len(matches['voltage']) else 0.0,
                    image_file=image_file
                )
                batteries.append(battery)
            except (IndexError, ValueError) as e:
                print(f"Error creating battery {i+1}: {str(e)}")
                continue
        
        return batteries
    
    def detect_battery_regions(self, image: np.ndarray) -> List[np.ndarray]:
        """檢測圖片中的電池區域（進階功能）"""
        # This is a placeholder for more advanced battery detection
        # Could use contour detection or machine learning for better accuracy
        
        # Simple approach: divide image into grid regions
        height, width = image.shape[:2]
        regions = []
        
        # Assume batteries are arranged in a grid pattern
        rows, cols = 2, 4  # Adjustable based on typical layouts
        
        for row in range(rows):
            for col in range(cols):
                y1 = (height // rows) * row
                y2 = (height // rows) * (row + 1)
                x1 = (width // cols) * col
                x2 = (width // cols) * (col + 1)
                
                region = image[y1:y2, x1:x2]
                regions.append(region)
        
        return regions
    
    def get_recognition_status(self) -> Dict:
        """取得圖片識別服務狀態"""
        claude_info = self.claude_service.get_service_info()
        
        return {
            'claude_ai': claude_info,
            'traditional_ocr': {
                'service_name': 'Traditional OCR',
                'available': True,
                'description': 'OpenCV + Tesseract OCR 傳統識別方法',
                'tesseract_cmd': config('TESSERACT_CMD', default='tesseract')
            },
            'preferred_method': 'Claude AI' if claude_info['available'] else 'Traditional OCR'
        }