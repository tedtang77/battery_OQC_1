import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Toaster } from 'react-hot-toast'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: '電池 OQC 系統',
  description: '電池品質檢查系統 - 自動識別電池芯資訊並匯入資料庫',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-TW">
      <body className={inter.className}>
        <nav className="bg-gray-800 text-white p-4">
          <div className="container mx-auto flex justify-between items-center">
            <h1 className="text-xl font-bold">電池 OQC 系統</h1>
            <div className="flex space-x-4">
              <a href="/" className="hover:text-gray-300">首頁</a>
              <a href="/batteries" className="hover:text-gray-300">電池資料</a>
              <a href="/batches" className="hover:text-gray-300">批次記錄</a>
            </div>
          </div>
        </nav>
        <main className="min-h-screen bg-gray-100">
          {children}
        </main>
        <Toaster position="top-right" />
      </body>
    </html>
  )
}