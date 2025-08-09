import pytest
import asyncio
import os
import sys
from unittest.mock import Mock, AsyncMock

# Add backend directory to Python path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../backend'))

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_prisma_client():
    """Mock Prisma database client for testing"""
    mock_client = Mock()
    
    # Mock batterycell operations
    mock_client.batterycell = Mock()
    mock_client.batterycell.create = AsyncMock()
    mock_client.batterycell.find_many = AsyncMock(return_value=[])
    mock_client.batterycell.find_unique = AsyncMock(return_value=None)
    mock_client.batterycell.update = AsyncMock()
    mock_client.batterycell.delete = AsyncMock()
    
    # Mock batchprocess operations
    mock_client.batchprocess = Mock()
    mock_client.batchprocess.create = AsyncMock()
    mock_client.batchprocess.find_many = AsyncMock(return_value=[])
    
    # Mock connection methods
    mock_client.connect = AsyncMock()
    mock_client.disconnect = AsyncMock()
    
    return mock_client

@pytest.fixture
def mock_tesseract():
    """Mock Tesseract OCR for testing"""
    with pytest.MonkeyPatch.context() as m:
        mock_ocr = Mock()
        mock_ocr.return_value = "Test OCR output"
        m.setattr("pytesseract.image_to_string", mock_ocr)
        yield mock_ocr

@pytest.fixture
def sample_ocr_text():
    """Sample OCR text containing battery information"""
    return """
    Battery Cell Information:
    Serial Number: C044160
    Model: 6754E4
    Energy: 36.74Wh
    Capacity: 10.8Ah
    Voltage: 3.40V
    
    Additional Battery:
    Serial: C044161
    Model: 6754E5
    Energy: 37.20Wh
    Capacity: 11.0Ah
    Voltage: 3.38V
    """

@pytest.fixture
def mock_cv2():
    """Mock OpenCV functions for testing"""
    import numpy as np
    
    with pytest.MonkeyPatch.context() as m:
        # Mock imread
        mock_imread = Mock()
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_imread.return_value = test_image
        m.setattr("cv2.imread", mock_imread)
        
        # Mock other CV2 functions
        m.setattr("cv2.cvtColor", Mock(return_value=np.zeros((480, 640), dtype=np.uint8)))
        m.setattr("cv2.createCLAHE", Mock(return_value=Mock(apply=Mock(return_value=np.zeros((480, 640), dtype=np.uint8)))))
        m.setattr("cv2.GaussianBlur", Mock(return_value=np.zeros((480, 640), dtype=np.uint8)))
        m.setattr("cv2.threshold", Mock(return_value=(0, np.zeros((480, 640), dtype=np.uint8))))
        
        yield mock_imread

# Test data fixtures
@pytest.fixture
def battery_test_data():
    """Standard battery test data"""
    return {
        'serial_number': 'C044160',
        'model': '6754E4',
        'energy': 36.74,
        'capacity': 10.8,
        'voltage': 3.40,
        'image_file': 'test.jpg'
    }

@pytest.fixture
def multiple_battery_test_data():
    """Multiple battery test data"""
    return [
        {
            'serial_number': 'C044160',
            'model': '6754E4',
            'energy': 36.74,
            'capacity': 10.8,
            'voltage': 3.40,
            'image_file': 'test1.jpg'
        },
        {
            'serial_number': 'C044161',
            'model': '6754E5',
            'energy': 37.20,
            'capacity': 11.0,
            'voltage': 3.38,
            'image_file': 'test2.jpg'
        }
    ]