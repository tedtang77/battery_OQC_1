'use client';

import { useState, useEffect } from 'react';
import { batteryApi } from '@/lib/api';
import { BatchProcess } from '@/types/battery';
import toast from 'react-hot-toast';

export default function BatchesPage() {
  const [batches, setBatches] = useState<BatchProcess[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadBatches();
  }, []);

  const loadBatches = async () => {
    setLoading(true);
    try {
      const result = await batteryApi.getBatches();
      setBatches(result);
    } catch (error) {
      console.error('Error loading batches:', error);
      toast.error('載入批次記錄失敗');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    loadBatches();
    toast.success('資料已重新載入');
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-TW', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-lg">載入中...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-2xl font-bold">批次處理記錄</h2>
            <p className="text-gray-600 mt-1">
              總計 {batches.length} 個處理批次
            </p>
          </div>
          <button
            onClick={handleRefresh}
            className="btn-secondary"
          >
            重新整理
          </button>
        </div>

        {batches.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-400 mb-4">
              <svg className="mx-auto h-16 w-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">沒有批次記錄</h3>
            <p className="text-gray-600 mb-4">
              當您處理並儲存電池資料時，系統會自動記錄批次資訊
            </p>
            <a href="/" className="btn-primary">
              開始處理圖片
            </a>
          </div>
        ) : (
          <>
            {/* Summary Statistics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="bg-indigo-50 p-4 rounded-lg">
                <h3 className="text-sm font-medium text-indigo-600">總處理批次</h3>
                <p className="text-2xl font-bold text-indigo-900">{batches.length}</p>
              </div>
              <div className="bg-teal-50 p-4 rounded-lg">
                <h3 className="text-sm font-medium text-teal-600">總處理電池數</h3>
                <p className="text-2xl font-bold text-teal-900">
                  {batches.reduce((sum, batch) => sum + batch.total_cells, 0)}
                </p>
              </div>
              <div className="bg-orange-50 p-4 rounded-lg">
                <h3 className="text-sm font-medium text-orange-600">平均每批數量</h3>
                <p className="text-2xl font-bold text-orange-900">
                  {batches.length > 0 ? 
                    Math.round(batches.reduce((sum, batch) => sum + batch.total_cells, 0) / batches.length)
                    : 0
                  }
                </p>
              </div>
            </div>

            {/* Batch Table */}
            <div className="overflow-x-auto">
              <table className="min-w-full bg-white border border-gray-200 rounded-lg">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      批次編號
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      批次名稱
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      處理電池數
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      處理時間
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      建立時間
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {batches.map((batch) => (
                    <tr key={batch.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        #{batch.id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {batch.batch_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          {batch.total_cells} 顆
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDateTime(batch.processed_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDateTime(batch.created_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  );
}