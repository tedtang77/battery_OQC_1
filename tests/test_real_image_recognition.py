import pytest
import asyncio
import os
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

import sys
sys.path.append('../backend')

from backend.services.image_processor import ImageProcessor
from backend.services.claude_vision_service import ClaudeVisionService
from backend.models.battery import BatteryCellResponse

class TestRealImageRecognition:
    """
    真實照片識別測試
    確保系統能正確識別特定照片中的電池資訊
    """
    
    # 預期的測試結果
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
                {
                    'serial_number': 'C044817',
                    'model': '6754E4',
                    'energy': 36.72,
                    'capacity': 10.8,
                    'voltage': 3.40
                },
                {
                    'serial_number': 'C046758',
                    'model': '6754E4',
                    'energy': 36.72,
                    'capacity': 10.8,
                    'voltage': 3.40
                },
                {
                    'serial_number': 'C048463',
                    'model': '6754E4',
                    'energy': 36.72,
                    'capacity': 10.8,
                    'voltage': 3.40
                }
            ]
        },
        'PXL_20250724_010602031.jpg': {
            'total_cells': 8,
            'cells': [
                {
                    'serial_number': 'C042316',
                    'model': '6754E4',
                    'energy': 36.72,
                    'capacity': 10.8,
                    'voltage': 3.40
                },
                {
                    'serial_number': 'C049332',
                    'model': '6754E4',
                    'energy': 36.72,
                    'capacity': 10.8,
                    'voltage': 3.40
                },
                {
                    'serial_number': 'C0494219',  # Note: This appears to have 7 digits, might be C049421
                    'model': '6754E4',
                    'energy': 36.72,
                    'capacity': 10.8,
                    'voltage': 3.40
                },
                {
                    'serial_number': 'C048397',
                    'model': '6754E4',
                    'energy': 36.72,
                    'capacity': 10.8,
                    'voltage': 3.40
                }
                # Note: Only 4 cells specified in test case, but total_cells is 8
                # The remaining 4 cells' data would need to be provided for complete testing
            ]
        }
    }
    
    @pytest.fixture
    def image_processor(self):
        """測試用的 ImageProcessor 實例"""
        return ImageProcessor()
    
    @pytest.fixture
    def data_path(self):
        """Data 資料夾路徑"""
        return Path(__file__).parent.parent / "data"
    
    def get_image_path(self, data_path: Path, filename: str) -> str:
        """取得圖片完整路徑"""
        image_path = data_path / filename
        if not image_path.exists():
            pytest.skip(f"Image file {filename} not found in data folder")
        return str(image_path)
    
    def compare_battery_data(self, actual: BatteryCellResponse, expected: dict, tolerance: float = 0.01) -> dict:
        """
        比較電池資料，返回比對結果
        
        Args:
            actual: 實際識別結果
            expected: 預期結果
            tolerance: 數值容差
            
        Returns:
            比對結果字典，包含各欄位是否匹配
        """
        result = {
            'serial_number': actual.serial_number == expected['serial_number'],
            'model': actual.model == expected['model'],
            'energy': abs(actual.energy - expected['energy']) <= tolerance,
            'capacity': abs(actual.capacity - expected['capacity']) <= tolerance,
            'voltage': abs(actual.voltage - expected['voltage']) <= tolerance,
        }
        
        # 計算總分
        result['total_score'] = sum(result.values()) / len(result)
        
        return result
    
    def find_best_match(self, actual_batteries: list, expected_batteries: list) -> list:
        """
        找到實際結果和預期結果的最佳匹配
        
        Returns:
            匹配結果列表，每個元素包含 (actual_battery, expected_battery, match_score)
        """
        matches = []
        used_expected = set()
        
        for actual in actual_batteries:
            best_match = None
            best_score = 0
            best_expected_idx = -1
            
            for i, expected in enumerate(expected_batteries):
                if i in used_expected:
                    continue
                
                comparison = self.compare_battery_data(actual, expected)
                if comparison['total_score'] > best_score:
                    best_score = comparison['total_score']
                    best_match = expected
                    best_expected_idx = i
            
            if best_match and best_score > 0.6:  # 至少60%匹配度
                matches.append((actual, best_match, best_score))
                used_expected.add(best_expected_idx)
            else:
                matches.append((actual, None, 0))
        
        return matches
    
    @pytest.mark.asyncio
    async def test_image_recognition_pxl_010217469(self, image_processor, data_path):
        """測試圖片 PXL_20250724_010217469.jpg (4 cells)"""
        filename = 'PXL_20250724_010217469.jpg'
        image_path = self.get_image_path(data_path, filename)
        expected = self.EXPECTED_RESULTS[filename]
        
        # 執行識別
        results = await image_processor.process_image(image_path)
        
        # 驗證總數
        assert len(results) == expected['total_cells'], \
            f"Expected {expected['total_cells']} cells, got {len(results)}"
        
        # 詳細比對每個電池
        matches = self.find_best_match(results, expected['cells'])
        
        # 驗證匹配結果
        perfect_matches = sum(1 for _, _, score in matches if score >= 0.9)
        good_matches = sum(1 for _, _, score in matches if score >= 0.7)
        
        print(f"\n=== {filename} 識別結果 ===")
        print(f"預期電池數: {expected['total_cells']}, 實際識別: {len(results)}")
        print(f"完美匹配: {perfect_matches}/{len(matches)}")
        print(f"良好匹配: {good_matches}/{len(matches)}")
        
        for i, (actual, expected_match, score) in enumerate(matches):
            print(f"\n電池 {i+1}:")
            print(f"  識別: {actual.serial_number}, {actual.model}, {actual.energy}Wh, {actual.capacity}Ah, {actual.voltage}V")
            if expected_match:
                print(f"  預期: {expected_match['serial_number']}, {expected_match['model']}, {expected_match['energy']}Wh, {expected_match['capacity']}Ah, {expected_match['voltage']}V")
                print(f"  匹配度: {score:.2f}")
            else:
                print(f"  未找到匹配的預期結果")
        
        # 至少要有70%的電池獲得良好匹配
        assert good_matches >= expected['total_cells'] * 0.7, \
            f"只有 {good_matches}/{expected['total_cells']} 個電池達到良好匹配標準"
    
    @pytest.mark.asyncio
    async def test_image_recognition_pxl_010602031(self, image_processor, data_path):
        """測試圖片 PXL_20250724_010602031.jpg (8 cells)"""
        filename = 'PXL_20250724_010602031.jpg'
        image_path = self.get_image_path(data_path, filename)
        expected = self.EXPECTED_RESULTS[filename]
        
        # 執行識別
        results = await image_processor.process_image(image_path)
        
        # 驗證總數
        assert len(results) == expected['total_cells'], \
            f"Expected {expected['total_cells']} cells, got {len(results)}"
        
        # 詳細比對已知的4個電池資料
        known_cells = expected['cells']  # 只有4個已知電池資料
        matches = self.find_best_match(results[:len(known_cells)], known_cells)
        
        good_matches = sum(1 for _, _, score in matches if score >= 0.7)
        
        print(f"\n=== {filename} 識別結果 ===")
        print(f"預期電池數: {expected['total_cells']}, 實際識別: {len(results)}")
        print(f"已知電池資料: {len(known_cells)}")
        print(f"良好匹配: {good_matches}/{len(known_cells)}")
        
        for i, (actual, expected_match, score) in enumerate(matches):
            print(f"\n電池 {i+1}:")
            print(f"  識別: {actual.serial_number}, {actual.model}, {actual.energy}Wh, {actual.capacity}Ah, {actual.voltage}V")
            if expected_match:
                print(f"  預期: {expected_match['serial_number']}, {expected_match['model']}, {expected_match['energy']}Wh, {expected_match['capacity']}Ah, {expected_match['voltage']}V")
                print(f"  匹配度: {score:.2f}")
        
        # 顯示其他識別到的電池
        if len(results) > len(known_cells):
            print(f"\n其他識別到的電池:")
            for i, battery in enumerate(results[len(known_cells):], len(known_cells) + 1):
                print(f"  電池 {i}: {battery.serial_number}, {battery.model}, {battery.energy}Wh, {battery.capacity}Ah, {battery.voltage}V")
        
        # 至少要有70%的已知電池獲得良好匹配
        assert good_matches >= len(known_cells) * 0.7, \
            f"只有 {good_matches}/{len(known_cells)} 個已知電池達到良好匹配標準"
    
    @pytest.mark.asyncio
    async def test_recognition_methods_comparison(self, data_path):
        """比較 Claude AI 和傳統 OCR 的識別效果"""
        filename = 'PXL_20250724_010217469.jpg'
        image_path = self.get_image_path(data_path, filename)
        expected = self.EXPECTED_RESULTS[filename]
        
        # 測試 Claude AI (如果可用)
        claude_service = ClaudeVisionService()
        claude_results = []
        if claude_service.is_available():
            claude_results = await claude_service.analyze_battery_image(image_path, filename)
        
        # 測試傳統 OCR
        image_processor = ImageProcessor()
        ocr_results = await image_processor.process_image_with_ocr(image_path)
        
        print(f"\n=== 識別方法比較: {filename} ===")
        
        # Claude AI 結果
        if claude_results:
            claude_matches = self.find_best_match(claude_results, expected['cells'])
            claude_good_matches = sum(1 for _, _, score in claude_matches if score >= 0.7)
            print(f"\nClaude AI:")
            print(f"  識別數量: {len(claude_results)}")
            print(f"  良好匹配: {claude_good_matches}/{len(expected['cells'])}")
            print(f"  準確率: {claude_good_matches / len(expected['cells']) * 100:.1f}%")
        else:
            print(f"\nClaude AI: 不可用 (未設定 API Key)")
        
        # 傳統 OCR 結果
        ocr_matches = self.find_best_match(ocr_results, expected['cells'])
        ocr_good_matches = sum(1 for _, _, score in ocr_matches if score >= 0.7)
        print(f"\n傳統 OCR:")
        print(f"  識別數量: {len(ocr_results)}")
        print(f"  良好匹配: {ocr_good_matches}/{len(expected['cells'])}")
        print(f"  準確率: {ocr_good_matches / len(expected['cells']) * 100:.1f}%")
        
        # 至少有一種方法要能達到基本要求
        has_working_method = (
            (claude_results and claude_good_matches >= len(expected['cells']) * 0.5) or
            (ocr_good_matches >= len(expected['cells']) * 0.5)
        )
        
        assert has_working_method, "沒有任何識別方法能達到50%的基本准確率要求"
    
    @pytest.mark.asyncio
    async def test_all_data_images_basic_recognition(self, image_processor, data_path):
        """對所有 data 資料夾中的圖片進行基本識別測試"""
        image_files = list(data_path.glob("*.jpg")) + list(data_path.glob("*.jpeg")) + list(data_path.glob("*.png"))
        
        if not image_files:
            pytest.skip("No image files found in data folder")
        
        print(f"\n=== 批次識別測試 ===")
        print(f"找到 {len(image_files)} 個圖片檔案")
        
        total_batteries = 0
        successful_files = 0
        
        for image_file in image_files:
            try:
                results = await image_processor.process_image(str(image_file))
                battery_count = len(results)
                total_batteries += battery_count
                
                if battery_count > 0:
                    successful_files += 1
                
                print(f"  {image_file.name}: {battery_count} 個電池")
                
                # 顯示識別到的電池概要
                for i, battery in enumerate(results[:3]):  # 只顯示前3個
                    print(f"    {i+1}. {battery.serial_number} ({battery.model})")
                if len(results) > 3:
                    print(f"    ... 還有 {len(results) - 3} 個電池")
                    
            except Exception as e:
                print(f"  {image_file.name}: 處理失敗 - {str(e)}")
        
        print(f"\n總結:")
        print(f"  成功處理: {successful_files}/{len(image_files)} 個檔案")
        print(f"  識別電池總數: {total_batteries} 個")
        print(f"  平均每張圖片: {total_batteries / len(image_files):.1f} 個電池")
        
        # 基本要求：至少要有一半的圖片能成功識別出電池
        assert successful_files >= len(image_files) * 0.5, \
            f"只有 {successful_files}/{len(image_files)} 個圖片成功識別出電池"
    
    def test_expected_data_integrity(self):
        """驗證預期結果數據的完整性"""
        for filename, data in self.EXPECTED_RESULTS.items():
            # 檢查必要欄位
            assert 'total_cells' in data, f"{filename}: 缺少 total_cells 欄位"
            assert 'cells' in data, f"{filename}: 缺少 cells 欄位"
            assert isinstance(data['total_cells'], int), f"{filename}: total_cells 必須是整數"
            assert isinstance(data['cells'], list), f"{filename}: cells 必須是列表"
            
            # 檢查每個電池資料
            for i, cell in enumerate(data['cells']):
                required_fields = ['serial_number', 'model', 'energy', 'capacity', 'voltage']
                for field in required_fields:
                    assert field in cell, f"{filename} 電池 {i+1}: 缺少 {field} 欄位"
                
                # 檢查資料類型和合理性
                assert isinstance(cell['serial_number'], str), f"{filename} 電池 {i+1}: serial_number 必須是字串"
                assert isinstance(cell['model'], str), f"{filename} 電池 {i+1}: model 必須是字串"
                assert isinstance(cell['energy'], (int, float)), f"{filename} 電池 {i+1}: energy 必須是數字"
                assert isinstance(cell['capacity'], (int, float)), f"{filename} 電池 {i+1}: capacity 必須是數字"
                assert isinstance(cell['voltage'], (int, float)), f"{filename} 電池 {i+1}: voltage 必須是數字"
                
                # 檢查數值合理性
                assert 0 < cell['energy'] < 100, f"{filename} 電池 {i+1}: energy 值不合理"
                assert 0 < cell['capacity'] < 50, f"{filename} 電池 {i+1}: capacity 值不合理"
                assert 0 < cell['voltage'] < 10, f"{filename} 電池 {i+1}: voltage 值不合理"
        
        print("✅ 預期結果數據驗證通過")

class TestImageRecognitionAccuracy:
    """圖片識別準確性測試"""
    
    @pytest.mark.asyncio
    async def test_recognition_consistency(self):
        """測試識別結果的一致性（多次識別同一張圖片）"""
        data_path = Path(__file__).parent.parent / "data"
        filename = 'PXL_20250724_010217469.jpg'
        image_path = data_path / filename
        
        if not image_path.exists():
            pytest.skip(f"Image file {filename} not found")
        
        image_processor = ImageProcessor()
        
        # 執行5次識別
        results_list = []
        for i in range(5):
            results = await image_processor.process_image(str(image_path))
            results_list.append(results)
        
        # 檢查結果數量一致性
        counts = [len(results) for results in results_list]
        assert min(counts) == max(counts), f"識別結果數量不一致: {counts}"
        
        print(f"\n=== 識別一致性測試 ===")
        print(f"5次識別結果數量: {counts}")
        print("✅ 識別數量保持一致")
    
    @pytest.mark.asyncio
    async def test_edge_cases(self):
        """測試邊緣情況"""
        image_processor = ImageProcessor()
        
        # 測試不存在的圖片
        results = await image_processor.process_image("nonexistent.jpg")
        assert results == [], "不存在圖片應返回空列表"
        
        # 測試空路徑
        results = await image_processor.process_image("")
        assert results == [], "空路徑應返回空列表"
        
        print("✅ 邊緣情況測試通過")