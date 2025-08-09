'use client';

import { useState } from 'react';
import { batteryApi } from '@/lib/api';
import { BatteryCell, RecognitionStatus } from '@/types/battery';
import BatteryTable from '@/components/BatteryTable';
import ProcessingStatus from '@/components/ProcessingStatus';
import RecognitionStatusComponent from '@/components/RecognitionStatus';
import toast from 'react-hot-toast';

export default function Home() {
  const [batteries, setBatteries] = useState<BatteryCell[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [currentStep, setCurrentStep] = useState<string>('');
  const [recognitionStatus, setRecognitionStatus] = useState<RecognitionStatus | null>(null);

  const processImages = async () => {
    setIsProcessing(true);
    
    if (recognitionStatus?.claude_ai.available) {
      setCurrentStep('使用 Claude AI 分析圖片...');
    } else {
      setCurrentStep('使用傳統 OCR 處理圖片...');
    }
    
    try {
      const result = await batteryApi.processImages();
      setBatteries(result);
      
      // 統計識別方式
      const claudeCount = result.filter(b => b.recognition_method === 'Claude AI').length;
      const ocrCount = result.filter(b => b.recognition_method === 'Traditional OCR').length;
      
      let message = `成功處理 ${result.length} 個電池資料`;
      if (claudeCount > 0 && ocrCount > 0) {
        message += ` (Claude AI: ${claudeCount}, OCR: ${ocrCount})`;
      } else if (claudeCount > 0) {
        message += ` (使用 Claude AI)`;
      } else if (ocrCount > 0) {
        message += ` (使用傳統 OCR)`;
      }
      
      toast.success(message);
      setCurrentStep('處理完成');
    } catch (error) {
      console.error('Error processing images:', error);
      toast.error('圖片處理失敗');
      setCurrentStep('處理失敗');
    } finally {
      setIsProcessing(false);
    }
  };

  const saveBatteries = async () => {
    if (batteries.length === 0) {
      toast.error('沒有電池資料可以儲存');
      return;
    }

    setIsSaving(true);
    try {
      const result = await batteryApi.saveBatteries(batteries);
      toast.success(result.message);
      // Clear the processed batteries after saving
      setBatteries([]);
    } catch (error) {
      console.error('Error saving batteries:', error);
      toast.error('儲存電池資料失敗');
    } finally {
      setIsSaving(false);
    }
  };

  const exportCsv = async () => {
    try {
      const blob = await batteryApi.exportCsv();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `battery_data_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      toast.success('CSV 檔案已下載');
    } catch (error) {
      console.error('Error exporting CSV:', error);
      toast.error('匯出 CSV 失敗');
    }
  };

  return (
    <div className="container mx-auto p-6">
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-2xl font-bold mb-4">電池 OQC 處理系統</h2>
        <p className="text-gray-600 mb-6">
          自動處理 data 資料夾中的電池照片，提取電池資訊並儲存至資料庫
        </p>

        {/* Recognition Status */}
        <RecognitionStatusComponent onStatusLoaded={setRecognitionStatus} />

        {/* Control Panel */}
        <div className="flex flex-wrap gap-4 mb-6">
          <button
            onClick={processImages}
            disabled={isProcessing}
            className="btn-primary flex items-center"
          >
            {isProcessing ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                處理中...
              </>
            ) : (
              '處理圖片'
            )}
          </button>

          <button
            onClick={saveBatteries}
            disabled={isSaving || batteries.length === 0}
            className="btn-success flex items-center"
          >
            {isSaving ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                儲存中...
              </>
            ) : (
              `儲存到資料庫 (${batteries.length})`
            )}
          </button>

          <button
            onClick={exportCsv}
            className="btn-secondary"
          >
            匯出 CSV
          </button>
        </div>

        {/* Processing Status */}
        {isProcessing && (
          <ProcessingStatus 
            isProcessing={isProcessing}
            currentStep={currentStep}
          />
        )}

        {/* Results Table */}
        {batteries.length > 0 && (
          <div className="mt-6">
            <h3 className="text-lg font-semibold mb-4">處理結果 ({batteries.length} 個電池)</h3>
            <BatteryTable batteries={batteries} />
          </div>
        )}

        {/* Instructions */}
        {batteries.length === 0 && !isProcessing && (
          <div className="bg-blue-50 border border-blue-200 rounded-md p-4 mt-6">
            <h4 className="text-lg font-medium text-blue-900 mb-2">使用說明</h4>
            <ol className="list-decimal list-inside text-blue-800 space-y-1">
              <li>點擊「處理圖片」按鈕開始處理 data 資料夾中的電池照片</li>
              <li>系統將自動識別每顆電池的序號、型號、能量、容量和電壓</li>
              <li>檢視處理結果，確認資料正確性</li>
              <li>點擊「儲存到資料庫」將資料儲存</li>
              <li>可以匯出 CSV 檔案進行進一步分析</li>
            </ol>
          </div>
        )}
      </div>
    </div>
  );
}