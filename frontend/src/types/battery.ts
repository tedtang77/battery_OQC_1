export interface BatteryCell {
  id?: number;
  serial_number: string;
  model: string;
  energy: number;
  capacity: number;
  voltage: number;
  image_file?: string;
  recognition_method?: string;
  processed_at?: string;
  created_at?: string;
  updated_at?: string;
}

export interface BatchProcess {
  id: number;
  batch_name: string;
  total_cells: number;
  processed_at: string;
  created_at: string;
}

export interface ApiResponse<T> {
  data?: T;
  message?: string;
  error?: string;
}

export interface ProcessingStatus {
  isProcessing: boolean;
  currentStep?: string;
  progress?: number;
}

export interface TableColumn {
  key: keyof BatteryCell;
  label: string;
  sortable?: boolean;
}

export interface SortConfig {
  key: keyof BatteryCell;
  direction: 'asc' | 'desc';
}

export interface RecognitionStatus {
  claude_ai: {
    service_name: string;
    available: boolean;
    model?: string;
    api_key_configured: boolean;
    description: string;
  };
  traditional_ocr: {
    service_name: string;
    available: boolean;
    description: string;
    tesseract_cmd: string;
  };
  preferred_method: string;
}