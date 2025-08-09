from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class BatteryCellBase(BaseModel):
    serial_number: str
    model: str
    energy: float
    capacity: float
    voltage: float
    image_file: Optional[str] = None
    recognition_method: Optional[str] = None

class BatteryCellCreate(BatteryCellBase):
    pass

class BatteryCellResponse(BatteryCellBase):
    id: Optional[int] = None
    processed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class BatchProcessBase(BaseModel):
    batch_name: str
    total_cells: int

class BatchProcessCreate(BatchProcessBase):
    pass

class BatchProcessResponse(BatchProcessBase):
    id: int
    processed_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True