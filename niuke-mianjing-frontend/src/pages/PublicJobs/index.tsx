import React, { useEffect, useMemo, useState } from 'react'
import { Button, Drawer, Empty, Input, message, Pagination, Skeleton, Space, Tag, Typography } from 'antd'
import {
  ArrowLeftOutlined,
  ArrowRightOutlined,
  BankOutlined,
  EnvironmentOutlined,
  HomeOutlined,
  LinkOutlined,
  RadarChartOutlined,
  SearchOutlined,
  TeamOutlined,
} from '@ant-design/icons'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { recruitmentApi } from '@/api'
import type { RecruitmentJob, RecruitmentSource, RecruitmentTrack } from '@/api/types'

const { Paragraph, Text, Title } = Typography
const PAGE_SIZE = 12
const sourceLogos: Record<string, string> = {
  bytedance: '/company-logos/字节跳动.svg',
  tencent: '/company-logos/腾讯-01.svg',
}

const formatDate = (value?: string | null) => {
  if (!value) return '官网实时岗位'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '官网实时岗位'
  return date.toLocaleDateString('zh-CN', { year: 'numeric', month: 'short', day: 'numeric' })
}

const renderTextBlocks = (value?: string) => {
  const blocks = (value || '')
    .split(/\n+/)
    .map((item) => item.trim())
    .filter(Boolean)

  if (!blocks.length) return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="官网暂未提供详细内容" />
  return (
    <div className="job-rich-text">
      {blocks.map((item, index) => <p key={`${item.slice(0, 24)}-${index}`}>{item}</p>)}
    </div>
  )
}

const PublicJobs: React.FC = () => {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const [sources, setSources] = useState<RecruitmentSource[]>([])
  const [tracks, setTracks] = useState<RecruitmentTrack[]>([])
  const [source, setSource] = useState(searchParams.get('source') || 'tencent')
  const [track, setTrack] = useState(searchParams.get('track') || '')
  const [keyword, setKeyword] = useState(searchParams.get('keyword') || '')
  const [queryKeyword, setQueryKeyword] = useState(searchParams.get('keyword') || '')
  const [jobs, setJobs] = useState<RecruitmentJob[]>([])
  const [selectedJob, setSelectedJob] = useState<RecruitmentJob | null>(null)
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({ current: 1, total: 0 })

  const activeSource = useMemo(
    () => sources.find((item) => item.source === source),
    [source, sources],
  )

  const loadJobs = async (page = 1, nextSource = source, nextKeyword = queryKeyword, nextTrack = track) => {
    try {
      setLoading(true)
      const data = await recruitmentApi.jobs({
        source: nextSource,
        keyword: nextKeyword || undefined,
        track: nextKeyword ? undefined : nextTrack || undefined,
        page,
        page_size: PAGE_SIZE,
      })
      setJobs(data?.items || [])
      setPagination({ current: page, total: data?.total || 0 })
    } catch (error: unknown) {
      message.error((error as Error).message || '官网岗位加载失败')
      setJobs([])
    } finally {
      setLoading(false)
    }
  }

  const search = () => {
    const value = keyword.trim()
    setQueryKeyword(value)
    setSearchParams({ source, ...(track ? { track } : {}), ...(value ? { keyword: value } : {}) })
    void loadJobs(1, source, value, track)
  }

  const changeSource = (nextSource: string) => {
    setSource(nextSource)
    setPagination((prev) => ({ ...prev, current: 1 }))
    setSearchParams({ source: nextSource, ...(track ? { track } : {}), ...(queryKeyword ? { keyword: queryKeyword } : {}) })
    void loadJobs(1, nextSource, queryKeyword, track)
  }

  const changeTrack = (nextTrack: string) => {
    setTrack(nextTrack)
    setKeyword('')
    setQueryKeyword('')
    setPagination((prev) => ({ ...prev, current: 1 }))
    setSearchParams({ source, ...(nextTrack ? { track: nextTrack } : {}) })
    void loadJobs(1, source, '', nextTrack)
  }

  useEffect(() => {
    recruitmentApi.sources().then(setSources).catch(() => setSources([]))
    recruitmentApi.tracks().then(setTracks).catch(() => setTracks([]))
    void loadJobs(1)
  }, [])

  return (
    <div className="public-page jobs-page">
      <header className="public-nav">
        <button className="public-brand" onClick={() => navigate('/')}>
          <img src="/offerlens.svg" alt="OfferLens" />
          <strong>OfferLens</strong>
        </button>
        <nav>
          <Button type="text" icon={<HomeOutlined />} onClick={() => navigate('/')}>首页</Button>
          <Button type="text" onClick={() => navigate('/interviews')}>面经库</Button>
          <Button type="primary" onClick={() => navigate('/jobs')}>职位雷达</Button>
        </nav>
      </header>

      <main>
        <section className="jobs-hero">
          <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate('/')}>返回首页</Button>
          <Tag color="blue" className="hero-tag">Official Career Radar</Tag>
          <Title>看见大厂正在寻找什么样的人</Title>
          <Paragraph>
            聚合大厂招聘官网公开岗位。先看真实岗位要求，再决定该补什么能力、准备什么项目，
            比盲目背题更接近市场答案。
          </Paragraph>
          <div className="jobs-hero-metrics">
            <div><strong>{pagination.total.toLocaleString()}</strong><span>{activeSource?.company || '大厂'}公开岗位</span></div>
            <div><strong>官方</strong><span>岗位来源可追溯</span></div>
            <div><strong>持续</strong><span>跟踪人才偏好</span></div>
          </div>
        </section>

        <section className="jobs-control-panel">
          <div className="source-switcher">
            {sources.map((item) => (
              <button
                key={item.source}
                className={source === item.source ? 'active' : ''}
                onClick={() => changeSource(item.source)}
              >
                <span><img src={sourceLogos[item.source]} alt={`${item.company} logo`} /></span>
                <div>
                  <b>{item.company}</b>
                  <small>{item.description}</small>
                </div>
              </button>
            ))}
          </div>
          <div className="job-track-switcher">
            <button className={!track ? 'active' : ''} onClick={() => changeTrack('')}>
              <b>全部方向</b>
              <small>查看官网全部公开岗位</small>
            </button>
            {tracks.map((item) => (
              <button key={item.id} className={track === item.id ? 'active' : ''} onClick={() => changeTrack(item.id)}>
                <b>{item.name}</b>
                <small>{item.description}</small>
              </button>
            ))}
          </div>
          <div className="jobs-search">
            <Input
              size="large"
              prefix={<SearchOutlined />}
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
              onPressEnter={search}
              placeholder="搜索岗位，例如：后端、AI、基础架构、产品经理"
              allowClear
            />
            <Button type="primary" size="large" icon={<RadarChartOutlined />} loading={loading} onClick={search}>
              搜索官网岗位
            </Button>
          </div>
          <div className="jobs-result-meta">
            <Text>当前展示 <b>{activeSource?.company || source}</b> 的公开岗位</Text>
            <Text type="secondary">
              {queryKeyword ? `关键词：${queryKeyword}` : track ? `方向：${tracks.find((item) => item.id === track)?.name || track}` : '全部岗位'}
              {' '}· 共 {pagination.total.toLocaleString()} 条
            </Text>
          </div>
        </section>

        {loading ? (
          <div className="job-grid">
            {Array.from({ length: 6 }).map((_, index) => (
              <div className="job-card skeleton" key={index}><Skeleton active paragraph={{ rows: 4 }} /></div>
            ))}
          </div>
        ) : jobs.length > 0 ? (
          <div className="job-grid">
            {jobs.map((job) => (
              <button className="job-card" key={`${job.source}-${job.source_job_id}`} onClick={() => setSelectedJob(job)}>
                <div className="job-card-top">
                  <span className={`job-company-mark ${job.source}`}>
                    <img src={sourceLogos[job.source]} alt={`${job.company} logo`} />
                  </span>
                  <Tag color="blue">{job.category || job.job_family || '综合岗位'}</Tag>
                </div>
                <h2>{job.title}</h2>
                <div className="job-card-meta">
                  <span><EnvironmentOutlined /> {job.location || job.country || '地点面议'}</span>
                  {job.business_unit && <span><BankOutlined /> {job.business_unit}</span>}
                  {job.experience && <span><TeamOutlined /> {job.experience}</span>}
                </div>
                <p>{job.description || job.requirements || '点击查看官网岗位详情'}</p>
                <div className="job-card-footer">
                  <small>{formatDate(job.updated_at)}</small>
                  <span>查看要求 <ArrowRightOutlined /></span>
                </div>
              </button>
            ))}
          </div>
        ) : (
          <div className="jobs-empty"><Empty description="没有找到匹配岗位，换个关键词试试" /></div>
        )}

        <div className="public-pagination">
          <Pagination
            current={pagination.current}
            pageSize={PAGE_SIZE}
            total={pagination.total}
            showSizeChanger={false}
            onChange={(page) => {
              setPagination((prev) => ({ ...prev, current: page }))
              void loadJobs(page)
              window.scrollTo({ top: 300, behavior: 'smooth' })
            }}
          />
        </div>
      </main>

      <Drawer
        title={null}
        open={Boolean(selectedJob)}
        width={Math.min(window.innerWidth - 24, 820)}
        onClose={() => setSelectedJob(null)}
        className="job-detail-drawer"
      >
        {selectedJob && (
          <article className="job-detail">
            <div className="job-detail-hero">
              <div className={`job-company-mark large ${selectedJob.source}`}>
                <img src={sourceLogos[selectedJob.source]} alt={`${selectedJob.company} logo`} />
              </div>
              <Space size={8} wrap>
                <Tag color="blue">{selectedJob.company}</Tag>
                <Tag>{selectedJob.category || selectedJob.job_family || '综合岗位'}</Tag>
                <Tag>{selectedJob.location || selectedJob.country || '地点面议'}</Tag>
              </Space>
              <h1>{selectedJob.title}</h1>
              <div className="job-detail-meta">
                {selectedJob.business_unit && <span><BankOutlined /> {selectedJob.business_unit}</span>}
                {selectedJob.employment_type && <span><TeamOutlined /> {selectedJob.employment_type}</span>}
                <span><EnvironmentOutlined /> {selectedJob.location || selectedJob.country || '地点面议'}</span>
              </div>
              <Button type="primary" size="large" href={selectedJob.source_url} target="_blank" icon={<LinkOutlined />}>
                前往官网查看与投递
              </Button>
            </div>
            <section>
              <h2>岗位职责</h2>
              {renderTextBlocks(selectedJob.description)}
            </section>
            <section>
              <h2>任职要求</h2>
              {renderTextBlocks(selectedJob.requirements)}
            </section>
            {selectedJob.preferred_qualifications && (
              <section>
                <h2>优先条件</h2>
                {renderTextBlocks(selectedJob.preferred_qualifications)}
              </section>
            )}
          </article>
        )}
      </Drawer>
    </div>
  )
}

export default PublicJobs
