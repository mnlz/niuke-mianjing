import React, { useMemo, useState } from 'react'
import { Badge, Button, Layout, Menu, Typography } from 'antd'
import {
  BarChartOutlined,
  ClockCircleOutlined,
  DatabaseOutlined,
  FileMarkdownOutlined,
  FileSearchOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  SendOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import { useLocation, useNavigate } from 'react-router-dom'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useCrawlStore } from '@/store/crawlStore'

const { Sider, Header, Content } = Layout
const { Text } = Typography

const menuItems = [
  { key: '/', icon: <BarChartOutlined />, label: '首页' },
  { key: '/quick-crawl', icon: <ThunderboltOutlined />, label: '快速爬取' },
  { key: '/schedule', icon: <ClockCircleOutlined />, label: '定时任务' },
  { key: '/logs', icon: <FileSearchOutlined />, label: '爬取日志' },
  { key: '/data', icon: <DatabaseOutlined />, label: '面经数据' },
  { key: '/cards', icon: <FileMarkdownOutlined />, label: '卡片工坊' },
  { key: '/wechat', icon: <SendOutlined />, label: '公众号工坊' },
]

const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { connected, progresses } = useCrawlStore()
  useWebSocket()

  const runningCount = useMemo(
    () => Object.values(progresses).filter((p) => p.status === 'running').length,
    [progresses],
  )

  return (
    <Layout className="app-shell">
      <Sider trigger={null} collapsible collapsed={collapsed} width={232} className="app-sider">
        <div className="brand">
          <div className="brand-mark">牛</div>
          {!collapsed && (
            <div>
              <Text className="brand-title">牛客面经助手</Text>
              <Text className="brand-subtitle">内容采集与卡片生成</Text>
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
