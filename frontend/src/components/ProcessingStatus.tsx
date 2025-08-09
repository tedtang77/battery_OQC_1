'use client';

import { ProcessingStatus as ProcessingStatusType } from '@/types/battery';

interface ProcessingStatusProps {
  isProcessing: boolean;
  currentStep?: string;
  progress?: number;
}

export default function ProcessingStatus({
  isProcessing,
  currentStep,
  progress
}: ProcessingStatusProps) {
  if (!isProcessing) return null;

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
      <div className="flex items-center">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mr-3"></div>
        <div className="flex-1">
          <h4 className="text-sm font-medium text-blue-900">
            {currentStep || '處理中...'}
          </h4>
          {progress !== undefined && (
            <div className="mt-2">
              <div className="bg-blue-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="text-xs text-blue-600 mt-1">{progress}% 完成</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}