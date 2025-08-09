# 電池 OQC 系統測試指南

本系統包含完整的測試套件，確保圖片識別功能的正確性和穩定性。

## 🧪 測試類型

### 1. 單元測試 (Unit Tests)
測試個別組件的功能是否正確：
- `test_image_processor.py` - 圖片處理器測試
- `test_database_service.py` - 資料庫服務測試
- `test_csv_exporter.py` - CSV匯出器測試
- `test_main_api.py` - API端點測試
- `test_claude_vision_service.py` - Claude AI服務測試

### 2. 真實圖片識別測試 (Real Image Recognition Tests)
**⭐ 重要：這是專門針對您提供的測試案例設計的測試**

測試特定照片的識別準確性：
- `test_real_image_recognition.py` - 真實照片識別驗證

#### 測試案例
- **Test 1**: `PXL_20250724_010217469.jpg` - 4個電池
- **Test 2**: `PXL_20250724_010602031.jpg` - 8個電池

#### 預期結果驗證
系統會檢查識別出的電池是否符合預期：
- 電池總數是否正確
- 序號 (Serial Number) 是否匹配
- 型號 (Model) 是否正確
- 能量、容量、電壓數值是否準確

## 🚀 執行測試

### 快速執行所有測試
```bash
# 執行完整測試套件 (包含準確性測試)
python run_tests.py

# 只執行準確性測試
python run_accuracy_tests.py
```

### 單獨執行特定測試
```bash
# 執行真實圖片識別測試
pytest tests/test_real_image_recognition.py -v -s

# 執行特定測試案例
pytest tests/test_real_image_recognition.py::TestRealImageRecognition::test_image_recognition_pxl_010217469 -v -s

# 執行識別方法比較測試
pytest tests/test_real_image_recognition.py::TestRealImageRecognition::test_recognition_methods_comparison -v -s
```

### 單元測試
```bash
# 執行所有單元測試
pytest tests/ -v

# 執行特定組件測試
pytest tests/test_claude_vision_service.py -v
```

## 📊 測試結果解讀

### 準確性測試輸出範例
```
=== PXL_20250724_010217469.jpg 識別結果 ===
預期電池數: 4, 實際識別: 4
完美匹配: 3/4
良好匹配: 4/4

電池 1:
  識別: C048026, 6754E4, 36.72Wh, 10.8Ah, 3.40V
  預期: C048026, 6754E4, 36.72Wh, 10.8Ah, 3.40V
  匹配度: 1.00

電池 2:
  識別: C044817, 6754E4, 36.70Wh, 10.8Ah, 3.40V
  預期: C044817, 6754E4, 36.72Wh, 10.8Ah, 3.40V
  匹配度: 0.80
```

### 匹配度標準
- **1.00 (完美匹配)**: 所有欄位都完全正確
- **0.90+ (優秀匹配)**: 一個小的數值差異
- **0.70+ (良好匹配)**: 主要欄位正確，可接受的誤差
- **0.60+ (基本匹配)**: 識別出電池但有明顯誤差
- **< 0.60 (匹配失敗)**: 識別結果不正確

## 🔧 測試配置

### 環境要求
1. **必要圖片檔案**: 測試圖片必須存在於 `data/` 資料夾中
2. **Claude AI (可選)**: 設定 `ANTHROPIC_API_KEY` 以測試 Claude AI 識別
3. **傳統 OCR**: 確保 Tesseract 已正確安裝

### 預期結果更新
如果您需要更新測試的預期結果，請修改 `tests/test_real_image_recognition.py` 中的 `EXPECTED_RESULTS` 字典：

```python
EXPECTED_RESULTS = {
    'PXL_20250724_010217469.jpg': {
        'total_cells': 4,
        'cells': [
            {
                'serial_number': 'C048026',
                'model': '6754E4',
                'energy': 36.72,
                'capacity': 10.8,
                'voltage': 3.40
            },
            # 更多電池資料...
        ]
    }
}
```

## 📈 持續改善

### 如果測試失敗
1. **檢查圖片品質**: 確保測試圖片清晰可讀
2. **調整容差**: 修改數值比對的容差範圍
3. **更新預期結果**: 根據實際情況調整預期值
4. **改善識別算法**: 優化 OCR 預處理或 Claude AI 提示

### 新增測試案例
要新增更多測試圖片：
1. 將圖片放入 `data/` 資料夾
2. 手動確認圖片中的電池資訊
3. 更新 `EXPECTED_RESULTS` 字典
4. 新增對應的測試方法

## 🎯 測試目標

### 最低通過標準
- **電池數量**: 100% 正確識別總數
- **序號識別**: 70%+ 完全正確
- **型號識別**: 80%+ 正確
- **數值識別**: 70%+ 在合理容差範圍內

### 理想目標
- **Claude AI**: 90%+ 整體準確率
- **傳統 OCR**: 70%+ 整體準確率
- **系統穩定性**: 多次執行結果一致

## 🚨 故障排除

### 常見問題

#### 1. 圖片檔案找不到
```
Image file PXL_20250724_010217469.jpg not found in data folder
```
**解決方案**: 確認圖片檔案存在於 `data/` 資料夾中

#### 2. Claude AI 不可用
```
Claude AI service not available
```
**解決方案**: 檢查 `.env` 檔案中的 `ANTHROPIC_API_KEY` 設定

#### 3. OCR 識別失敗
```
Error processing image with OCR
```
**解決方案**: 
- 確認 Tesseract 已正確安裝
- 檢查 `TESSERACT_CMD` 環境變數
- 驗證圖片檔案未損壞

#### 4. 匹配度過低
```
只有 1/4 個電池達到良好匹配標準
```
**解決方案**:
- 檢查預期結果是否正確
- 調整匹配容差
- 改善圖片前處理

## 📝 測試報告

### 自動生成報告
執行 `python run_accuracy_tests.py` 會自動生成詳細的 JSON 報告：
- 測試通過率統計
- 每個測試的詳細結果
- 識別準確性分析
- 改善建議

### 手動檢查
使用 `-s` 參數執行 pytest 可以看到詳細的輸出：
```bash
pytest tests/test_real_image_recognition.py -v -s
```

這將顯示每個電池的詳細識別結果和比對過程。