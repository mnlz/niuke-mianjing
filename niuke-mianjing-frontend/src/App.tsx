import React, { Suspense, lazy, useEffect, useState } from 'react'
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { ConfigProvider, Spin } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import AppLayout from '@/components/Layout'
import Dashboard from '@/pages/Dashboard'
import { authApi } from '@/api'
import { ADMIN_TOKEN_CHANGED_EVENT, clearAdminToken, getAdminToken } from '@/utils/auth'

const PublicHome = lazy(() => import('@/pages/PublicHome'))
const PublicInterviews = lazy(() => import('@/pages/PublicInterviews'))
const PublicJobs = lazy(() => import('@/pages/PublicJobs'))
const Schedule = lazy(() => import('@/pages/Schedule'))
const Logs = lazy(() => import('@/pages/Logs'))
const Data = lazy(() => import('@/pages/Data'))
const QuickCrawl = lazy(() => import('@/pages/QuickCrawl'))
const Cards = lazy(() => import('@/pages/Cards'))
const Wechat = lazy(() => import('@/pages/Wechat'))
const AdminLogin = lazy(() => import('@/pages/AdminLogin'))

const Loading: React.FC = () => (
  <div className="page-loading">
    <Spin size="large" />
  </div>
)

const AdminRoutes: React.FC = () => {
  const location = useLocation()
  const [status, setStatus] = useState<'checking' | 'allowed' | 'denied'>('checking')

  useEffect(() => {
    let active = true

    const verifySession = async () => {
      if (!getAdminToken()) {
        if (active) setStatus('denied')
        return
      }

      if (active) setStatus('checking')
      try {
        await authApi.me()
        if (active) setStatus('allowed')
      } catch {
        clearAdminToken()
        if (active) setStatus('denied')
      }
    }

    void verifySession()
    window.addEventListener(ADMIN_TOKEN_CHANGED_EVENT, verifySession)
    return () => {
      active = false
      window.removeEventListener(ADMIN_TOKEN_CHANGED_EVENT, verifySession)
    }
  }, [])

  if (status === 'checking') return <Loading />
  if (status === 'denied') return <Navigate to="/admin-login" replace state={{ from: location.pathname }} />

  return (
    <AppLayout>
      <Suspense fallback={<Loading />}>
        <Routes>
          <Route path="/admin" element={<Dashboard />} />
          <Route path="/quick-crawl" element={<QuickCrawl />} />
          <Route path="/schedule" element={<Schedule />} />
          <Route path="/logs" element={<Logs />} />
          <Route path="/data" element={<Data />} />
          <Route path="/cards" element={<Cards />} />
          <Route path="/wechat" element={<Wechat />} />
          <Route path="*" element={<Navigate to="/admin" replace />} />
        </Routes>
      </Suspense>
    </AppLayout>
  )
}

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
      <Routes>
        <Route
          path="/"
          element={
            <Suspense fallback={<Loading />}>
              <PublicHome />
            </Suspense>
          }
        />
        <Route
          path="/interviews"
          element={
            <Suspense fallback={<Loading />}>
              <PublicInterviews />
            </Suspense>
          }
        />
        <Route
          path="/jobs"
          element={
            <Suspense fallback={<Loading />}>
              <PublicJobs />
            </Suspense>
          }
        />
        <Route
          path="/admin-login"
          element={
            <Suspense fallback={<Loading />}>
              <AdminLogin />
            </Suspense>
          }
        />
        <Route path="/*" element={<AdminRoutes />} />
      </Routes>
    </BrowserRouter>
  </ConfigProvider>
)

export default App
