from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from typing import List, Optional
import uvicorn
import os
from datetime import datetime

from services.image_processor import ImageProcessor
from services.database_service import DatabaseService
from models.battery import BatteryCellResponse, BatchProcessResponse
from utils.csv_exporter import CSVExporter

app = FastAPI(title="電池 OQC 系統", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
image_processor = ImageProcessor()
db_service = DatabaseService()
csv_exporter = CSVExporter()

@app.on_event("startup")
async def startup_event():
    await db_service.connect()

@app.on_event("shutdown")
async def shutdown_event():
    await db_service.disconnect()

@app.get("/")
async def root():
    return {"message": "電池 OQC 系統 API"}

@app.get("/recognition-status")
async def get_recognition_status():
    """取得圖片識別服務狀態"""
    try:
        status = image_processor.get_recognition_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recognition status: {str(e)}")

@app.post("/process-images", response_model=List[BatteryCellResponse])
async def process_images():
    """處理 data 資料夾中的所有圖片"""
    try:
        data_path = "../data"
        if not os.path.exists(data_path):
            raise HTTPException(status_code=404, detail="Data folder not found")
        
        results = []
        image_files = [f for f in os.listdir(data_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        for image_file in image_files:
            image_path = os.path.join(data_path, image_file)
            battery_data = await image_processor.process_image(image_path)
            
            if battery_data:
                for battery in battery_data:
                    battery.image_file = image_file
                    results.append(battery)
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing images: {str(e)}")

@app.post("/save-batteries")
async def save_batteries(batteries: List[BatteryCellResponse]):
    """儲存電池資料到資料庫"""
    try:
        saved_batteries = []
        for battery in batteries:
            saved_battery = await db_service.save_battery(battery.dict())
            saved_batteries.append(saved_battery)
        
        # 記錄批次處理
        batch_name = f"Batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        await db_service.save_batch_process(batch_name, len(saved_batteries))
        
        return {"message": f"Successfully saved {len(saved_batteries)} batteries", "count": len(saved_batteries)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving batteries: {str(e)}")

@app.get("/batteries", response_model=List[BatteryCellResponse])
async def get_batteries(skip: int = 0, limit: int = 100):
    """取得所有電池資料"""
    try:
        batteries = await db_service.get_batteries(skip=skip, limit=limit)
        return batteries
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving batteries: {str(e)}")

@app.get("/export-csv")
async def export_csv():
    """匯出電池資料為 CSV"""
    try:
        batteries = await db_service.get_batteries()
        csv_file = csv_exporter.export_batteries(batteries)
        
        return FileResponse(
            path=csv_file,
            filename=f"battery_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            media_type='application/octet-stream'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting CSV: {str(e)}")

@app.get("/batches", response_model=List[BatchProcessResponse])
async def get_batches():
    """取得所有批次處理記錄"""
    try:
        batches = await db_service.get_batch_processes()
        return batches
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving batches: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)