import React from 'react'
import { Button } from 'antd'
import { FileTextOutlined, PlusOutlined, ReadOutlined, RobotOutlined } from '@ant-design/icons'
import { useLocation, useNavigate } from 'react-router-dom'
import UserSessionButton from '@/components/UserSessionButton'
import { getUserToken, userLoginPath } from '@/utils/auth'

type ActivePage = 'home' | 'create' | 'sample' | 'reports'

const AnalysisHeader: React.FC<{ active: ActivePage }> = ({ active }) => {
  const navigate = useNavigate()
  const location = useLocation()
  const openReports = () => navigate(getUserToken() ? '/ai-analysis/reports' : userLoginPath(`${location.pathname}${location.search}`))
  const navItems = [
    { key: 'home', label: 'AI 分析', path: '/ai-analysis' },
    { key: 'create', label: '新建分析', path: '/ai-analysis/create' },
    { key: 'sample', label: '报告示例', path: '/ai-analysis/sample-report' },
  ] as const
  return (
    <header className="ai-site-header">
      <div className="ai-site-nav">
        <button className="public-brand" onClick={() => navigate('/')}>
          <img src="/offerlens.svg" alt="OfferLens" />
          <span><strong>OfferLens</strong><small>AI Insights</small></span>
        </button>
        <nav className="ai-header-primary-nav" aria-label="AI 分析导航">
          {navItems.map((item) => <Button key={item.key} type="text" className={`ai-header-nav-item${active === item.key ? ' active' : ''}`} aria-current={active === item.key ? 'page' : undefined} onClick={() => navigate(item.path)}>{item.label}</Button>)}
          <Button type="text" className={`ai-header-nav-item${active === 'reports' ? ' active' : ''}`} aria-current={active === 'reports' ? 'page' : undefined} onClick={openReports}>我的报告</Button>
        </nav>
        <nav className="ai-header-mobile-nav" aria-label="AI 分析快捷导航">
          <Button type={active === 'home' ? 'primary' : 'text'} aria-label="AI 分析" aria-current={active === 'home' ? 'page' : undefined} icon={<RobotOutlined />} onClick={() => navigate('/ai-analysis')} />
          <Button type={active === 'create' ? 'primary' : 'text'} aria-label="新建分析" aria-current={active === 'create' ? 'page' : undefined} icon={<PlusOutlined />} onClick={() => navigate('/ai-analysis/create')} />
          <Button type={active === 'sample' ? 'primary' : 'text'} aria-label="报告示例" aria-current={active === 'sample' ? 'page' : undefined} icon={<ReadOutlined />} onClick={() => navigate('/ai-analysis/sample-report')} />
          <Button type={active === 'reports' ? 'primary' : 'text'} aria-label="我的报告" aria-current={active === 'reports' ? 'page' : undefined} icon={<FileTextOutlined />} onClick={openReports} />
        </nav>
        <div className="ai-header-account">
          <UserSessionButton />
          <Button className="ai-header-report-cta" type="primary" onClick={openReports}>我的报告</Button>
        </div>
      </div>
    </header>
  )
}

export default AnalysisHeader
