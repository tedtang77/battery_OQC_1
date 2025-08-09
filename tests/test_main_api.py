import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient

import sys
sys.path.append('../backend')

from backend.main import app
from backend.models.battery import BatteryCellResponse, BatchProcessResponse

class TestMainAPI:
    
    @pytest.fixture
    def client(self):
        """測試用的 FastAPI 客戶端"""
        return TestClient(app)
    
    @pytest.fixture
    def sample_battery_response(self):
        """測試用的電池回應資料"""
        return BatteryCellResponse(
            id=1,
            serial_number='C044160',
            model='6754E4',
            energy=36.74,
            capacity=10.8,
            voltage=3.40,
            image_file='test.jpg',
            processed_at=datetime(2024, 1, 1, 12, 0, 0),
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0)
        )
    
    def test_root_endpoint(self, client):
        """測試根路徑端點"""
        response = client.get("/")
        
        assert response.status_code == 200
        assert response.json() == {"message": "電池 OQC 系統 API"}
    
    @patch('backend.main.image_processor.process_image')
    @patch('os.path.exists')
    @patch('os.listdir')
    def test_process_images_success(self, mock_listdir, mock_exists, mock_process_image, client, sample_battery_response):
        """測試成功處理圖片"""
        # Setup mocks
        mock_exists.return_value = True
        mock_listdir.return_value = ['test1.jpg', 'test2.jpg', 'other.txt']
        mock_process_image.return_value = [sample_battery_response]
        
        response = client.post("/process-images")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 2  # Only .jpg files should be processed
        assert data[0]['serial_number'] == 'C044160'
        assert data[0]['model'] == '6754E4'
    
    @patch('os.path.exists')
    def test_process_images_data_folder_not_found(self, mock_exists, client):
        """測試資料夾不存在時的錯誤"""
        mock_exists.return_value = False
        
        response = client.post("/process-images")
        
        assert response.status_code == 404
        assert "Data folder not found" in response.json()['detail']
    
    @patch('backend.main.image_processor.process_image')
    @patch('os.path.exists')
    @patch('os.listdir')
    def test_process_images_processing_error(self, mock_listdir, mock_exists, mock_process_image, client):
        """測試圖片處理錯誤"""
        mock_exists.return_value = True
        mock_listdir.return_value = ['test.jpg']
        mock_process_image.side_effect = Exception("Processing error")
        
        response = client.post("/process-images")
        
        assert response.status_code == 500
        assert "Error processing images" in response.json()['detail']
    
    @patch('backend.main.db_service.save_battery')
    @patch('backend.main.db_service.save_batch_process')
    def test_save_batteries_success(self, mock_save_batch, mock_save_battery, client, sample_battery_response):
        """測試成功儲存電池資料"""
        # Setup mocks
        mock_save_battery.return_value = sample_battery_response
        mock_save_batch.return_value = Mock()
        
        battery_data = [{
            "serial_number": "C044160",
            "model": "6754E4",
            "energy": 36.74,
            "capacity": 10.8,
            "voltage": 3.40,
            "image_file": "test.jpg"
        }]
        
        response = client.post("/save-batteries", json=battery_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "Successfully saved 1 batteries" in data['message']
        assert data['count'] == 1
    
    @patch('backend.main.db_service.save_battery')
    def test_save_batteries_error(self, mock_save_battery, client):
        """測試儲存電池資料錯誤"""
        mock_save_battery.side_effect = Exception("Database error")
        
        battery_data = [{
            "serial_number": "C044160",
            "model": "6754E4",
            "energy": 36.74,
            "capacity": 10.8,
            "voltage": 3.40,
            "image_file": "test.jpg"
        }]
        
        response = client.post("/save-batteries", json=battery_data)
        
        assert response.status_code == 500
        assert "Error saving batteries" in response.json()['detail']
    
    @patch('backend.main.db_service.get_batteries')
    def test_get_batteries_success(self, mock_get_batteries, client, sample_battery_response):
        """測試成功取得電池列表"""
        mock_get_batteries.return_value = [sample_battery_response]
        
        response = client.get("/batteries?skip=0&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        assert data[0]['serial_number'] == 'C044160'
    
    @patch('backend.main.db_service.get_batteries')
    def test_get_batteries_default_params(self, mock_get_batteries, client):
        """測試使用預設參數取得電池列表"""
        mock_get_batteries.return_value = []
        
        response = client.get("/batteries")
        
        mock_get_batteries.assert_called_once_with(skip=0, limit=100)
        assert response.status_code == 200
    
    @patch('backend.main.db_service.get_batteries')
    def test_get_batteries_error(self, mock_get_batteries, client):
        """測試取得電池列表錯誤"""
        mock_get_batteries.side_effect = Exception("Database error")
        
        response = client.get("/batteries")
        
        assert response.status_code == 500
        assert "Error retrieving batteries" in response.json()['detail']
    
    @patch('backend.main.csv_exporter.export_batteries')
    @patch('backend.main.db_service.get_batteries')
    def test_export_csv_success(self, mock_get_batteries, mock_export_csv, client, sample_battery_response, tmp_path):
        """測試成功匯出 CSV"""
        # Create a temporary CSV file
        csv_file = tmp_path / "test_export.csv"
        csv_file.write_text("test,data\n1,2")
        
        mock_get_batteries.return_value = [sample_battery_response]
        mock_export_csv.return_value = str(csv_file)
        
        response = client.get("/export-csv")
        
        assert response.status_code == 200
        assert response.headers['content-type'] == 'application/octet-stream'
    
    @patch('backend.main.db_service.get_batteries')
    def test_export_csv_error(self, mock_get_batteries, client):
        """測試匯出 CSV 錯誤"""
        mock_get_batteries.side_effect = Exception("Database error")
        
        response = client.get("/export-csv")
        
        assert response.status_code == 500
        assert "Error exporting CSV" in response.json()['detail']
    
    @patch('backend.main.db_service.get_batch_processes')
    def test_get_batches_success(self, mock_get_batches, client):
        """測試成功取得批次列表"""
        mock_batch = BatchProcessResponse(
            id=1,
            batch_name="Test_Batch",
            total_cells=5,
            processed_at=datetime(2024, 1, 1, 12, 0, 0),
            created_at=datetime(2024, 1, 1, 12, 0, 0)
        )
        mock_get_batches.return_value = [mock_batch]
        
        response = client.get("/batches")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        assert data[0]['batch_name'] == "Test_Batch"
        assert data[0]['total_cells'] == 5
    
    @patch('backend.main.db_service.get_batch_processes')
    def test_get_batches_error(self, mock_get_batches, client):
        """測試取得批次列表錯誤"""
        mock_get_batches.side_effect = Exception("Database error")
        
        response = client.get("/batches")
        
        assert response.status_code == 500
        assert "Error retrieving batches" in response.json()['detail']
    
    def test_cors_headers(self, client):
        """測試 CORS 標頭"""
        response = client.options("/", headers={"Origin": "http://localhost:3000"})
        
        # FastAPI automatically handles OPTIONS requests for CORS
        assert response.status_code in [200, 405]  # 405 if OPTIONS not explicitly defined
    
    @patch('os.path.exists')
    @patch('os.listdir')
    def test_process_images_no_image_files(self, mock_listdir, mock_exists, client):
        """測試資料夾中沒有圖片檔案"""
        mock_exists.return_value = True
        mock_listdir.return_value = ['text.txt', 'doc.pdf']  # No image files
        
        response = client.post("/process-images")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data == []  # Should return empty list
    
    @patch('backend.main.image_processor.process_image')
    @patch('os.path.exists')
    @patch('os.listdir')
    def test_process_images_mixed_file_types(self, mock_listdir, mock_exists, mock_process_image, client, sample_battery_response):
        """測試處理混合檔案類型"""
        mock_exists.return_value = True
        mock_listdir.return_value = ['image1.jpg', 'image2.JPG', 'image3.png', 'image4.PNG', 'text.txt', 'doc.pdf']
        mock_process_image.return_value = [sample_battery_response]
        
        response = client.post("/process-images")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should process 4 image files (jpg, JPG, png, PNG)
        assert len(data) == 4
        
        # Verify process_image was called for each image file
        assert mock_process_image.call_count == 4
    
    def test_api_response_format(self, client):
        """測試 API 回應格式"""
        response = client.get("/")
        
        assert response.status_code == 200
        assert response.headers['content-type'] == 'application/json'
        
        data = response.json()
        assert isinstance(data, dict)
        assert 'message' in data