import React, { Suspense, lazy } from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { ConfigProvider, Spin } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import AppLayout from '@/components/Layout'
import Dashboard from '@/pages/Dashboard'

const Schedule = lazy(() => import('@/pages/Schedule'))
const Logs = lazy(() => import('@/pages/Logs'))
const Data = lazy(() => import('@/pages/Data'))
const QuickCrawl = lazy(() => import('@/pages/QuickCrawl'))
const Cards = lazy(() => import('@/pages/Cards'))
const Wechat = lazy(() => import('@/pages/Wechat'))

const Loading: React.FC = () => (
  <div className="page-loading">
    <Spin size="large" />
  </div>
)

const App: React.FC = () => (
  <ConfigProvider
    locale={zhCN}
    theme={{
      token: {
        colorPrimary: '#1677ff',
        colorBgLayout: '#f5f7fb',
        colorBgContainer: '#ffffff',
        colorBorder: '#e5e7eb',
        colorText: '#1f2937',
        colorTextSecondary: '#6b7280',
        borderRadius: 8,
        fontFamily:
          '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
      },
      components: {
        Layout: {
          headerBg: '#ffffff',
          siderBg: '#ffffff',
          bodyBg: '#f5f7fb',
        },
        Menu: {
          itemSelectedBg: '#eaf3ff',
          itemSelectedColor: '#1677ff',
          itemHoverBg: '#f3f7ff',
        },
        Card: {
          borderRadiusLG: 10,
        },
        Table: {
          headerBg: '#f8fafc',
          headerColor: '#475569',
          rowHoverBg: '#f8fafc',
        },
      },
    }}
  >
    <BrowserRouter>
      <AppLayout>
        <Suspense fallback={<Loading />}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/quick-crawl" element={<QuickCrawl />} />
            <Route path="/schedule" element={<Schedule />} />
            <Route path="/logs" element={<Logs />} />
            <Route path="/data" element={<Data />} />
            <Route path="/cards" element={<Cards />} />
            <Route path="/wechat" element={<Wechat />} />
          </Routes>
        </Suspense>
      </AppLayout>
    </BrowserRouter>
  </ConfigProvider>
)

export default App
