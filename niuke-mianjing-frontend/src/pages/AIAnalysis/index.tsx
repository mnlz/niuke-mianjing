import React, { useEffect, useMemo, useState } from 'react'
import { Button, Checkbox, Empty, Input, message, Select, Space, Tag, Typography, Upload } from 'antd'
import { CopyOutlined, HomeOutlined, RobotOutlined, UploadOutlined } from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useNavigate } from 'react-router-dom'
import { recruitmentApi } from '@/api'
import type { RecruitmentInterview, RecruitmentSource, RecruitmentTrack, RecruitmentType } from '@/api/types'
import { getAdminToken } from '@/utils/auth'
import { recruitmentTypeName, recruitmentTypes, reportTypes, type ReportType } from './config'
import './style.css'

const { Paragraph, Text, Title } = Typography

const AIAnalysis: React.FC = () => {
  const navigate = useNavigate()
  const [sources, setSources] = useState<RecruitmentSource[]>([])
  const [tracks, setTracks] = useState<RecruitmentTrack[]>([])
  const [source, setSource] = useState('tencent')
  const [compareSources, setCompareSources] = useState<string[]>(['tencent', 'meituan', 'bytedance'])
  const [recruitmentType, setRecruitmentType] = useState<RecruitmentType>('campus')
  const [track, setTrack] = useState('backend')
  const [reportType, setReportType] = useState<ReportType>('job')
  const [interviews, setInterviews] = useState<RecruitmentInterview[]>([])
  const [selectedInterviewIds, setSelectedInterviewIds] = useState<number[]>([])
  const [resume, setResume] = useState('')
  const [report, setReport] = useState('')
  const [loading, setLoading] = useState(false)
  const [interviewLoading, setInterviewLoading] = useState(false)

  const needsInterviews = reportType === 'job_interviews' || reportType === 'full'
  const needsResume = reportType === 'full'
  const isCompare = reportType === 'company_compare'
  const activeSource = useMemo(() => sources.find((item) => item.source === source), [source, sources])
  const singleTypeOptions = useMemo(() => {
    const supported = activeSource?.supported_recruitment_types
    return recruitmentTypes.filter((item) => !supported?.length || supported.includes(item.value))
  }, [activeSource])
  const sourceOptions = sources.map((item) => ({ label: item.company, value: item.source }))
  const compareOptions = sources
    .filter((item) => item.supported_recruitment_types?.includes(recruitmentType))
    .map((item) => ({ label: item.company, value: item.source }))

  useEffect(() => {
    recruitmentApi.sources()
      .then((data) => {
        setSources(data || [])
        const defaults = (data || [])
          .filter((item) => item.supported_recruitment_types?.includes(recruitmentType))
          .map((item) => item.source)
          .filter((item) => ['tencent', 'meituan', 'bytedance', 'jd'].includes(item))
          .slice(0, 4)
        if (defaults.length >= 2) setCompareSources(defaults)
      })
      .catch(() => setSources([]))
    recruitmentApi.tracks().then(setTracks).catch(() => setTracks([]))
  }, [])

  useEffect(() => {
    if (!needsInterviews) {
      setInterviews([])
      setSelectedInterviewIds([])
      return
    }
    setInterviewLoading(true)
    recruitmentApi.trackInterviews({ source, recruitment_type: recruitmentType, track, limit: 12 })
      .then((data) => {
        const items = data || []
        setInterviews(items)
        setSelectedInterviewIds(items.map((item) => item.id))
      })
      .catch(() => {
        setInterviews([])
        setSelectedInterviewIds([])
      })
      .finally(() => setInterviewLoading(false))
  }, [needsInterviews, source, recruitmentType, track])

  const changeSource = (value: string) => {
    const meta = sources.find((item) => item.source === value)
    const nextType = meta?.supported_recruitment_types?.includes(recruitmentType)
      ? recruitmentType
      : (meta?.supported_recruitment_types?.[0] as RecruitmentType) || recruitmentType
    setSource(value)
    setRecruitmentType(nextType)
  }

  const changeRecruitmentType = (value: RecruitmentType) => {
    setRecruitmentType(value)
    setCompareSources((prev) => prev.filter((item) =>
      sources.find((sourceItem) => sourceItem.source === item)?.supported_recruitment_types?.includes(value),
    ))
  }

  const copyReport = async () => {
    if (!report) return
    await navigator.clipboard.writeText(report)
    message.success('报告已复制')
  }

  const runReport = async () => {
    if (!getAdminToken()) {
      message.warning('AI 分析需要先登录后台')
      navigate('/admin-login', { state: { from: '/ai-analysis' } })
      return
    }
    if (isCompare && compareSources.length < 2) {
      message.warning('请至少选择 2 家公司')
      return
    }
    if (needsInterviews && !selectedInterviewIds.length) {
      message.warning('请至少选择 1 篇面经')
      return
    }
    if (needsResume && !resume.trim()) {
      message.warning('请先上传或粘贴简历')
      return
    }
    try {
      setLoading(true)
      const result = await recruitmentApi.aiReport({
        report_type: reportType,
        source,
        recruitment_type: recruitmentType,
        track,
        compare_sources: isCompare ? compareSources : undefined,
        selected_interview_ids: needsInterviews ? selectedInterviewIds.slice(0, 8) : undefined,
        resume: needsResume ? resume : '',
      })
      setReport(result.report)
    } catch (error: unknown) {
      message.error((error as Error).message || 'AI 报告生成失败')
    } finally {
      setLoading(false)
    }
  }

  const parseResume = async (file: File) => {
    if (!getAdminToken()) {
      message.warning('解析简历需要先登录后台')
      navigate('/admin-login', { state: { from: '/ai-analysis' } })
      return false
    }
    try {
      const data = await recruitmentApi.parseResume(file)
      setResume(data.text)
      message.success('简历解析完成')
    } catch (error: unknown) {
      message.error((error as Error).message || '简历解析失败')
    }
    return false
  }

  return (
    <div className="public-page ai-analysis-page">
      <header className="public-nav">
        <button className="public-brand" onClick={() => navigate('/')}>
          <img src="/offerlens.svg" alt="OfferLens" />
          <strong>OfferLens</strong>
        </button>
        <nav>
          <Button type="text" icon={<HomeOutlined />} onClick={() => navigate('/')}>首页</Button>
          <Button type="text" onClick={() => navigate('/interviews')}>面经库</Button>
          <Button type="text" onClick={() => navigate('/jobs')}>职位雷达</Button>
          <Button type="primary" icon={<RobotOutlined />}>AI 分析</Button>
        </nav>
      </header>

      <main>
        <section className="ai-page-heading">
          <Text>AI Analysis Workbench</Text>
          <Title>招聘情报分析</Title>
          <Paragraph>先选择分析类型，再组合官网岗位、真实面经和简历，生成可直接用于求职准备的报告。</Paragraph>
        </section>

        <section className="ai-report-type-row">
          {reportTypes.map((item) => (
            <button key={item.value} className={reportType === item.value ? 'active' : ''} onClick={() => setReportType(item.value)}>
              <strong>{item.label}</strong>
              <span>{item.desc}</span>
            </button>
          ))}
        </section>

        <section className="ai-workbench">
          <aside className="ai-config-panel">
            <div className="ai-panel-title">
              <Text>配置</Text>
              <strong>{isCompare ? '对比范围' : '分析对象'}</strong>
            </div>

            {isCompare ? (
              <label>
                <span>对比公司</span>
                <Select
                  mode="multiple"
                  value={compareSources}
                  onChange={setCompareSources}
                  options={compareOptions}
                  placeholder="选择需要对比的公司"
                />
              </label>
            ) : (
              <label>
                <span>公司</span>
                <Select value={source} onChange={changeSource} options={sourceOptions} />
              </label>
            )}

            <label>
              <span>招聘类型</span>
              <Select
                value={recruitmentType}
                onChange={changeRecruitmentType}
                options={isCompare ? recruitmentTypes : singleTypeOptions}
              />
            </label>
            <label>
              <span>岗位方向</span>
              <Select value={track} onChange={setTrack} options={tracks.map((item) => ({ label: item.name, value: item.id }))} />
            </label>

            <div className="ai-selected-job">
              <Text strong>{isCompare ? `对比 ${compareSources.length} 家公司` : activeSource?.company || source}</Text>
              <h2>{tracks.find((item) => item.id === track)?.name || track}</h2>
              <Space wrap>
                <Tag>{recruitmentTypeName(recruitmentType)}</Tag>
                <Tag>{reportTypes.find((item) => item.value === reportType)?.label}</Tag>
              </Space>
            </div>

            {needsInterviews && (
              <div className="ai-interview-picker">
                <div className="ai-picker-header">
                  <Text>最近面经</Text>
                  <Button
                    size="small"
                    type="link"
                    onClick={() => setSelectedInterviewIds(
                      selectedInterviewIds.length === interviews.length ? [] : interviews.map((item) => item.id),
                    )}
                  >
                    {selectedInterviewIds.length === interviews.length ? '取消全选' : '全选'}
                  </Button>
                </div>
                {interviewLoading ? (
                  <Text type="secondary">正在匹配最近面经...</Text>
                ) : interviews.length ? (
                  <div className="ai-interview-list">
                    {interviews.map((item) => (
                      <label key={item.id}>
                        <Checkbox
                          checked={selectedInterviewIds.includes(item.id)}
                          onChange={(event) => {
                            setSelectedInterviewIds((prev) =>
                              event.target.checked ? [...prev, item.id] : prev.filter((id) => id !== item.id),
                            )
                          }}
                        />
                        <span>
                          <b>{item.title}</b>
                          <small>{item.company} · {item.post || '面经'} · {item.edit_time || ''}</small>
                        </span>
                      </label>
                    ))}
                  </div>
                ) : (
                  <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂未匹配到该方向面经" />
                )}
              </div>
            )}

            {needsResume && (
              <div className="ai-resume-box">
                <Upload accept="application/pdf,.pdf" maxCount={1} beforeUpload={(file) => parseResume(file as File)} showUploadList={false}>
                  <Button icon={<UploadOutlined />}>上传 PDF 简历</Button>
                </Upload>
                <Input.TextArea
                  value={resume}
                  onChange={(event) => setResume(event.target.value)}
                  placeholder="可粘贴简历文本；完整分析会使用这里的内容。"
                  rows={5}
                />
              </div>
            )}

            <Button type="primary" size="large" icon={<RobotOutlined />} loading={loading} onClick={runReport} block>
              生成分析报告
            </Button>
          </aside>

          <section className="ai-report-panel">
            <div className="ai-report-header">
              <div>
                <Text>Report</Text>
                <h2>分析结果</h2>
              </div>
              <Space>
                {report && <Button icon={<CopyOutlined />} onClick={copyReport}>复制报告</Button>}
                <Tag color="blue">{reportTypes.find((item) => item.value === reportType)?.label}</Tag>
              </Space>
            </div>
            {report ? (
              <div className="ai-report-markdown">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{report}</ReactMarkdown>
              </div>
            ) : (
              <Empty description="生成后的报告会显示在这里" />
            )}
          </section>
        </section>
      </main>
    </div>
  )
}

export default AIAnalysis
