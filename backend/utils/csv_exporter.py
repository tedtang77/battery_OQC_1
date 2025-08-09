import pandas as pd
import os
from typing import List
from datetime import datetime

from models.battery import BatteryCellResponse

class CSVExporter:
    def __init__(self, output_dir: str = "exports"):
        self.output_dir = output_dir
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def export_batteries(self, batteries: List[BatteryCellResponse]) -> str:
        """將電池資料匯出為 CSV 檔案"""
        try:
            # Convert battery data to DataFrame
            data = []
            for battery in batteries:
                data.append({
                    'ID': battery.id,
                    'Serial Number': battery.serial_number,
                    'Model': battery.model,
                    'Energy (Wh)': battery.energy,
                    'Capacity (Ah)': battery.capacity,
                    'Voltage (V)': battery.voltage,
                    'Image File': battery.image_file,
                    'Processed At': battery.processed_at.strftime('%Y-%m-%d %H:%M:%S') if battery.processed_at else '',
                    'Created At': battery.created_at.strftime('%Y-%m-%d %H:%M:%S') if battery.created_at else '',
                    'Updated At': battery.updated_at.strftime('%Y-%m-%d %H:%M:%S') if battery.updated_at else ''
                })
            
            df = pd.DataFrame(data)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"battery_data_{timestamp}.csv"
            filepath = os.path.join(self.output_dir, filename)
            
            # Export to CSV
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            
            return filepath
        except Exception as e:
            print(f"Error exporting batteries to CSV: {str(e)}")
            raise
    
    def export_summary_report(self, batteries: List[BatteryCellResponse]) -> str:
        """匯出電池資料摘要報告"""
        try:
            # Convert to DataFrame for analysis
            data = []
            for battery in batteries:
                data.append({
                    'Serial Number': battery.serial_number,
                    'Model': battery.model,
                    'Energy': battery.energy,
                    'Capacity': battery.capacity,
                    'Voltage': battery.voltage,
                    'Image File': battery.image_file
                })
            
            df = pd.DataFrame(data)
            
            # Create summary statistics
            summary_data = {
                'Total Batteries': len(batteries),
                'Unique Models': df['Model'].nunique(),
                'Average Energy (Wh)': df['Energy'].mean(),
                'Average Capacity (Ah)': df['Capacity'].mean(),
                'Average Voltage (V)': df['Voltage'].mean(),
                'Energy Range': f"{df['Energy'].min():.2f} - {df['Energy'].max():.2f} Wh",
                'Capacity Range': f"{df['Capacity'].min():.2f} - {df['Capacity'].max():.2f} Ah",
                'Voltage Range': f"{df['Voltage'].min():.2f} - {df['Voltage'].max():.2f} V"
            }
            
            # Create summary DataFrame
            summary_df = pd.DataFrame(list(summary_data.items()), columns=['Metric', 'Value'])
            
            # Model distribution
            model_dist = df['Model'].value_counts().reset_index()
            model_dist.columns = ['Model', 'Count']
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"battery_summary_{timestamp}.csv"
            filepath = os.path.join(self.output_dir, filename)
            
            # Write to CSV with multiple sheets simulation
            with open(filepath, 'w', encoding='utf-8-sig') as f:
                f.write("電池資料摘要報告\n")
                f.write("=" * 50 + "\n\n")
                
                # Write summary statistics
                f.write("摘要統計\n")
                summary_df.to_csv(f, index=False)
                f.write("\n\n")
                
                # Write model distribution
                f.write("型號分布\n")
                model_dist.to_csv(f, index=False)
                f.write("\n\n")
                
                # Write detailed data
                f.write("詳細資料\n")
                df.to_csv(f, index=False)
            
            return filepath
        except Exception as e:
            print(f"Error exporting summary report: {str(e)}")
            raise