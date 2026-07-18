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
  RobotOutlined,
  SearchOutlined,
  TeamOutlined,
} from '@ant-design/icons'
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { recruitmentApi } from '@/api'
import type { RecruitmentInterview, RecruitmentJob, RecruitmentJobPage, RecruitmentSource, RecruitmentType } from '@/api/types'
import { recruitmentSourceLogos, recruitmentTypeName, recruitmentTypeOptions } from '@/constants/recruitment'
import { formatDisplayTime } from '@/utils/datetime'
import { interviewRoute } from './jobUtils'
import UserSessionButton from '@/components/UserSessionButton'
import { isAnonymousPageAllowed, userLoginPath } from '@/utils/auth'

const { Paragraph, Text, Title } = Typography
const PAGE_SIZE = 12
const PRIMARY_TECH_FAMILY_COUNT = 10

const analysisTrackByRoleFamily: Record<string, string> = {
  backend_software: 'backend',
  sre_devops: 'backend',
  security: 'backend',
  frontend_fullstack: 'frontend',
  client: 'client',
  game_multimedia: 'client',
  testing_quality: 'testing',
  data_engineering: 'data',
  data_analysis: 'data',
  ai_algorithm: 'ai',
  ai_application: 'ai',
  ai_infra: 'ai',
}

const specialtyLabels: Record<string, string> = {
  ai_related: 'AI 相关',
  llm: '大模型',
  agent_rag: 'Agent/RAG',
  recommendation: '推荐系统',
  search: '搜索',
  computer_vision: '计算机视觉',
  nlp_speech: 'NLP/语音',
  multimodal_aigc: '多模态/AIGC',
  ai_safety: 'AI Safety',
  embodied_ai: '具身智能',
  ai_coding: 'AI Coding',
  training_inference: '训练/推理',
  ai_chip: 'AI 芯片',
  cloud_native: '云原生',
  distributed_systems: '分布式系统',
  storage_database: '数据库/存储',
  network: '网络',
  audio_video: '音视频',
  graphics: '图形学',
  game_engine: '游戏引擎',
}

const businessDomainLabels: Record<string, string> = {
  ecommerce: '电商',
  ads: '广告商业化',
  payment_finance: '支付金融',
  gaming: '游戏',
  cloud: '云计算',
  enterprise: '企业服务',
  content_social: '内容社交',
  international: '国际化',
}

const jobCategoryLabel = (job: RecruitmentJob) =>
  job.display_category || job.inferred_track_name || job.category || job.job_family || '综合岗位'

const officialCategoryLabel = (job: RecruitmentJob) => {
  const taxonomy = job.official_taxonomy
  const parts = taxonomy
    ? [taxonomy.level1?.name, taxonomy.level2?.name, taxonomy.level3?.name].filter(Boolean)
    : [job.category, job.job_family].filter(Boolean)
  return Array.from(new Set(parts)).join(' / ')
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
  const location = useLocation()
  const [searchParams, setSearchParams] = useSearchParams()
  const [sources, setSources] = useState<RecruitmentSource[]>([])
  const [source, setSource] = useState(searchParams.get('source') || 'tencent')
  const [roleGroup, setRoleGroup] = useState(searchParams.get('role_group') || '')
  const [roleFamily, setRoleFamily] = useState(searchParams.get('role_family') || '')
  const [aiHot, setAiHot] = useState(searchParams.get('ai_hot') === '1')
  const [showAllTechnical, setShowAllTechnical] = useState(false)
  const [recruitmentType, setRecruitmentType] = useState<RecruitmentType>((searchParams.get('type') as RecruitmentType) || 'campus')
  const [keyword, setKeyword] = useState(searchParams.get('keyword') || '')
  const [queryKeyword, setQueryKeyword] = useState(searchParams.get('keyword') || '')
  const [jobs, setJobs] = useState<RecruitmentJob[]>([])
  const [roleGroups, setRoleGroups] = useState<NonNullable<RecruitmentJobPage['role_groups']>>([])
  const [facetTotal, setFacetTotal] = useState(0)
  const [selectedJob, setSelectedJob] = useState<RecruitmentJob | null>(null)
  const [interviews, setInterviews] = useState<RecruitmentInterview[]>([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({ current: 1, total: 0 })

  const activeSource = useMemo(
    () => sources.find((item) => item.source === source),
    [source, sources],
  )
  const availableRecruitmentTypeOptions = useMemo(() => {
    const supported = activeSource?.supported_recruitment_types
    if (!supported?.length) return recruitmentTypeOptions
    return recruitmentTypeOptions.filter((item) => supported.includes(item.value))
  }, [activeSource])
  const logoMap = useMemo(
    () => Object.fromEntries(sources.map((item) => [item.source, item.logo || recruitmentSourceLogos[item.source]])),
    [sources],
  )
  const activeRoleGroup = useMemo(
    () => roleGroups.find((item) => item.id === roleGroup),
    [roleGroup, roleGroups],
  )
  const roleFamilies = activeRoleGroup?.role_families || []
  const activeRoleFamily = roleFamilies.find((item) => item.id === roleFamily)
  const visibleRoleFamilies = activeRoleGroup?.id === 'engineering' && !showAllTechnical
    ? roleFamilies.slice(0, PRIMARY_TECH_FAMILY_COUNT)
    : roleFamilies

  const loadJobs = async (
    page = 1,
    nextSource = source,
    nextKeyword = queryKeyword,
    nextRoleGroup = roleGroup,
    nextRoleFamily = roleFamily,
    nextRecruitmentType = recruitmentType,
    nextAiHot = aiHot,
  ) => {
    try {
      setLoading(true)
      const data = await recruitmentApi.jobs({
        source: nextSource,
        keyword: nextKeyword || undefined,
        role_group: nextRoleGroup || undefined,
        role_family: nextRoleFamily || undefined,
        ai_hot: nextAiHot || undefined,
        recruitment_type: nextRecruitmentType,
        page,
        page_size: PAGE_SIZE,
      })
      setJobs(data?.items || [])
      setRoleGroups(data?.role_groups || [])
      setFacetTotal(data?.facet_total || data?.total || 0)
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
    setSearchParams({ source, type: recruitmentType, ...(aiHot ? { ai_hot: '1' } : {}), ...(roleGroup ? { role_group: roleGroup } : {}), ...(roleFamily ? { role_family: roleFamily } : {}), ...(value ? { keyword: value } : {}) })
    void loadJobs(1, source, value, roleGroup, roleFamily, recruitmentType, aiHot)
  }

  const changeSource = (nextSource: string) => {
    const nextSourceMeta = sources.find((item) => item.source === nextSource)
    const supportedTypes = nextSourceMeta?.supported_recruitment_types || []
    const nextRecruitmentType = supportedTypes.length && !supportedTypes.includes(recruitmentType)
      ? supportedTypes[0]
      : recruitmentType
    setSource(nextSource)
    setRecruitmentType(nextRecruitmentType)
    setRoleGroup('')
    setRoleFamily('')
    setShowAllTechnical(false)
    setPagination((prev) => ({ ...prev, current: 1 }))
    setSearchParams({ source: nextSource, type: nextRecruitmentType, ...(aiHot ? { ai_hot: '1' } : {}), ...(queryKeyword ? { keyword: queryKeyword } : {}) })
    void loadJobs(1, nextSource, queryKeyword, '', '', nextRecruitmentType, aiHot)
  }

  const changeRecruitmentType = (nextType: RecruitmentType) => {
    setRecruitmentType(nextType)
    setRoleGroup('')
    setRoleFamily('')
    setShowAllTechnical(false)
    setPagination((prev) => ({ ...prev, current: 1 }))
    setSearchParams({ source, type: nextType, ...(aiHot ? { ai_hot: '1' } : {}), ...(queryKeyword ? { keyword: queryKeyword } : {}) })
    void loadJobs(1, source, queryKeyword, '', '', nextType, aiHot)
  }

  const changeAiHot = () => {
    const nextAiHot = !aiHot
    setAiHot(nextAiHot)
    setRoleGroup('')
    setRoleFamily('')
    setKeyword('')
    setQueryKeyword('')
    setShowAllTechnical(false)
    setPagination((prev) => ({ ...prev, current: 1 }))
    setSearchParams({ source, type: recruitmentType, ...(nextAiHot ? { ai_hot: '1' } : {}) })
    void loadJobs(1, source, '', '', '', recruitmentType, nextAiHot)
  }

  const changeRoleGroup = (nextRoleGroup: string) => {
    setAiHot(false)
    setRoleGroup(nextRoleGroup)
    setRoleFamily('')
    setKeyword('')
    setQueryKeyword('')
    setShowAllTechnical(false)
    setPagination((prev) => ({ ...prev, current: 1 }))
    setSearchParams({ source, type: recruitmentType, ...(nextRoleGroup ? { role_group: nextRoleGroup } : {}) })
    void loadJobs(1, source, '', nextRoleGroup, '', recruitmentType, false)
  }

  const changeRoleFamily = (nextRoleFamily: string) => {
    setAiHot(false)
    setRoleFamily(nextRoleFamily)
    setKeyword('')
    setQueryKeyword('')
    setPagination((prev) => ({ ...prev, current: 1 }))
    setSearchParams({ source, type: recruitmentType, ...(roleGroup ? { role_group: roleGroup } : {}), ...(nextRoleFamily ? { role_family: nextRoleFamily } : {}) })
    void loadJobs(1, source, '', roleGroup, nextRoleFamily, recruitmentType, false)
  }

  const openAIAnalysis = () => {
    const params = new URLSearchParams({ report: 'full', source, type: recruitmentType })
    const track = aiHot ? 'ai' : analysisTrackByRoleFamily[roleFamily]
    if (track) params.set('track', track)
    navigate(`/ai-analysis/create?${params.toString()}`)
  }

  useEffect(() => {
    recruitmentApi.sources().then(setSources).catch(() => setSources([]))
    void loadJobs(1)
  }, [])

  useEffect(() => {
    const supportedTypes = activeSource?.supported_recruitment_types || []
    if (!supportedTypes.length || supportedTypes.includes(recruitmentType)) return
    const nextRecruitmentType = supportedTypes[0]
    setRecruitmentType(nextRecruitmentType)
    setPagination((prev) => ({ ...prev, current: 1 }))
    setRoleGroup('')
    setRoleFamily('')
    setShowAllTechnical(false)
    setSearchParams({ source, type: nextRecruitmentType, ...(aiHot ? { ai_hot: '1' } : {}), ...(queryKeyword ? { keyword: queryKeyword } : {}) })
    void loadJobs(1, source, queryKeyword, '', '', nextRecruitmentType, aiHot)
  }, [activeSource, recruitmentType])

  useEffect(() => {
    if (!selectedJob?.source_job_id || !selectedJob.recruitment_type) {
      setInterviews([])
      return
    }
    recruitmentApi
      .interviews({
        source: selectedJob.source,
        recruitment_type: selectedJob.recruitment_type,
        source_job_id: selectedJob.source_job_id,
      })
      .then((data) => setInterviews(data || []))
      .catch(() => setInterviews([]))
  }, [selectedJob])

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
          <Button type="text" onClick={() => navigate('/ai-analysis')}>AI 分析</Button>
          <Button type="primary" onClick={() => navigate('/jobs')}>职位雷达</Button>
          <UserSessionButton />
        </nav>
      </header>

      <main>
        <section className="jobs-hero">
          <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate('/')}>返回首页</Button>
          <Tag color="blue" className="hero-tag">Official Career Radar</Tag>
          <Title>按真实岗位族筛选大厂职位</Title>
          <Paragraph>
            将各公司不同的官网分类统一为后端、算法、机器学习工程、数据、安全、硬件等可比较岗位族，
            同时保留官网原始分类和完整任职要求。
          </Paragraph>
          <div className="jobs-hero-metrics">
            <div><strong>{facetTotal.toLocaleString()}</strong><span>{activeSource?.company || '大厂'}公开岗位</span></div>
            <div><strong>{roleGroups.length}</strong><span>当前职位大类</span></div>
            <div><strong>官网</strong><span>职责与要求可追溯</span></div>
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
                <span><img src={item.logo || recruitmentSourceLogos[item.source]} alt={`${item.company} logo`} /></span>
                <div>
                  <b>{item.company}</b>
                  <small>{(item.supported_recruitment_types || []).map(recruitmentTypeName).join(' · ') || '官网公开岗位'}</small>
                </div>
              </button>
            ))}
          </div>
          <div className="recruitment-type-switcher">
            {availableRecruitmentTypeOptions.map((item) => (
              <button
                key={item.value}
                className={recruitmentType === item.value ? 'active' : ''}
                onClick={() => changeRecruitmentType(item.value)}
              >
                {item.label}
              </button>
            ))}
          </div>
          <div className="job-family-heading">
            <div><b>职位大类</b><small>统一各公司官网的技术、产品、运营等不同叫法</small></div>
            <span>当前批次 {facetTotal.toLocaleString()} 条</span>
          </div>
          <div className="job-track-switcher job-group-switcher" aria-label="职位大类筛选">
            <button className={!roleGroup && !aiHot ? 'active' : ''} onClick={() => changeRoleGroup('')}>
              <b>全部大类</b>
              <small>{facetTotal.toLocaleString()}</small>
            </button>
            <button className={aiHot ? 'active ai-hot' : 'ai-hot'} onClick={changeAiHot}>
              <b>🔥 AI 热门岗位</b>
            </button>
            {roleGroups.map((item) => (
              <button key={item.id} className={roleGroup === item.id ? 'active' : ''} onClick={() => changeRoleGroup(item.id)}>
                <b>{item.name}</b>
                <small>{item.count.toLocaleString()}</small>
              </button>
            ))}
          </div>
          {activeRoleGroup && (
            <>
              <div className="job-family-heading sublevel">
                <div><b>{activeRoleGroup.name}岗位族</b><small>结合官网二级分类、岗位标题和职责进一步细分</small></div>
              </div>
              <div className="job-track-switcher" aria-label="岗位族筛选">
                <button className={!roleFamily ? 'active' : ''} onClick={() => changeRoleFamily('')}>
                  <b>全部{activeRoleGroup.name}</b>
                  <small>{activeRoleGroup.count.toLocaleString()}</small>
                </button>
                {visibleRoleFamilies.map((item) => (
                  <button key={item.id} className={roleFamily === item.id ? 'active' : ''} onClick={() => changeRoleFamily(item.id)}>
                    <b>{item.name}</b>
                    <small>{item.count.toLocaleString()}</small>
                  </button>
                ))}
                {activeRoleGroup.id === 'engineering' && roleFamilies.length > PRIMARY_TECH_FAMILY_COUNT && (
                  <button onClick={() => setShowAllTechnical((value) => !value)}>
                    <b>{showAllTechnical ? '收起更多' : `更多技术方向（${roleFamilies.length - PRIMARY_TECH_FAMILY_COUNT}）`}</b>
                  </button>
                )}
              </div>
            </>
          )}
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
              {recruitmentTypeName(recruitmentType)}
              {' · '}
              {aiHot
                ? `AI 热门岗位${queryKeyword ? ` · 关键词：${queryKeyword}` : ''}`
                : queryKeyword
                ? `关键词：${queryKeyword}`
                : roleFamily
                  ? `${activeRoleGroup?.name || '岗位'} / ${roleFamilies.find((item) => item.id === roleFamily)?.name || roleFamily}`
                  : roleGroup
                    ? `职位大类：${activeRoleGroup?.name || roleGroup}`
                    : '全部岗位'}
              {' '}· 共 {pagination.total.toLocaleString()} 条
            </Text>
          </div>
        </section>

        <section className="market-radar-banner jobs-ai-banner">
          <div>
            <Tag color="blue">AI OFFER REPORT</Tag>
            <Title level={2}>
              把{activeSource?.company || '当前公司'} · {aiHot ? 'AI 热门岗位' : activeRoleFamily?.name || activeRoleGroup?.name || '全部岗位'}，变成你的面试作战报告
            </Title>
            <Paragraph>
              自动结合官网岗位职责、任职要求、相关真实面经和你的简历，输出简历修改、项目深挖、八股重点与高频算法题。
            </Paragraph>
            <Space wrap>
              <Button type="primary" size="large" icon={<RobotOutlined />} onClick={openAIAnalysis}>
                用当前岗位生成报告 <ArrowRightOutlined />
              </Button>
              <Button size="large" onClick={() => navigate('/ai-analysis/sample-report')}>查看示例报告</Button>
            </Space>
          </div>
          <div className="market-radar-signals" aria-hidden="true">
            <span>{activeSource?.company || '目标公司'}</span>
            <span>{recruitmentTypeName(recruitmentType)}</span>
            <span>{aiHot ? 'AI 热门' : activeRoleFamily?.name || activeRoleGroup?.name || '岗位要求'}</span>
            <span>{pagination.total.toLocaleString()} 个当前岗位</span>
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
                    <img src={logoMap[job.source] || recruitmentSourceLogos[job.source]} alt={`${job.company} logo`} />
                  </span>
                  <Space size={6}>
                    <Tag color="blue">{jobCategoryLabel(job)}</Tag>
                    <Tag>{recruitmentTypeName(job.recruitment_type)}</Tag>
                  </Space>
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
              if (!isAnonymousPageAllowed(page)) {
                message.info('登录后可以继续浏览更多岗位')
                navigate(userLoginPath(`${location.pathname}${location.search}`))
                return
              }
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
                <img src={logoMap[selectedJob.source] || recruitmentSourceLogos[selectedJob.source]} alt={`${selectedJob.company} logo`} />
              </div>
              <Space size={8} wrap>
                <Tag color="blue">{selectedJob.company}</Tag>
                <Tag>{recruitmentTypeName(selectedJob.recruitment_type)}</Tag>
                <Tag>{jobCategoryLabel(selectedJob)}</Tag>
                {officialCategoryLabel(selectedJob) && <Tag>官方：{officialCategoryLabel(selectedJob)}</Tag>}
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
            {Boolean(selectedJob.specialties?.length || selectedJob.business_domains?.length || selectedJob.tech_stack?.length) && (
              <section className="job-signal-section">
                <h2>岗位能力画像</h2>
                <Space size={[8, 8]} wrap>
                  {selectedJob.specialties?.map((item) => <Tag color="blue" key={`specialty-${item}`}>{specialtyLabels[item] || item}</Tag>)}
                  {selectedJob.business_domains?.map((item) => <Tag color="purple" key={`domain-${item}`}>{businessDomainLabels[item] || item}</Tag>)}
                  {selectedJob.tech_stack?.map((item) => <Tag key={`stack-${item}`}>{item}</Tag>)}
                </Space>
              </section>
            )}
            <section>
              <h2>岗位职责</h2>
              {renderTextBlocks(selectedJob.description)}
            </section>
            <section>
              <h2>任职要求</h2>
              {renderTextBlocks(selectedJob.requirements)}
            </section>
            <section>
              <h2>过往面试</h2>
              {interviews.length ? (
                <div className="job-interview-list">
                  {interviews.map((item) => (
                    <Button key={item.id} type="link" onClick={() => navigate(interviewRoute(item))}>
                      {item.title} <Text type="secondary">· {item.post || '面经'} · {formatDisplayTime(item.edit_time)}</Text>
                    </Button>
                  ))}
                </div>
              ) : (
                <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂未匹配到该岗位相关面经" />
              )}
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
