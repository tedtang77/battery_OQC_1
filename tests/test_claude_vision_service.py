import pytest
import json
import base64
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

import sys
sys.path.append('../backend')

from backend.services.claude_vision_service import ClaudeVisionService
from backend.models.battery import BatteryCellResponse

class TestClaudeVisionService:
    
    @pytest.fixture
    def mock_anthropic_client(self):
        """Mock Anthropic client"""
        mock_client = Mock()
        mock_message = Mock()
        mock_content = Mock()
        mock_content.text = '''
        {
            "batteries": [
                {
                    "serial_number": "C044160",
                    "model": "6754E4",
                    "energy": 36.74,
                    "capacity": 10.8,
                    "voltage": 3.40,
                    "confidence": 0.95
                }
            ],
            "total_batteries_found": 1,
            "recognition_method": "Claude AI Vision",
            "notes": "Clear image, high confidence detection"
        }
        '''
        mock_message.content = [mock_content]
        mock_client.messages.create.return_value = mock_message
        return mock_client
    
    @pytest.fixture
    def temp_image_file(self):
        """建立臨時測試圖片檔案"""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            # Create a simple test image data
            tmp.write(b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xFF\xDB\x00C\x00\xFF\xD9')
            tmp.flush()
            yield tmp.name
        os.unlink(tmp.name)
    
    @patch('backend.services.claude_vision_service.config')
    def test_init_with_api_key(self, mock_config):
        """測試有 API Key 的初始化"""
        mock_config.side_effect = lambda key, default='': {
            'ANTHROPIC_API_KEY': 'test-api-key',
            'CLAUDE_MODEL': 'claude-3-5-sonnet-20241022'
        }.get(key, default)
        
        with patch('backend.services.claude_vision_service.Anthropic') as mock_anthropic:
            service = ClaudeVisionService()
            
            assert service.is_available()
            assert service.api_key == 'test-api-key'
            assert service.model == 'claude-3-5-sonnet-20241022'
            mock_anthropic.assert_called_once_with(api_key='test-api-key')
    
    @patch('backend.services.claude_vision_service.config')
    def test_init_without_api_key(self, mock_config):
        """測試沒有 API Key 的初始化"""
        mock_config.side_effect = lambda key, default='': {
            'ANTHROPIC_API_KEY': '',
            'CLAUDE_MODEL': 'claude-3-5-sonnet-20241022'
        }.get(key, default)
        
        service = ClaudeVisionService()
        
        assert not service.is_available()
        assert service.client is None
    
    @patch('backend.services.claude_vision_service.config')
    def test_encode_image_to_base64_success(self, mock_config, temp_image_file):
        """測試成功編碼圖片為 base64"""
        mock_config.return_value = ''
        service = ClaudeVisionService()
        
        result = service.encode_image_to_base64(temp_image_file)
        
        assert result is not None
        assert isinstance(result, str)
        
        # Verify it's valid base64
        try:
            decoded = base64.b64decode(result)
            assert len(decoded) > 0
        except Exception:
            pytest.fail("Result is not valid base64")
    
    @patch('backend.services.claude_vision_service.config')
    def test_encode_image_to_base64_file_not_found(self, mock_config):
        """測試圖片檔案不存在"""
        mock_config.return_value = ''
        service = ClaudeVisionService()
        
        result = service.encode_image_to_base64('nonexistent.jpg')
        
        assert result is None
    
    @patch('backend.services.claude_vision_service.config')
    def test_create_battery_analysis_prompt(self, mock_config):
        """測試建立分析提示詞"""
        mock_config.return_value = ''
        service = ClaudeVisionService()
        
        prompt = service.create_battery_analysis_prompt()
        
        assert isinstance(prompt, str)
        assert 'Serial Number' in prompt
        assert 'Model' in prompt
        assert 'Energy' in prompt
        assert 'Capacity' in prompt
        assert 'Voltage' in prompt
        assert 'JSON' in prompt
    
    @patch('backend.services.claude_vision_service.config')
    async def test_analyze_battery_image_success(self, mock_config, mock_anthropic_client, temp_image_file):
        """測試成功分析電池圖片"""
        mock_config.side_effect = lambda key, default='': {
            'ANTHROPIC_API_KEY': 'test-api-key',
            'CLAUDE_MODEL': 'claude-3-5-sonnet-20241022'
        }.get(key, default)
        
        with patch('backend.services.claude_vision_service.Anthropic', return_value=mock_anthropic_client):
            service = ClaudeVisionService()
            
            result = await service.analyze_battery_image(temp_image_file, 'test.jpg')
            
            assert len(result) == 1
            battery = result[0]
            assert isinstance(battery, BatteryCellResponse)
            assert battery.serial_number == "C044160"
            assert battery.model == "6754E4"
            assert battery.energy == 36.74
            assert battery.capacity == 10.8
            assert battery.voltage == 3.40
            assert battery.image_file == 'test.jpg'
    
    @patch('backend.services.claude_vision_service.config')
    async def test_analyze_battery_image_service_not_available(self, mock_config, temp_image_file):
        """測試服務不可用時的情況"""
        mock_config.return_value = ''
        service = ClaudeVisionService()
        
        result = await service.analyze_battery_image(temp_image_file, 'test.jpg')
        
        assert result == []
    
    @patch('backend.services.claude_vision_service.config')
    async def test_analyze_battery_image_anthropic_error(self, mock_config, temp_image_file):
        """測試 Anthropic API 錯誤"""
        mock_config.side_effect = lambda key, default='': {
            'ANTHROPIC_API_KEY': 'test-api-key',
            'CLAUDE_MODEL': 'claude-3-5-sonnet-20241022'
        }.get(key, default)
        
        mock_client = Mock()
        mock_client.messages.create.side_effect = Exception("API Error")
        
        with patch('backend.services.claude_vision_service.Anthropic', return_value=mock_client):
            service = ClaudeVisionService()
            
            result = await service.analyze_battery_image(temp_image_file, 'test.jpg')
            
            assert result == []
    
    @patch('backend.services.claude_vision_service.config')
    def test_parse_claude_response_success(self, mock_config):
        """測試成功解析 Claude 回應"""
        mock_config.return_value = ''
        service = ClaudeVisionService()
        
        response_text = '''
        Here is the analysis:
        
        ```json
        {
            "batteries": [
                {
                    "serial_number": "C044160",
                    "model": "6754E4",
                    "energy": 36.74,
                    "capacity": 10.8,
                    "voltage": 3.40,
                    "confidence": 0.95
                }
            ],
            "total_batteries_found": 1,
            "notes": "High quality detection"
        }
        ```
        '''
        
        result = service.parse_claude_response(response_text, 'test.jpg')
        
        assert len(result) == 1
        battery = result[0]
        assert battery.serial_number == "C044160"
        assert battery.model == "6754E4"
        assert battery.energy == 36.74
    
    @patch('backend.services.claude_vision_service.config')
    def test_parse_claude_response_no_json(self, mock_config):
        """測試回應中沒有 JSON"""
        mock_config.return_value = ''
        service = ClaudeVisionService()
        
        response_text = "Sorry, I cannot identify any batteries in this image."
        
        result = service.parse_claude_response(response_text, 'test.jpg')
        
        assert result == []
    
    @patch('backend.services.claude_vision_service.config')
    def test_parse_claude_response_invalid_json(self, mock_config):
        """測試無效的 JSON"""
        mock_config.return_value = ''
        service = ClaudeVisionService()
        
        response_text = '''
        ```json
        {
            "batteries": [
                {
                    "serial_number": "C044160",
                    "model": "6754E4"
                    // Invalid JSON - missing comma
                }
            ]
        }
        ```
        '''
        
        result = service.parse_claude_response(response_text, 'test.jpg')
        
        assert result == []
    
    @patch('backend.services.claude_vision_service.config')
    def test_parse_claude_response_multiple_batteries(self, mock_config):
        """測試解析多顆電池"""
        mock_config.return_value = ''
        service = ClaudeVisionService()
        
        response_text = '''
        {
            "batteries": [
                {
                    "serial_number": "C044160",
                    "model": "6754E4",
                    "energy": 36.74,
                    "capacity": 10.8,
                    "voltage": 3.40
                },
                {
                    "serial_number": "C044161",
                    "model": "6754E5",
                    "energy": 37.20,
                    "capacity": 11.0,
                    "voltage": 3.38
                }
            ],
            "total_batteries_found": 2
        }
        '''
        
        result = service.parse_claude_response(response_text, 'test.jpg')
        
        assert len(result) == 2
        assert result[0].serial_number == "C044160"
        assert result[1].serial_number == "C044161"
    
    @patch('backend.services.claude_vision_service.config')
    def test_parse_claude_response_missing_data(self, mock_config):
        """測試缺少資料的情況"""
        mock_config.return_value = ''
        service = ClaudeVisionService()
        
        response_text = '''
        {
            "batteries": [
                {
                    "serial_number": "C044160",
                    "model": null,
                    "energy": null,
                    "capacity": 10.8,
                    "voltage": 3.40
                }
            ],
            "total_batteries_found": 1
        }
        '''
        
        result = service.parse_claude_response(response_text, 'test.jpg')
        
        assert len(result) == 1
        battery = result[0]
        assert battery.serial_number == "C044160"
        assert battery.model == "UNKNOWN"
        assert battery.energy == 0.0
        assert battery.capacity == 10.8
        assert battery.voltage == 3.40
    
    @patch('backend.services.claude_vision_service.config')
    def test_get_service_info_with_api_key(self, mock_config):
        """測試取得服務資訊（有 API Key）"""
        mock_config.side_effect = lambda key, default='': {
            'ANTHROPIC_API_KEY': 'test-api-key',
            'CLAUDE_MODEL': 'claude-3-5-sonnet-20241022'
        }.get(key, default)
        
        with patch('backend.services.claude_vision_service.Anthropic'):
            service = ClaudeVisionService()
            info = service.get_service_info()
            
            assert info['service_name'] == 'Claude AI Vision'
            assert info['available'] == True
            assert info['model'] == 'claude-3-5-sonnet-20241022'
            assert info['api_key_configured'] == True
    
    @patch('backend.services.claude_vision_service.config')
    def test_get_service_info_without_api_key(self, mock_config):
        """測試取得服務資訊（沒有 API Key）"""
        mock_config.return_value = ''
        service = ClaudeVisionService()
        info = service.get_service_info()
        
        assert info['service_name'] == 'Claude AI Vision'
        assert info['available'] == False
        assert info['model'] == None
        assert info['api_key_configured'] == False
    
    @patch('backend.services.claude_vision_service.config')
    async def test_analyze_image_with_confidence_scores(self, mock_config, temp_image_file):
        """測試包含信心度分數的分析"""
        mock_config.side_effect = lambda key, default='': {
            'ANTHROPIC_API_KEY': 'test-api-key',
            'CLAUDE_MODEL': 'claude-3-5-sonnet-20241022'
        }.get(key, default)
        
        mock_client = Mock()
        mock_message = Mock()
        mock_content = Mock()
        mock_content.text = '''
        {
            "batteries": [
                {
                    "serial_number": "C044160",
                    "model": "6754E4",
                    "energy": 36.74,
                    "capacity": 10.8,
                    "voltage": 3.40,
                    "confidence": 0.85
                }
            ],
            "total_batteries_found": 1,
            "notes": "Moderate lighting conditions"
        }
        '''
        mock_message.content = [mock_content]
        mock_client.messages.create.return_value = mock_message
        
        with patch('backend.services.claude_vision_service.Anthropic', return_value=mock_client):
            service = ClaudeVisionService()
            result = await service.analyze_battery_image(temp_image_file, 'test.jpg')
            
            assert len(result) == 1
            # Note: confidence is mentioned in the response but not stored in BatteryCellResponse
            # This is expected behavior as we don't have a confidence field in the model