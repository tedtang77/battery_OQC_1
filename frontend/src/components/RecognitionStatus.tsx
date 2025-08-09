'use client';

import { useState, useEffect } from 'react';
import { batteryApi } from '@/lib/api';
import { RecognitionStatus as RecognitionStatusType } from '@/types/battery';
import { CheckCircleIcon, XCircleIcon, InformationCircleIcon } from '@heroicons/react/24/outline';

interface RecognitionStatusProps {
  onStatusLoaded?: (status: RecognitionStatusType) => void;
}

export default function RecognitionStatus({ onStatusLoaded }: RecognitionStatusProps) {
  const [status, setStatus] = useState<RecognitionStatusType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    try {
      setLoading(true);
      const statusData = await batteryApi.getRecognitionStatus();
      setStatus(statusData);
      if (onStatusLoaded) {
        onStatusLoaded(statusData);
      }
      setError(null);
    } catch (err) {
      console.error('Error loading recognition status:', err);
      setError('無法載入識別服務狀態');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-gray-50 rounded-lg p-4">
        <div className="flex items-center">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600 mr-2"></div>
          <span className="text-sm text-gray-600">載入識別服務狀態...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <XCircleIcon className="h-5 w-5 text-red-600 mr-2" />
          <span className="text-sm text-red-600">{error}</span>
          <button
            onClick={loadStatus}
            className="ml-auto text-sm text-red-600 hover:text-red-800 underline"
          >
            重試
          </button>
        </div>
      </div>
    );
  }

  if (!status) return null;

  const getStatusIcon = (available: boolean) => {
    return available ? (
      <CheckCircleIcon className="h-5 w-5 text-green-600" />
    ) : (
      <XCircleIcon className="h-5 w-5 text-red-600" />
    );
  };

  const getStatusColor = (available: boolean) => {
    return available ? 'text-green-600' : 'text-red-600';
  };

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
      <div className="flex items-center mb-3">
        <InformationCircleIcon className="h-5 w-5 text-blue-600 mr-2" />
        <h3 className="text-sm font-medium text-blue-900">圖片識別服務狀態</h3>
        <button
          onClick={loadStatus}
          className="ml-auto text-xs text-blue-600 hover:text-blue-800 underline"
        >
          重新整理
        </button>
      </div>

      <div className="space-y-3">
        {/* Claude AI Status */}
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            {getStatusIcon(status.claude_ai.available)}
            <div className="ml-2">
              <span className="text-sm font-medium text-gray-900">
                {status.claude_ai.service_name}
              </span>
              {status.claude_ai.model && (
                <span className="ml-2 text-xs text-gray-500">({status.claude_ai.model})</span>
              )}
            </div>
          </div>
          <div className="text-right">
            <span className={`text-sm font-medium ${getStatusColor(status.claude_ai.available)}`}>
              {status.claude_ai.available ? '可用' : '不可用'}
            </span>
            {!status.claude_ai.api_key_configured && (
              <div className="text-xs text-gray-500">未設定 API Key</div>
            )}
          </div>
        </div>

        {/* Traditional OCR Status */}
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            {getStatusIcon(status.traditional_ocr.available)}
            <div className="ml-2">
              <span className="text-sm font-medium text-gray-900">
                {status.traditional_ocr.service_name}
              </span>
              <span className="ml-2 text-xs text-gray-500">
                ({status.traditional_ocr.tesseract_cmd})
              </span>
            </div>
          </div>
          <div className="text-right">
            <span className={`text-sm font-medium ${getStatusColor(status.traditional_ocr.available)}`}>
              {status.traditional_ocr.available ? '可用' : '不可用'}
            </span>
          </div>
        </div>

        {/* Preferred Method */}
        <div className="pt-2 border-t border-blue-200">
          <div className="flex items-center justify-between">
            <span className="text-sm text-blue-700">優先使用方法:</span>
            <span className="text-sm font-medium text-blue-900">
              {status.preferred_method}
            </span>
          </div>
        </div>

        {/* Setup Instructions */}
        {!status.claude_ai.available && (
          <div className="pt-2 border-t border-blue-200">
            <div className="text-xs text-blue-700">
              💡 <strong>提示:</strong> 若要啟用 Claude AI 識別，請在 backend/.env 檔案中設定 ANTHROPIC_API_KEY
            </div>
          </div>
        )}
      </div>
    </div>
  );
}