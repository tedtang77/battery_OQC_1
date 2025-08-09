import base64
import json
from typing import List, Optional, Dict, Any
from anthropic import Anthropic
from decouple import config
import logging

from models.battery import BatteryCellResponse

logger = logging.getLogger(__name__)

class ClaudeVisionService:
    """
    Anthropic Claude AI 圖片識別服務
    用於識別電池芯的各項參數資訊
    """
    
    def __init__(self):
        self.api_key = config('ANTHROPIC_API_KEY', default='')
        self.model = config('CLAUDE_MODEL', default='claude-3-5-sonnet-20241022')
        
        if self.api_key:
            self.client = Anthropic(api_key=self.api_key)
            logger.info("Claude Vision Service initialized with API key")
        else:
            self.client = None
            logger.info("Claude Vision Service initialized without API key (will use fallback OCR)")
    
    def is_available(self) -> bool:
        """檢查 Claude AI 服務是否可用"""
        return self.client is not None and bool(self.api_key)
    
    def encode_image_to_base64(self, image_path: str) -> Optional[str]:
        """將圖片編碼為 base64 格式"""
        try:
            with open(image_path, 'rb') as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding image {image_path}: {str(e)}")
            return None
    
    def create_battery_analysis_prompt(self) -> str:
        """建立電池分析提示詞"""
        return """
您是一個專業的電池品質檢查專家。請分析這張電池芯的照片，並提取以下資訊：

1. Serial Number (序號) - 通常是類似 C044160 的格式
2. Model (型號) - 通常是類似 6754E4 的格式  
3. Energy (能量) - 以 Wh 為單位，例如 36.74Wh
4. Capacity (容量) - 以 Ah 為單位，例如 10.8Ah
5. Voltage (電壓) - 以 V 為單位，例如 3.40V

圖片中可能包含多顆電池芯，請識別每一顆電池的完整資訊。

請以以下 JSON 格式回覆，確保格式正確：

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
  "recognition_method": "Claude AI Vision",
  "notes": "任何額外的觀察或註記"
}
```

重要注意事項：
- 如果某個值無法識別，請使用 null
- confidence 是您對識別結果的信心度 (0-1)
- 請仔細檢查數字的準確性
- 如果圖片模糊或資訊不清楚，請在 notes 中說明

請開始分析圖片：
"""
    
    async def analyze_battery_image(self, image_path: str, image_filename: str) -> List[BatteryCellResponse]:
        """
        使用 Claude AI 分析電池圖片
        
        Args:
            image_path: 圖片檔案路徑
            image_filename: 圖片檔案名稱
            
        Returns:
            識別到的電池資料列表
        """
        if not self.is_available():
            logger.warning("Claude AI service not available")
            return []
        
        try:
            # 編碼圖片
            base64_image = self.encode_image_to_base64(image_path)
            if not base64_image:
                return []
            
            # 準備訊息
            prompt = self.create_battery_analysis_prompt()
            
            # 調用 Claude API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": base64_image
                                }
                            }
                        ]
                    }
                ]
            )
            
            # 解析回應
            response_text = message.content[0].text
            logger.info(f"Claude AI response for {image_filename}: {response_text[:200]}...")
            
            # 從回應中提取 JSON
            batteries = self.parse_claude_response(response_text, image_filename)
            
            logger.info(f"Claude AI identified {len(batteries)} batteries in {image_filename}")
            return batteries
            
        except Exception as e:
            logger.error(f"Error analyzing image with Claude AI: {str(e)}")
            return []
    
    def parse_claude_response(self, response_text: str, image_filename: str) -> List[BatteryCellResponse]:
        """
        解析 Claude AI 的回應並轉換為電池資料物件
        
        Args:
            response_text: Claude AI 的回應文字
            image_filename: 圖片檔案名稱
            
        Returns:
            電池資料物件列表
        """
        try:
            # 嘗試從回應中提取 JSON
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.warning(f"No JSON found in Claude response for {image_filename}")
                return []
            
            json_text = response_text[json_start:json_end]
            
            # 清理可能的 markdown 格式
            if '```json' in response_text:
                lines = response_text.split('\n')
                json_lines = []
                in_json = False
                
                for line in lines:
                    if '```json' in line:
                        in_json = True
                        continue
                    elif '```' in line and in_json:
                        break
                    elif in_json:
                        json_lines.append(line)
                
                if json_lines:
                    json_text = '\n'.join(json_lines)
            
            # 解析 JSON
            data = json.loads(json_text)
            
            batteries = []
            battery_list = data.get('batteries', [])
            
            for i, battery_data in enumerate(battery_list):
                try:
                    battery = BatteryCellResponse(
                        serial_number=battery_data.get('serial_number') or f"CLAUDE_UNKNOWN_{i+1}",
                        model=battery_data.get('model') or "UNKNOWN",
                        energy=float(battery_data.get('energy') or 0.0),
                        capacity=float(battery_data.get('capacity') or 0.0),
                        voltage=float(battery_data.get('voltage') or 0.0),
                        image_file=image_filename
                    )
                    batteries.append(battery)
                    
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error parsing battery data {i+1} from Claude response: {str(e)}")
                    continue
            
            # 記錄額外資訊
            total_found = data.get('total_batteries_found', len(batteries))
            notes = data.get('notes', '')
            
            logger.info(f"Claude AI found {total_found} batteries in {image_filename}")
            if notes:
                logger.info(f"Claude AI notes for {image_filename}: {notes}")
            
            return batteries
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Claude JSON response for {image_filename}: {str(e)}")
            logger.debug(f"Raw response: {response_text}")
            return []
        except Exception as e:
            logger.error(f"Error processing Claude response for {image_filename}: {str(e)}")
            return []
    
    def get_service_info(self) -> Dict[str, Any]:
        """取得服務資訊"""
        return {
            'service_name': 'Claude AI Vision',
            'available': self.is_available(),
            'model': self.model if self.is_available() else None,
            'api_key_configured': bool(self.api_key),
            'description': 'Anthropic Claude AI 圖片識別服務'
        }