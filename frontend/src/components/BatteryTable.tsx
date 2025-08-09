'use client';

import { useState } from 'react';
import { BatteryCell, SortConfig, TableColumn } from '@/types/battery';
import { ChevronUpIcon, ChevronDownIcon } from '@heroicons/react/24/outline';

interface BatteryTableProps {
  batteries: BatteryCell[];
  showActions?: boolean;
  onEdit?: (battery: BatteryCell) => void;
  onDelete?: (batteryId: number) => void;
}

const columns: TableColumn[] = [
  { key: 'serial_number', label: '序號', sortable: true },
  { key: 'model', label: '型號', sortable: true },
  { key: 'energy', label: '能量 (Wh)', sortable: true },
  { key: 'capacity', label: '容量 (Ah)', sortable: true },
  { key: 'voltage', label: '電壓 (V)', sortable: true },
  { key: 'recognition_method', label: '識別方式', sortable: true },
  { key: 'image_file', label: '圖片檔案', sortable: true },
];

export default function BatteryTable({ 
  batteries, 
  showActions = false, 
  onEdit, 
  onDelete 
}: BatteryTableProps) {
  const [sortConfig, setSortConfig] = useState<SortConfig | null>(null);

  const sortedBatteries = [...batteries].sort((a, b) => {
    if (!sortConfig) return 0;

    const aValue = a[sortConfig.key];
    const bValue = b[sortConfig.key];

    if (aValue === undefined || bValue === undefined) return 0;

    if (typeof aValue === 'string' && typeof bValue === 'string') {
      return sortConfig.direction === 'asc' 
        ? aValue.localeCompare(bValue)
        : bValue.localeCompare(aValue);
    }

    if (typeof aValue === 'number' && typeof bValue === 'number') {
      return sortConfig.direction === 'asc' 
        ? aValue - bValue
        : bValue - aValue;
    }

    return 0;
  });

  const handleSort = (key: keyof BatteryCell) => {
    let direction: 'asc' | 'desc' = 'asc';
    
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }

    setSortConfig({ key, direction });
  };

  const getSortIcon = (columnKey: keyof BatteryCell) => {
    if (!sortConfig || sortConfig.key !== columnKey) {
      return <ChevronUpIcon className="h-4 w-4 text-gray-400" />;
    }

    return sortConfig.direction === 'asc' 
      ? <ChevronUpIcon className="h-4 w-4 text-blue-600" />
      : <ChevronDownIcon className="h-4 w-4 text-blue-600" />;
  };

  if (batteries.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        沒有電池資料
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full bg-white border border-gray-200 rounded-lg">
        <thead className="bg-gray-50">
          <tr>
            {columns.map((column) => (
              <th 
                key={column.key} 
                className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${
                  column.sortable ? 'cursor-pointer hover:bg-gray-100' : ''
                }`}
                onClick={() => column.sortable && handleSort(column.key)}
              >
                <div className="flex items-center">
                  {column.label}
                  {column.sortable && (
                    <span className="ml-2">
                      {getSortIcon(column.key)}
                    </span>
                  )}
                </div>
              </th>
            ))}
            {showActions && (
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                操作
              </th>
            )}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {sortedBatteries.map((battery, index) => (
            <tr key={battery.id || index} className="hover:bg-gray-50">
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                {battery.serial_number}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {battery.model}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {battery.energy.toFixed(2)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {battery.capacity.toFixed(2)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {battery.voltage.toFixed(2)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {battery.recognition_method ? (
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    battery.recognition_method === 'Claude AI' 
                      ? 'bg-blue-100 text-blue-800' 
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {battery.recognition_method === 'Claude AI' ? '🤖 Claude AI' : '🔍 OCR'}
                  </span>
                ) : (
                  <span className="text-gray-400">-</span>
                )}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {battery.image_file}
              </td>
              {showActions && (
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <div className="flex space-x-2">
                    {onEdit && (
                      <button
                        onClick={() => onEdit(battery)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        編輯
                      </button>
                    )}
                    {onDelete && battery.id && (
                      <button
                        onClick={() => onDelete(battery.id!)}
                        className="text-red-600 hover:text-red-900"
                      >
                        刪除
                      </button>
                    )}
                  </div>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}