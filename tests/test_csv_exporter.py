import pytest
import pandas as pd
import tempfile
import os
from datetime import datetime
from unittest.mock import Mock, patch

import sys
sys.path.append('../backend')

from backend.utils.csv_exporter import CSVExporter
from backend.models.battery import BatteryCellResponse

class TestCSVExporter:
    
    @pytest.fixture
    def temp_output_dir(self):
        """建立臨時輸出目錄"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def csv_exporter(self, temp_output_dir):
        """測試用的 CSVExporter 實例"""
        return CSVExporter(output_dir=temp_output_dir)
    
    @pytest.fixture
    def sample_batteries(self):
        """測試用的電池資料列表"""
        return [
            BatteryCellResponse(
                id=1,
                serial_number='C044160',
                model='6754E4',
                energy=36.74,
                capacity=10.8,
                voltage=3.40,
                image_file='test1.jpg',
                processed_at=datetime(2024, 1, 1, 12, 0, 0),
                created_at=datetime(2024, 1, 1, 12, 0, 0),
                updated_at=datetime(2024, 1, 1, 12, 0, 0)
            ),
            BatteryCellResponse(
                id=2,
                serial_number='C044161',
                model='6754E5',
                energy=37.20,
                capacity=11.0,
                voltage=3.38,
                image_file='test2.jpg',
                processed_at=datetime(2024, 1, 1, 12, 30, 0),
                created_at=datetime(2024, 1, 1, 12, 30, 0),
                updated_at=datetime(2024, 1, 1, 12, 30, 0)
            ),
            BatteryCellResponse(
                id=3,
                serial_number='C044162',
                model='6754E4',
                energy=36.50,
                capacity=10.7,
                voltage=3.41,
                image_file='test3.jpg',
                processed_at=datetime(2024, 1, 1, 13, 0, 0),
                created_at=datetime(2024, 1, 1, 13, 0, 0),
                updated_at=datetime(2024, 1, 1, 13, 0, 0)
            )
        ]
    
    def test_csv_exporter_initialization(self, temp_output_dir):
        """測試 CSVExporter 初始化"""
        exporter = CSVExporter(output_dir=temp_output_dir)
        
        assert exporter.output_dir == temp_output_dir
        assert os.path.exists(temp_output_dir)
    
    def test_csv_exporter_default_dir(self):
        """測試 CSVExporter 預設目錄"""
        exporter = CSVExporter()
        
        assert exporter.output_dir == "exports"
        assert os.path.exists("exports")
        
        # Clean up
        if os.path.exists("exports") and os.path.isdir("exports"):
            os.rmdir("exports")
    
    def test_export_batteries_success(self, csv_exporter, sample_batteries, temp_output_dir):
        """測試成功匯出電池資料"""
        filepath = csv_exporter.export_batteries(sample_batteries)
        
        # Check that file was created
        assert os.path.exists(filepath)
        assert filepath.startswith(temp_output_dir)
        assert filepath.endswith('.csv')
        
        # Read the CSV and verify content
        df = pd.read_csv(filepath)
        
        assert len(df) == 3
        assert list(df.columns) == [
            'ID', 'Serial Number', 'Model', 'Energy (Wh)', 
            'Capacity (Ah)', 'Voltage (V)', 'Image File', 
            'Processed At', 'Created At', 'Updated At'
        ]
        
        # Check first row data
        assert df.iloc[0]['ID'] == 1
        assert df.iloc[0]['Serial Number'] == 'C044160'
        assert df.iloc[0]['Model'] == '6754E4'
        assert df.iloc[0]['Energy (Wh)'] == 36.74
        assert df.iloc[0]['Capacity (Ah)'] == 10.8
        assert df.iloc[0]['Voltage (V)'] == 3.40
        assert df.iloc[0]['Image File'] == 'test1.jpg'
    
    def test_export_batteries_empty_list(self, csv_exporter, temp_output_dir):
        """測試匯出空電池列表"""
        filepath = csv_exporter.export_batteries([])
        
        # Check that file was created
        assert os.path.exists(filepath)
        
        # Read the CSV and verify content
        df = pd.read_csv(filepath)
        
        assert len(df) == 0
        assert list(df.columns) == [
            'ID', 'Serial Number', 'Model', 'Energy (Wh)', 
            'Capacity (Ah)', 'Voltage (V)', 'Image File', 
            'Processed At', 'Created At', 'Updated At'
        ]
    
    def test_export_batteries_with_none_dates(self, csv_exporter, temp_output_dir):
        """測試匯出包含空日期的電池資料"""
        battery_with_none_dates = BatteryCellResponse(
            id=1,
            serial_number='C044160',
            model='6754E4',
            energy=36.74,
            capacity=10.8,
            voltage=3.40,
            image_file='test1.jpg',
            processed_at=None,
            created_at=None,
            updated_at=None
        )
        
        filepath = csv_exporter.export_batteries([battery_with_none_dates])
        
        # Check that file was created
        assert os.path.exists(filepath)
        
        # Read the CSV and verify content
        df = pd.read_csv(filepath)
        
        assert len(df) == 1
        assert df.iloc[0]['Processed At'] == ''
        assert df.iloc[0]['Created At'] == ''
        assert df.iloc[0]['Updated At'] == ''
    
    def test_export_summary_report_success(self, csv_exporter, sample_batteries, temp_output_dir):
        """測試成功匯出摘要報告"""
        filepath = csv_exporter.export_summary_report(sample_batteries)
        
        # Check that file was created
        assert os.path.exists(filepath)
        assert filepath.startswith(temp_output_dir)
        assert 'summary' in filepath
        assert filepath.endswith('.csv')
        
        # Read the file content
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        
        # Check that summary sections are present
        assert '電池資料摘要報告' in content
        assert '摘要統計' in content
        assert '型號分布' in content
        assert '詳細資料' in content
        
        # Check some specific statistics
        assert 'Total Batteries,3' in content
        assert 'Unique Models,2' in content  # 6754E4 and 6754E5
    
    def test_export_summary_report_calculations(self, csv_exporter, sample_batteries, temp_output_dir):
        """測試摘要報告計算正確性"""
        filepath = csv_exporter.export_summary_report(sample_batteries)
        
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        
        # Calculate expected values
        total_batteries = len(sample_batteries)
        avg_energy = sum(b.energy for b in sample_batteries) / total_batteries
        avg_capacity = sum(b.capacity for b in sample_batteries) / total_batteries
        avg_voltage = sum(b.voltage for b in sample_batteries) / total_batteries
        
        min_energy = min(b.energy for b in sample_batteries)
        max_energy = max(b.energy for b in sample_batteries)
        
        assert f'Total Batteries,{total_batteries}' in content
        assert f'{avg_energy:.2f}' in content
        assert f'{min_energy:.2f} - {max_energy:.2f} Wh' in content
    
    def test_export_batteries_filename_format(self, csv_exporter, sample_batteries):
        """測試匯出檔案名稱格式"""
        with patch('backend.utils.csv_exporter.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 15, 14, 30, 45)
            mock_datetime.strftime = datetime.strftime
            
            filepath = csv_exporter.export_batteries(sample_batteries)
            
            expected_filename = 'battery_data_20240115_143045.csv'
            assert expected_filename in filepath
    
    def test_export_summary_report_filename_format(self, csv_exporter, sample_batteries):
        """測試摘要報告檔案名稱格式"""
        with patch('backend.utils.csv_exporter.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 15, 14, 30, 45)
            mock_datetime.strftime = datetime.strftime
            
            filepath = csv_exporter.export_summary_report(sample_batteries)
            
            expected_filename = 'battery_summary_20240115_143045.csv'
            assert expected_filename in filepath
    
    def test_export_batteries_error_handling(self, csv_exporter):
        """測試匯出時的錯誤處理"""
        # Create invalid battery data that might cause errors
        invalid_battery = Mock()
        invalid_battery.id = None
        invalid_battery.serial_number = None
        
        with pytest.raises(Exception):
            csv_exporter.export_batteries([invalid_battery])
    
    @patch('pandas.DataFrame.to_csv')
    def test_export_batteries_pandas_error(self, mock_to_csv, csv_exporter, sample_batteries):
        """測試 pandas 匯出錯誤"""
        mock_to_csv.side_effect = Exception("Pandas error")
        
        with pytest.raises(Exception):
            csv_exporter.export_batteries(sample_batteries)
    
    def test_export_model_distribution(self, csv_exporter, sample_batteries, temp_output_dir):
        """測試型號分布統計"""
        filepath = csv_exporter.export_summary_report(sample_batteries)
        
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        
        # Check model distribution
        # We have 2 batteries with 6754E4 and 1 with 6754E5
        assert '6754E4,2' in content
        assert '6754E5,1' in content