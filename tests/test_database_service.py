import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock

import sys
sys.path.append('../backend')

from backend.services.database_service import DatabaseService
from backend.models.battery import BatteryCellResponse, BatchProcessResponse

class TestDatabaseService:
    
    @pytest.fixture
    def database_service(self):
        """測試用的 DatabaseService 實例"""
        service = DatabaseService()
        # Mock the Prisma client
        service.db = Mock()
        return service
    
    @pytest.fixture
    def sample_battery_data(self):
        """測試用的電池資料"""
        return {
            'serial_number': 'C044160',
            'model': '6754E4',
            'energy': 36.74,
            'capacity': 10.8,
            'voltage': 3.40,
            'image_file': 'test.jpg'
        }
    
    @pytest.fixture
    def sample_battery_db_record(self):
        """模擬從資料庫回傳的電池記錄"""
        mock_record = Mock()
        mock_record.id = 1
        mock_record.serialNumber = 'C044160'
        mock_record.model = '6754E4'
        mock_record.energy = 36.74
        mock_record.capacity = 10.8
        mock_record.voltage = 3.40
        mock_record.imageFile = 'test.jpg'
        mock_record.processedAt = datetime(2024, 1, 1, 12, 0, 0)
        mock_record.createdAt = datetime(2024, 1, 1, 12, 0, 0)
        mock_record.updatedAt = datetime(2024, 1, 1, 12, 0, 0)
        return mock_record
    
    async def test_connect(self, database_service):
        """測試資料庫連接"""
        database_service.db.connect = AsyncMock()
        
        await database_service.connect()
        
        database_service.db.connect.assert_called_once()
    
    async def test_disconnect(self, database_service):
        """測試資料庫斷線"""
        database_service.db.disconnect = AsyncMock()
        
        await database_service.disconnect()
        
        database_service.db.disconnect.assert_called_once()
    
    async def test_save_battery_success(self, database_service, sample_battery_data, sample_battery_db_record):
        """測試成功儲存電池資料"""
        database_service.db.batterycell.create = AsyncMock(return_value=sample_battery_db_record)
        
        result = await database_service.save_battery(sample_battery_data)
        
        # Verify the create call
        database_service.db.batterycell.create.assert_called_once_with(
            data={
                'serialNumber': 'C044160',
                'model': '6754E4',
                'energy': 36.74,
                'capacity': 10.8,
                'voltage': 3.40,
                'imageFile': 'test.jpg',
            }
        )
        
        # Verify the returned result
        assert isinstance(result, BatteryCellResponse)
        assert result.id == 1
        assert result.serial_number == 'C044160'
        assert result.model == '6754E4'
        assert result.energy == 36.74
    
    async def test_save_battery_error(self, database_service, sample_battery_data):
        """測試儲存電池資料時發生錯誤"""
        database_service.db.batterycell.create = AsyncMock(side_effect=Exception("Database error"))
        
        with pytest.raises(Exception):
            await database_service.save_battery(sample_battery_data)
    
    async def test_save_batch_process_success(self, database_service):
        """測試成功儲存批次處理記錄"""
        mock_batch_record = Mock()
        mock_batch_record.id = 1
        mock_batch_record.batchName = "Test_Batch"
        mock_batch_record.totalCells = 5
        mock_batch_record.processedAt = datetime(2024, 1, 1, 12, 0, 0)
        mock_batch_record.createdAt = datetime(2024, 1, 1, 12, 0, 0)
        
        database_service.db.batchprocess.create = AsyncMock(return_value=mock_batch_record)
        
        result = await database_service.save_batch_process("Test_Batch", 5)
        
        # Verify the create call
        database_service.db.batchprocess.create.assert_called_once_with(
            data={
                'batchName': "Test_Batch",
                'totalCells': 5,
            }
        )
        
        # Verify the returned result
        assert isinstance(result, BatchProcessResponse)
        assert result.id == 1
        assert result.batch_name == "Test_Batch"
        assert result.total_cells == 5
    
    async def test_get_batteries_success(self, database_service, sample_battery_db_record):
        """測試成功取得電池列表"""
        mock_batteries = [sample_battery_db_record]
        database_service.db.batterycell.find_many = AsyncMock(return_value=mock_batteries)
        
        result = await database_service.get_batteries(skip=0, limit=10)
        
        # Verify the find_many call
        database_service.db.batterycell.find_many.assert_called_once_with(
            skip=0,
            take=10,
            order={'createdAt': 'desc'}
        )
        
        # Verify the returned result
        assert len(result) == 1
        assert isinstance(result[0], BatteryCellResponse)
        assert result[0].serial_number == 'C044160'
    
    async def test_get_batteries_empty(self, database_service):
        """測試取得空的電池列表"""
        database_service.db.batterycell.find_many = AsyncMock(return_value=[])
        
        result = await database_service.get_batteries()
        
        assert result == []
    
    async def test_get_battery_by_id_found(self, database_service, sample_battery_db_record):
        """測試根據ID找到電池"""
        database_service.db.batterycell.find_unique = AsyncMock(return_value=sample_battery_db_record)
        
        result = await database_service.get_battery_by_id(1)
        
        # Verify the find_unique call
        database_service.db.batterycell.find_unique.assert_called_once_with(
            where={'id': 1}
        )
        
        # Verify the returned result
        assert isinstance(result, BatteryCellResponse)
        assert result.id == 1
        assert result.serial_number == 'C044160'
    
    async def test_get_battery_by_id_not_found(self, database_service):
        """測試根據ID找不到電池"""
        database_service.db.batterycell.find_unique = AsyncMock(return_value=None)
        
        result = await database_service.get_battery_by_id(999)
        
        assert result is None
    
    async def test_get_batch_processes_success(self, database_service):
        """測試成功取得批次處理列表"""
        mock_batch = Mock()
        mock_batch.id = 1
        mock_batch.batchName = "Test_Batch"
        mock_batch.totalCells = 5
        mock_batch.processedAt = datetime(2024, 1, 1, 12, 0, 0)
        mock_batch.createdAt = datetime(2024, 1, 1, 12, 0, 0)
        
        database_service.db.batchprocess.find_many = AsyncMock(return_value=[mock_batch])
        
        result = await database_service.get_batch_processes()
        
        # Verify the find_many call
        database_service.db.batchprocess.find_many.assert_called_once_with(
            order={'createdAt': 'desc'}
        )
        
        # Verify the returned result
        assert len(result) == 1
        assert isinstance(result[0], BatchProcessResponse)
        assert result[0].batch_name == "Test_Batch"
    
    async def test_delete_battery_success(self, database_service):
        """測試成功刪除電池"""
        database_service.db.batterycell.delete = AsyncMock()
        
        result = await database_service.delete_battery(1)
        
        # Verify the delete call
        database_service.db.batterycell.delete.assert_called_once_with(
            where={'id': 1}
        )
        
        assert result is True
    
    async def test_delete_battery_error(self, database_service):
        """測試刪除電池時發生錯誤"""
        database_service.db.batterycell.delete = AsyncMock(side_effect=Exception("Delete error"))
        
        result = await database_service.delete_battery(1)
        
        assert result is False
    
    async def test_update_battery_success(self, database_service, sample_battery_data, sample_battery_db_record):
        """測試成功更新電池資料"""
        database_service.db.batterycell.update = AsyncMock(return_value=sample_battery_db_record)
        
        result = await database_service.update_battery(1, sample_battery_data)
        
        # Verify the update call
        database_service.db.batterycell.update.assert_called_once_with(
            where={'id': 1},
            data={
                'serialNumber': 'C044160',
                'model': '6754E4',
                'energy': 36.74,
                'capacity': 10.8,
                'voltage': 3.40,
                'imageFile': 'test.jpg',
            }
        )
        
        # Verify the returned result
        assert isinstance(result, BatteryCellResponse)
        assert result.id == 1
        assert result.serial_number == 'C044160'
    
    async def test_update_battery_error(self, database_service, sample_battery_data):
        """測試更新電池資料時發生錯誤"""
        database_service.db.batterycell.update = AsyncMock(side_effect=Exception("Update error"))
        
        with pytest.raises(Exception):
            await database_service.update_battery(1, sample_battery_data)
    
    @pytest.mark.asyncio
    async def test_database_service_full_workflow(self, database_service, sample_battery_data):
        """測試完整的資料庫操作流程"""
        # Mock all the database operations
        mock_battery = Mock()
        mock_battery.id = 1
        mock_battery.serialNumber = sample_battery_data['serial_number']
        mock_battery.model = sample_battery_data['model']
        mock_battery.energy = sample_battery_data['energy']
        mock_battery.capacity = sample_battery_data['capacity']
        mock_battery.voltage = sample_battery_data['voltage']
        mock_battery.imageFile = sample_battery_data['image_file']
        mock_battery.processedAt = datetime.now()
        mock_battery.createdAt = datetime.now()
        mock_battery.updatedAt = datetime.now()
        
        database_service.db.batterycell.create = AsyncMock(return_value=mock_battery)
        database_service.db.batterycell.find_many = AsyncMock(return_value=[mock_battery])
        database_service.db.batterycell.find_unique = AsyncMock(return_value=mock_battery)
        database_service.db.batterycell.delete = AsyncMock()
        
        # Test save battery
        saved_battery = await database_service.save_battery(sample_battery_data)
        assert isinstance(saved_battery, BatteryCellResponse)
        
        # Test get batteries
        batteries = await database_service.get_batteries()
        assert len(batteries) == 1
        
        # Test get battery by id
        battery = await database_service.get_battery_by_id(1)
        assert battery is not None
        
        # Test delete battery
        result = await database_service.delete_battery(1)
        assert result is True