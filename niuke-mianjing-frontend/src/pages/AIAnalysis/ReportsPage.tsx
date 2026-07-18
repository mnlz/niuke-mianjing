import React, { useEffect, useMemo, useState } from 'react'
import { Button, Drawer, Empty, Input, message, Popconfirm, Select, Spin, Tag } from 'antd'
import { DeleteOutlined, DownloadOutlined, EyeOutlined, FileTextOutlined, PlusOutlined, SearchOutlined } from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { recruitmentApi } from '@/api'
import type { RecruitmentAIReportRecord } from '@/api/types'
import { clearUserSession, getUserToken, userLoginPath } from '@/utils/auth'
import AnalysisHeader from './AnalysisHeader'
import { filterReports, type AnalysisReportType } from './analysisUtils'
import { recruitmentTypeName, reportTypeMeta, reportTypes } from './config'
import './style.css'

const ReportsPage: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams, setSearchParams] = useSearchParams()
  const [reports, setReports] = useState<RecruitmentAIReportRecord[]>([])
  const [query, setQuery] = useState('')
  const [type, setType] = useState<AnalysisReportType | 'all'>('all')
  const [sort, setSort] = useState<'new' | 'old'>('new')
  const [selected, setSelected] = useState<RecruitmentAIReportRecord | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!getUserToken()) {
      navigate(userLoginPath(`${location.pathname}${location.search}`), { replace: true })
      return
    }
    recruitmentApi.aiReports().then((rows) => {
      setReports(rows || [])
      const requested = searchParams.get('id')
      if (requested) setSelected((rows || []).find((item) => item.report_code === requested) || null)
    }).catch((error: unknown) => {
      clearUserSession()
      message.error((error as Error).message || '报告加载失败')
      navigate(userLoginPath('/ai-analysis/reports'), { replace: true })
    }).finally(() => setLoading(false))
  }, [])

  const visibleReports = useMemo(() => [...filterReports(reports, query, type)].sort((a, b) => sort === 'new' ? b.created_at.localeCompare(a.created_at) : a.created_at.localeCompare(b.created_at)), [reports, query, type, sort])
  const companies = new Set(reports.map((item) => item.company)).size
  const fullReports = reports.filter((item) => item.report_type === 'full').length
  const latestUpdate = reports.length ? new Date(Math.max(...reports.map((item) => new Date(item.updated_at || item.created_at).getTime()))).toLocaleString('zh-CN') : '暂无报告'
  const openReport = (report: RecruitmentAIReportRecord) => { setSelected(report); setSearchParams({ id: report.report_code }) }
  const closeReport = () => { setSelected(null); setSearchParams({}) }
  const deleteReport = async (reportCode: string) => {
    try {
      await recruitmentApi.deleteAIReport(reportCode)
      setReports((current) => current.filter((item) => item.report_code !== reportCode))
      if (selected?.report_code === reportCode) closeReport()
      message.success('报告已删除')
    } catch (error: unknown) {
      message.error((error as Error).message || '删除失败')
    }
  }
  const downloadReport = (report: RecruitmentAIReportRecord) => {
    const link = document.createElement('a')
    link.href = URL.createObjectURL(new Blob([report.content], { type: 'text/markdown;charset=utf-8' }))
    link.download = `${report.title.replace(/[\\/:*?"<>|]/g, '-')}.md`
    link.click()
    URL.revokeObjectURL(link.href)
  }

  return (
    <div className="ai-product-page ai-reports-page">
      <AnalysisHeader active="reports" />
      <main>
        <div className="ai-reports-title"><div><span>REPORT WORKSPACE</span><h1>AI 报告中心</h1><p>集中查看、筛选和导出当前账号的求职分析报告。</p></div><div className="ai-report-head-meta"><span>最近更新：{latestUpdate}</span><i /><span>共 <b>{reports.length}</b> 份报告</span><Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/ai-analysis/create')}>新建分析</Button></div></div>
        <section className="ai-report-kpis">
          <article><span>TOTAL REPORTS</span><strong>{reports.length}</strong><small>账号云端保存</small></article>
          <article><span>ANALYZED COMPANIES</span><strong>{companies}</strong><small>目标公司去重统计</small></article>
          <article><span>FULL SCAN</span><strong>{fullReports}<em> / {reports.length || 0}</em></strong><small>4 元素完整报告</small></article>
        </section>
        <section className="ai-report-workspace">
          <aside className="ai-report-sidebar"><b>// 报告分类</b><button className={type === 'all' ? 'active' : ''} onClick={() => setType('all')}><span>全部报告</span><em>{reports.length}</em></button>{reportTypes.map((item) => <button key={item.value} className={type === item.value ? 'active' : ''} onClick={() => setType(item.value)}><span>{item.short}</span><em>{reports.filter((report) => report.report_type === item.value).length}</em></button>)}<div className="ai-report-side-note"><FileTextOutlined /><b>报告已同步</b><p>报告保存在账号中，换设备登录也可以继续查看。</p></div></aside>
          <div className="ai-report-list-panel">
            <div className="ai-report-toolbar"><Input prefix={<SearchOutlined />} value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索报告、公司或岗位" allowClear /><Select value={sort} onChange={setSort} options={[{ label: '最近生成', value: 'new' }, { label: '最早生成', value: 'old' }]} /><span>共 {visibleReports.length} 份</span></div>
            {loading ? <div className="page-loading"><Spin /></div> : visibleReports.length ? <div className="ai-report-table"><div className="ai-report-row header"><span>报告</span><span>类型 / 范围</span><span>生成时间</span><span>操作</span></div>{visibleReports.map((report) => <div className="ai-report-row" key={report.report_code} onClick={() => openReport(report)}><span className="report-name"><i><FileTextOutlined /></i><span><b>{report.title}</b><small>{report.report_code}</small></span></span><span><Tag color={report.report_type === 'full' ? 'blue' : 'default'}>{reportTypeMeta(report.report_type).short}</Tag><b>{report.track_name}</b><small>{report.company} · {recruitmentTypeName(report.recruitment_type)}</small></span><span><b>{new Date(report.created_at).toLocaleDateString('zh-CN')}</b><small>{new Date(report.created_at).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}</small></span><span className="report-actions"><Button type="text" aria-label="查看报告" icon={<EyeOutlined />} onClick={(event) => { event.stopPropagation(); openReport(report) }} /><Button type="text" aria-label="下载报告" icon={<DownloadOutlined />} onClick={(event) => { event.stopPropagation(); downloadReport(report) }} /><Popconfirm title="删除这份报告？" onConfirm={() => deleteReport(report.report_code)}><Button danger type="text" aria-label="删除报告" icon={<DeleteOutlined />} onClick={(event) => event.stopPropagation()} /></Popconfirm></span></div>)}</div> : <Empty description="还没有生成报告"><Button type="primary" onClick={() => navigate('/ai-analysis/create')}>新建第一份报告</Button></Empty>}
          </div>
        </section>
      </main>
      <Drawer className="ai-report-drawer" width={720} open={Boolean(selected)} onClose={closeReport} title={selected ? <div><small>{selected.report_code}</small><b>{selected.title}</b></div> : null} extra={selected && <Button icon={<DownloadOutlined />} onClick={() => downloadReport(selected)}>下载 Markdown</Button>}>
        {selected && <><div className="ai-report-drawer-cover"><small>OFFERLENS AI REPORT</small><h2>{selected.title}</h2><p>{selected.company} · {selected.track_name} · {recruitmentTypeName(selected.recruitment_type)}</p></div><div className="ai-drawer-meta"><Tag color="blue">{reportTypeMeta(selected.report_type).label}</Tag><span>模型：{selected.model}</span><span>{new Date(selected.created_at).toLocaleString('zh-CN')}</span></div><div className="ai-report-markdown"><ReactMarkdown remarkPlugins={[remarkGfm]}>{selected.content}</ReactMarkdown></div></>}
      </Drawer>
    </div>
  )
}

export default ReportsPage
