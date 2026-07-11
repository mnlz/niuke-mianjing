import React, { useMemo, useState } from 'react'
import { Badge, Button, Layout, Menu, Typography } from 'antd'
import {
  BarChartOutlined,
  ClockCircleOutlined,
  DatabaseOutlined,
  FileMarkdownOutlined,
  FileSearchOutlined,
  HomeOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  SendOutlined,
  SolutionOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import { useLocation, useNavigate } from 'react-router-dom'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useCrawlStore } from '@/store/crawlStore'
import { clearAdminToken } from '@/utils/auth'

const { Sider, Header, Content } = Layout
const { Text } = Typography

const menuItems = [
  { key: '/admin', icon: <BarChartOutlined />, label: '后台首页' },
  { key: '/quick-crawl', icon: <ThunderboltOutlined />, label: '快速爬取' },
  { key: '/schedule', icon: <ClockCircleOutlined />, label: '定时任务' },
  { key: '/logs', icon: <FileSearchOutlined />, label: '爬取日志' },
  { key: '/data', icon: <DatabaseOutlined />, label: '面经数据' },
  { key: '/recruitment-jobs', icon: <SolutionOutlined />, label: '岗位管理' },
  { key: '/cards', icon: <FileMarkdownOutlined />, label: '卡片工坊' },
  { key: '/wechat', icon: <SendOutlined />, label: '公众号工坊' },
]

const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const connected = useCrawlStore((s) => s.connected)
  const progresses = useCrawlStore((s) => s.progresses)
  useWebSocket()

  const runningCount = useMemo(
    () => Object.values(progresses).filter((p) => p.status === 'running').length,
    [progresses],
  )

  return (
    <Layout className="app-shell">
      <Sider trigger={null} collapsible collapsed={collapsed} width={232} className="app-sider">
        <div className="brand">
          <img className="brand-logo-img" src="/offerlens.svg" alt="OfferLens" />
          {!collapsed && (
            <div>
              <Text className="brand-title">OfferLens</Text>
              <Text className="brand-subtitle">内容采集与发布后台</Text>
            </div>
          )}
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          className="side-menu"
        />
      </Sider>
      <Layout>
        <Header className="app-header">
          <div className="header-left">
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
            />
            <Text className="header-version">niuke-mianjing v2.0</Text>
          </div>
          <div className="header-right">
            <Button type="text" icon={<HomeOutlined />} onClick={() => navigate('/')}>
              查看前台
            </Button>
            <Button
              type="text"
              icon={<LogoutOutlined />}
              onClick={() => {
                clearAdminToken()
                navigate('/admin-login', { replace: true })
              }}
            >
              退出
            </Button>
            {runningCount > 0 && (
              <Badge status="processing" text={<Text className="running-text">爬取中（{runningCount}）</Text>} />
            )}
            <Badge status={connected ? 'success' : 'error'} text={connected ? '实时已连接' : '实时未连接'} />
          </div>
        </Header>
        <Content className="app-content">{children}</Content>
      </Layout>
    </Layout>
  )
}

export default AppLayout
