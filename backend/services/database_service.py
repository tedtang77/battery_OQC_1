from prisma import Prisma
from typing import List, Optional, Dict, Any
from datetime import datetime

from models.battery import BatteryCellResponse, BatchProcessResponse

class DatabaseService:
    def __init__(self):
        self.db = Prisma()
    
    async def connect(self):
        """連接資料庫"""
        await self.db.connect()
    
    async def disconnect(self):
        """斷開資料庫連接"""
        await self.db.disconnect()
    
    async def save_battery(self, battery_data: Dict[str, Any]) -> BatteryCellResponse:
        """儲存單個電池資料"""
        try:
            battery = await self.db.batterycell.create(
                data={
                    'serialNumber': battery_data['serial_number'],
                    'model': battery_data['model'],
                    'energy': battery_data['energy'],
                    'capacity': battery_data['capacity'],
                    'voltage': battery_data['voltage'],
                    'imageFile': battery_data.get('image_file', ''),
                }
            )
            
            return BatteryCellResponse(
                id=battery.id,
                serial_number=battery.serialNumber,
                model=battery.model,
                energy=battery.energy,
                capacity=battery.capacity,
                voltage=battery.voltage,
                image_file=battery.imageFile,
                processed_at=battery.processedAt,
                created_at=battery.createdAt,
                updated_at=battery.updatedAt
            )
        except Exception as e:
            print(f"Error saving battery: {str(e)}")
            raise
    
    async def save_batch_process(self, batch_name: str, total_cells: int) -> BatchProcessResponse:
        """儲存批次處理記錄"""
        try:
            batch = await self.db.batchprocess.create(
                data={
                    'batchName': batch_name,
                    'totalCells': total_cells,
                }
            )
            
            return BatchProcessResponse(
                id=batch.id,
                batch_name=batch.batchName,
                total_cells=batch.totalCells,
                processed_at=batch.processedAt,
                created_at=batch.createdAt
            )
        except Exception as e:
            print(f"Error saving batch process: {str(e)}")
            raise
    
    async def get_batteries(self, skip: int = 0, limit: int = 100) -> List[BatteryCellResponse]:
        """取得電池資料列表"""
        try:
            batteries = await self.db.batterycell.find_many(
                skip=skip,
                take=limit,
                order={'createdAt': 'desc'}
            )
            
            return [
                BatteryCellResponse(
                    id=battery.id,
                    serial_number=battery.serialNumber,
                    model=battery.model,
                    energy=battery.energy,
                    capacity=battery.capacity,
                    voltage=battery.voltage,
                    image_file=battery.imageFile,
                    processed_at=battery.processedAt,
                    created_at=battery.createdAt,
                    updated_at=battery.updatedAt
                )
                for battery in batteries
            ]
        except Exception as e:
            print(f"Error retrieving batteries: {str(e)}")
            raise
    
    async def get_battery_by_id(self, battery_id: int) -> Optional[BatteryCellResponse]:
        """根據ID取得電池資料"""
        try:
            battery = await self.db.batterycell.find_unique(
                where={'id': battery_id}
            )
            
            if not battery:
                return None
            
            return BatteryCellResponse(
                id=battery.id,
                serial_number=battery.serialNumber,
                model=battery.model,
                energy=battery.energy,
                capacity=battery.capacity,
                voltage=battery.voltage,
                image_file=battery.imageFile,
                processed_at=battery.processedAt,
                created_at=battery.createdAt,
                updated_at=battery.updatedAt
            )
        except Exception as e:
            print(f"Error retrieving battery by ID: {str(e)}")
            raise
    
    async def get_batch_processes(self) -> List[BatchProcessResponse]:
        """取得所有批次處理記錄"""
        try:
            batches = await self.db.batchprocess.find_many(
                order={'createdAt': 'desc'}
            )
            
            return [
                BatchProcessResponse(
                    id=batch.id,
                    batch_name=batch.batchName,
                    total_cells=batch.totalCells,
                    processed_at=batch.processedAt,
                    created_at=batch.createdAt
                )
                for batch in batches
            ]
        except Exception as e:
            print(f"Error retrieving batch processes: {str(e)}")
            raise
    
    async def delete_battery(self, battery_id: int) -> bool:
        """刪除電池資料"""
        try:
            await self.db.batterycell.delete(
                where={'id': battery_id}
            )
            return True
        except Exception as e:
            print(f"Error deleting battery: {str(e)}")
            return False
    
    async def update_battery(self, battery_id: int, battery_data: Dict[str, Any]) -> Optional[BatteryCellResponse]:
        """更新電池資料"""
        try:
            battery = await self.db.batterycell.update(
                where={'id': battery_id},
                data={
                    'serialNumber': battery_data.get('serial_number'),
                    'model': battery_data.get('model'),
                    'energy': battery_data.get('energy'),
                    'capacity': battery_data.get('capacity'),
                    'voltage': battery_data.get('voltage'),
                    'imageFile': battery_data.get('image_file'),
                }
            )
            
            return BatteryCellResponse(
                id=battery.id,
                serial_number=battery.serialNumber,
                model=battery.model,
                energy=battery.energy,
                capacity=battery.capacity,
                voltage=battery.voltage,
                image_file=battery.imageFile,
                processed_at=battery.processedAt,
                created_at=battery.createdAt,
                updated_at=battery.updatedAt
            )
        except Exception as e:
            print(f"Error updating battery: {str(e)}")
            raise