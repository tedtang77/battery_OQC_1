'use client';

import { useState, useEffect } from 'react';
import { batteryApi } from '@/lib/api';
import { BatteryCell } from '@/types/battery';
import BatteryTable from '@/components/BatteryTable';
import toast from 'react-hot-toast';

export default function BatteriesPage() {
  const [batteries, setBatteries] = useState<BatteryCell[]>([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({
    skip: 0,
    limit: 50,
    total: 0
  });

  useEffect(() => {
    loadBatteries();
  }, [pagination.skip, pagination.limit]);

  const loadBatteries = async () => {
    setLoading(true);
    try {
      const result = await batteryApi.getBatteries(pagination.skip, pagination.limit);
      setBatteries(result);
    } catch (error) {
      console.error('Error loading batteries:', error);
      toast.error('載入電池資料失敗');
    } finally {
      setLoading(false);
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

  const handleRefresh = () => {
    loadBatteries();
    toast.success('資料已重新載入');
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
            <h2 className="text-2xl font-bold">電池資料庫</h2>
            <p className="text-gray-600 mt-1">
              總計 {batteries.length} 筆電池資料
            </p>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={handleRefresh}
              className="btn-secondary"
            >
              重新整理
            </button>
            <button
              onClick={exportCsv}
              className="btn-primary"
            >
              匯出 CSV
            </button>
          </div>
        </div>

        {batteries.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-400 mb-4">
              <svg className="mx-auto h-16 w-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">沒有電池資料</h3>
            <p className="text-gray-600 mb-4">
              請先在首頁處理電池圖片並儲存資料
            </p>
            <a href="/" className="btn-primary">
              前往處理圖片
            </a>
          </div>
        ) : (
          <>
            {/* Statistics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-blue-50 p-4 rounded-lg">
                <h3 className="text-sm font-medium text-blue-600">總電池數</h3>
                <p className="text-2xl font-bold text-blue-900">{batteries.length}</p>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <h3 className="text-sm font-medium text-green-600">平均能量</h3>
                <p className="text-2xl font-bold text-green-900">
                  {batteries.length > 0 ? 
                    (batteries.reduce((sum, b) => sum + b.energy, 0) / batteries.length).toFixed(1)
                    : '0'
                  } Wh
                </p>
              </div>
              <div className="bg-yellow-50 p-4 rounded-lg">
                <h3 className="text-sm font-medium text-yellow-600">平均容量</h3>
                <p className="text-2xl font-bold text-yellow-900">
                  {batteries.length > 0 ? 
                    (batteries.reduce((sum, b) => sum + b.capacity, 0) / batteries.length).toFixed(1)
                    : '0'
                  } Ah
                </p>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg">
                <h3 className="text-sm font-medium text-purple-600">平均電壓</h3>
                <p className="text-2xl font-bold text-purple-900">
                  {batteries.length > 0 ? 
                    (batteries.reduce((sum, b) => sum + b.voltage, 0) / batteries.length).toFixed(2)
                    : '0'
                  } V
                </p>
              </div>
            </div>

            {/* Battery Table */}
            <BatteryTable batteries={batteries} />
          </>
        )}
      </div>
    </div>
  );
}