import pytest
import numpy as np
import cv2
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock

import sys
sys.path.append('../backend')

from backend.services.image_processor import ImageProcessor
from backend.models.battery import BatteryCellResponse

class TestImageProcessor:
    
    @pytest.fixture
    def image_processor(self):
        """測試用的 ImageProcessor 實例"""
        return ImageProcessor()
    
    @pytest.fixture
    def sample_image(self):
        """建立測試用的圖片"""
        # Create a simple test image
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        # Add some text-like patterns
        cv2.rectangle(image, (50, 50), (200, 100), (255, 255, 255), -1)
        cv2.putText(image, 'C044160', (60, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        
        return image
    
    @pytest.fixture
    def temp_image_file(self, sample_image):
        """建立暫時的測試圖片檔案"""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            cv2.imwrite(tmp.name, sample_image)
            yield tmp.name
        os.unlink(tmp.name)
    
    def test_preprocess_image(self, image_processor, sample_image):
        """測試圖片預處理功能"""
        processed = image_processor.preprocess_image(sample_image)
        
        # Check that preprocessing returns a grayscale image
        assert len(processed.shape) == 2
        assert processed.dtype == np.uint8
        
        # Check that the processed image has same dimensions as input
        assert processed.shape[:2] == sample_image.shape[:2]
    
    def test_extract_battery_info_with_valid_text(self, image_processor):
        """測試從有效文字中提取電池資訊"""
        test_text = """
        Battery Information
        Serial: C044160
        Model: 6754E4
        Energy: 36.74Wh
        Capacity: 10.8Ah
        Voltage: 3.40V
        """
        
        batteries = image_processor.extract_battery_info(test_text, "test.jpg")
        
        assert len(batteries) == 1
        battery = batteries[0]
        
        assert isinstance(battery, BatteryCellResponse)
        assert battery.serial_number == "C044160"
        assert battery.model == "6754E4"
        assert battery.energy == 36.74
        assert battery.capacity == 10.8
        assert battery.voltage == 3.40
        assert battery.image_file == "test.jpg"
    
    def test_extract_battery_info_multiple_batteries(self, image_processor):
        """測試提取多顆電池資訊"""
        test_text = """
        Battery 1: C044160, Model 6754E4, 36.74Wh, 10.8Ah, 3.40V
        Battery 2: C044161, Model 6754E5, 37.20Wh, 11.0Ah, 3.38V
        """
        
        batteries = image_processor.extract_battery_info(test_text, "test.jpg")
        
        assert len(batteries) == 2
        
        # Check first battery
        assert batteries[0].serial_number == "C044160"
        assert batteries[0].model == "6754E4"
        assert batteries[0].energy == 36.74
        
        # Check second battery
        assert batteries[1].serial_number == "C044161"
        assert batteries[1].model == "6754E5"
        assert batteries[1].energy == 37.20
    
    def test_extract_battery_info_no_matches(self, image_processor):
        """測試沒有匹配資訊的情況"""
        test_text = "This is just random text with no battery information"
        
        batteries = image_processor.extract_battery_info(test_text, "test.jpg")
        
        assert len(batteries) == 0
    
    def test_extract_battery_info_partial_matches(self, image_processor):
        """測試部分匹配的情況"""
        test_text = """
        Serial: C044160
        Energy: 36.74Wh
        """
        
        batteries = image_processor.extract_battery_info(test_text, "test.jpg")
        
        assert len(batteries) == 1
        battery = batteries[0]
        
        assert battery.serial_number == "C044160"
        assert battery.energy == 36.74
        assert battery.model == "UNKNOWN"  # Should have default value
        assert battery.capacity == 0.0  # Should have default value
        assert battery.voltage == 0.0  # Should have default value
    
    @patch('pytesseract.image_to_string')
    @patch('cv2.imread')
    async def test_process_image_success(self, mock_imread, mock_ocr, image_processor, sample_image):
        """測試成功處理圖片"""
        # Setup mocks
        mock_imread.return_value = sample_image
        mock_ocr.return_value = "Serial: C044160 Model: 6754E4 Energy: 36.74Wh Capacity: 10.8Ah Voltage: 3.40V"
        
        result = await image_processor.process_image("test.jpg")
        
        assert len(result) == 1
        assert isinstance(result[0], BatteryCellResponse)
        assert result[0].serial_number == "C044160"
    
    @patch('cv2.imread')
    async def test_process_image_file_not_found(self, mock_imread, image_processor):
        """測試圖片檔案不存在的情況"""
        mock_imread.return_value = None
        
        result = await image_processor.process_image("nonexistent.jpg")
        
        assert result == []
    
    @patch('pytesseract.image_to_string')
    @patch('cv2.imread')
    async def test_process_image_ocr_error(self, mock_imread, mock_ocr, image_processor, sample_image):
        """測試 OCR 錯誤的情況"""
        mock_imread.return_value = sample_image
        mock_ocr.side_effect = Exception("OCR Error")
        
        result = await image_processor.process_image("test.jpg")
        
        assert result == []
    
    def test_detect_battery_regions(self, image_processor, sample_image):
        """測試電池區域檢測功能"""
        regions = image_processor.detect_battery_regions(sample_image)
        
        assert len(regions) == 8  # 2 rows x 4 cols
        
        for region in regions:
            assert isinstance(region, np.ndarray)
            assert len(region.shape) >= 2  # Should be at least 2D
    
    def test_serial_number_regex_patterns(self, image_processor):
        """測試序號正規表達式"""
        test_cases = [
            ("Serial: C044160", "C044160"),
            ("C123456", "C123456"),
            ("A987654", "A987654"),
            ("serial number: B555555", "B555555"),
            ("invalid serial", None)
        ]
        
        for test_text, expected in test_cases:
            batteries = image_processor.extract_battery_info(test_text, "test.jpg")
            
            if expected:
                assert len(batteries) >= 1
                assert batteries[0].serial_number == expected
            else:
                if batteries:
                    assert batteries[0].serial_number.startswith("UNKNOWN")
    
    def test_model_regex_patterns(self, image_processor):
        """測試型號正規表達式"""
        test_cases = [
            ("Model: 6754E4", "6754E4"),
            ("6754E5", "6754E5"),
            ("1234A9", "1234A9"),
            ("invalid model", None)
        ]
        
        for test_text, expected in test_cases:
            batteries = image_processor.extract_battery_info(test_text, "test.jpg")
            
            if expected:
                assert len(batteries) >= 1
                assert batteries[0].model == expected
            else:
                if batteries:
                    assert batteries[0].model == "UNKNOWN"
    
    def test_energy_regex_patterns(self, image_processor):
        """測試能量正規表達式"""
        test_cases = [
            ("Energy: 36.74Wh", 36.74),
            ("36Wh", 36.0),
            ("37.5 Wh", 37.5),
            ("invalid energy", 0.0)
        ]
        
        for test_text, expected in test_cases:
            batteries = image_processor.extract_battery_info(test_text, "test.jpg")
            
            if expected > 0:
                assert len(batteries) >= 1
                assert batteries[0].energy == expected
            else:
                if batteries:
                    assert batteries[0].energy == 0.0