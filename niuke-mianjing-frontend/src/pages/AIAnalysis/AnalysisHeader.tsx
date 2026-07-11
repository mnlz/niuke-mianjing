import React from 'react'
import { Button } from 'antd'
import { FileTextOutlined, PlusOutlined, RobotOutlined } from '@ant-design/icons'
import { useLocation, useNavigate } from 'react-router-dom'
import UserSessionButton from '@/components/UserSessionButton'
import { getUserToken, userLoginPath } from '@/utils/auth'

type ActivePage = 'home' | 'create' | 'reports'

const AnalysisHeader: React.FC<{ active: ActivePage }> = ({ active }) => {
  const navigate = useNavigate()
  const location = useLocation()
  const openReports = () => navigate(getUserToken() ? '/ai-analysis/reports' : userLoginPath(`${location.pathname}${location.search}`))
  return (
    <header className="ai-site-header">
      <div className="ai-site-nav">
        <button className="public-brand" onClick={() => navigate('/')}>
          <img src="/offerlens.svg" alt="OfferLens" />
          <span><strong>OfferLens</strong><small>AI Insights</small></span>
          <em className="ai-version-tag">AI · v2</em>
        </button>
        <nav className="ai-header-primary-nav" aria-label="AI 分析导航">
          <Button type={active === 'home' ? 'primary' : 'text'} aria-current={active === 'home' ? 'page' : undefined} onClick={() => navigate('/ai-analysis')}>AI 分析</Button>
          <Button type={active === 'reports' ? 'primary' : 'text'} aria-current={active === 'reports' ? 'page' : undefined} onClick={openReports}>我的报告</Button>
          {active !== 'create' && (
            <Button className="ai-header-create" type="primary" icon={<PlusOutlined />} onClick={() => navigate('/ai-analysis/create')}>
              新建分析
            </Button>
          )}
        </nav>
        <nav className="ai-header-mobile-nav" aria-label="AI 分析快捷导航">
          <Button type={active === 'home' ? 'primary' : 'text'} aria-label="AI 分析" aria-current={active === 'home' ? 'page' : undefined} icon={<RobotOutlined />} onClick={() => navigate('/ai-analysis')} />
          <Button type={active === 'reports' ? 'primary' : 'text'} aria-label="我的报告" aria-current={active === 'reports' ? 'page' : undefined} icon={<FileTextOutlined />} onClick={openReports} />
        </nav>
        <div className="ai-header-account">
          <UserSessionButton />
        </div>
      </div>
    </header>
  )
}

export default AnalysisHeader
