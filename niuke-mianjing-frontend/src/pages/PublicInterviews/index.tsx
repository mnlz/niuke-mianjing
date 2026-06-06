import React, { useEffect, useMemo, useState } from 'react'
import { Alert, Button, Card, Col, Drawer, Empty, Input, message, Pagination, Row, Select, Space, Tabs, Tag, Typography } from 'antd'
import {
  ArrowLeftOutlined,
  BarChartOutlined,
  CopyOutlined,
  FireOutlined,
  HomeOutlined,
  RobotOutlined,
  SearchOutlined,
  StarFilled,
  StarOutlined,
} from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { logApi, reviewApi } from '@/api'
import type { FilterOptions, NiukeRecord, ReviewAIResult, ReviewMastery, ReviewOverview, ReviewProgress } from '@/api/types'
import { hotInterviewCompanies } from '@/constants/companies'
import { formatDisplayTime } from '@/utils/datetime'
import { buildRecordMarkdown, getNowcoderUrl } from '@/utils/markdown'
import { getAdminToken } from '@/utils/auth'

const { Paragraph, Text, Title } = Typography

const PAGE_SIZE = 12

const defaultCompany = hotInterviewCompanies[0].searchName || hotInterviewCompanies[0].name

const masteryOptions: Array<{ label: string; value: ReviewMastery; color: string }> = [
  { label: '未开始', value: 'new', color: 'default' },
  { label: '学习中', value: 'learning', color: 'processing' },
  { label: '还模糊', value: 'fuzzy', color: 'warning' },
  { label: '已掌握', value: 'mastered', color: 'success' },
]

const masteryMeta = (value?: ReviewMastery) => masteryOptions.find((item) => item.value === value) || masteryOptions[0]

const normalizeInterviewText = (content: string) =>
  content
    .replace(/\r/g, '\n')
    .replace(/([。！？?])\s*(\d{1,2}[.、])/g, '$1\n$2')
    .replace(/([^\n])\s+(\d{1,2}[.、]\s*[^\d\s])/g, '$1\n$2')

const extractReviewCards = (record: NiukeRecord | null) => {
  if (!record?.content) return []
  const lines = normalizeInterviewText(record.content)
    .split(/\n+/)
    .map((line) => line.trim())
    .filter(Boolean)

  const questionLike = lines.filter((line) =>
    /(\?|？|什么|如何|怎么|区别|原理|介绍|讲讲|说说|实现|场景|为什么)/.test(line),
  )

  const source = questionLike.length > 0 ? questionLike : lines
  return source.slice(0, 8).map((line, index) => ({
    title: line.replace(/^\d{1,2}[.、]\s*/, '').slice(0, 72),
    tag: index < 3 ? '高优先级' : index < 6 ? '重点回看' : '补充',
  }))
}

const PublicInterviews: React.FC = () => {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const initialPost = searchParams.get('post') || ''
  const initialCompany = searchParams.get('company') || defaultCompany
  const [records, setRecords] = useState<NiukeRecord[]>([])
  const [selectedRecord, setSelectedRecord] = useState<NiukeRecord | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [detailTab, setDetailTab] = useState('raw')
  const [loading, setLoading] = useState(false)
  const [detailLoading, setDetailLoading] = useState(false)
  const [postFilter, setPostFilter] = useState(initialPost)
  const [companyFilter, setCompanyFilter] = useState(initialCompany)
  const [keyword, setKeyword] = useState('')
  const [filterOptions, setFilterOptions] = useState<FilterOptions>({ posts: [], companies: [] })
  const [pagination, setPagination] = useState({ current: 1, pageSize: PAGE_SIZE, total: 0 })
  const [progressMap, setProgressMap] = useState<Record<number, ReviewProgress>>({})
  const [overview, setOverview] = useState<ReviewOverview | null>(null)
  const [overviewLoading, setOverviewLoading] = useState(false)
  const [overviewDays, setOverviewDays] = useState(30)
  const [aiReview, setAiReview] = useState<ReviewAIResult | null>(null)
  const [aiLoading, setAiLoading] = useState(false)

  const selectedMarkdown = useMemo(
    () => (selectedRecord ? buildRecordMarkdown(selectedRecord) : ''),
    [selectedRecord],
  )

  const reviewCards = useMemo(() => extractReviewCards(selectedRecord), [selectedRecord])

  const selectedProgress = selectedRecord ? progressMap[selectedRecord.id] : null

  const postOptions = useMemo(
    () => [{ label: '全部方向', value: '' }, ...filterOptions.posts.map((post) => ({ label: post, value: post }))],
    [filterOptions.posts],
  )

  const companyOptions = useMemo(
    () => [
      { label: '全部公司', value: '' },
      ...filterOptions.companies.map((company) => ({ label: company, value: company })),
    ],
    [filterOptions.companies],
  )

  const visibleRecords = useMemo(() => {
    const value = keyword.trim().toLowerCase()
    if (!value) return records
    return records.filter((record) =>
      `${record.title} ${record.company} ${record.post} ${record.content}`.toLowerCase().includes(value),
    )
  }, [keyword, records])

  const fetchRecords = async (page = 1, pageSize = pagination.pageSize) => {
    try {
      setLoading(true)
      const offset = (page - 1) * pageSize
      const data = await logApi.records({
        post: postFilter || undefined,
        company: companyFilter || undefined,
        limit: pageSize,
        offset,
      })
      setRecords(data?.data || [])
      const ids = (data?.data || []).map((record) => record.id)
      if (ids.length) {
        reviewApi
          .progress(ids)
          .then((progressRows) => {
            setProgressMap((prev) => ({
              ...prev,
              ...Object.fromEntries((progressRows || []).map((item) => [item.record_id, item])),
            }))
          })
          .catch(() => undefined)
      }
      setPagination((prev) => ({
        ...prev,
        current: page,
        pageSize,
        total: data?.total || 0,
      }))
    } catch (e: unknown) {
      message.error((e as Error).message || '获取面经失败')
    } finally {
      setLoading(false)
    }
  }

  const openDetail = async (record: NiukeRecord) => {
    setDrawerOpen(true)
    setDetailTab('raw')
    setSelectedRecord(record)
    setAiReview(null)
    try {
      setDetailLoading(true)
      const detail = await logApi.record(record.id)
      setSelectedRecord(detail)
    } catch (e: unknown) {
      message.error((e as Error).message || '获取详情失败')
    } finally {
      setDetailLoading(false)
    }
  }

  const copyMarkdown = async () => {
    if (!selectedMarkdown) return
    await navigator.clipboard.writeText(selectedMarkdown)
    message.success('Markdown 已复制')
  }

  const updateRecordProgress = async (
    recordId: number,
    patch: { favorite?: boolean; mastery?: ReviewMastery; note?: string | null },
  ) => {
    const current = progressMap[recordId]
    const optimistic = {
      record_id: recordId,
      favorite: patch.favorite ?? current?.favorite ?? false,
      mastery: patch.mastery ?? current?.mastery ?? 'new',
      note: patch.note ?? current?.note ?? null,
      last_reviewed_at: current?.last_reviewed_at ?? null,
      updated_at: current?.updated_at ?? null,
    } as ReviewProgress
    setProgressMap((prev) => ({ ...prev, [recordId]: optimistic }))
    try {
      const saved = await reviewApi.updateProgress(recordId, patch)
      setProgressMap((prev) => ({ ...prev, [recordId]: saved }))
      message.success('复习状态已保存')
    } catch (e: unknown) {
      if (current) setProgressMap((prev) => ({ ...prev, [recordId]: current }))
      message.error((e as Error).message || '保存复习状态失败')
    }
  }

  const loadAiReview = async (refresh = false) => {
    if (!selectedRecord) return
    if (!getAdminToken()) {
      message.warning('AI 复盘目前仅对管理员开放，请先登录后台')
      return
    }
    try {
      setAiLoading(true)
      const data = await reviewApi.aiReview(selectedRecord.id, refresh)
      setAiReview(data)
      setDetailTab('ai')
      message.success(data.cached ? '已加载缓存复盘' : 'AI 复盘已生成')
    } catch (e: unknown) {
      message.error((e as Error).message || 'AI 复盘生成失败')
    } finally {
      setAiLoading(false)
    }
  }

  useEffect(() => {
    logApi
      .filters()
      .then((data) => setFilterOptions(data || { posts: [], companies: [] }))
      .catch(() => message.warning('筛选项加载失败，可继续查看已有数据'))
  }, [])

  useEffect(() => {
    fetchRecords(1)
  }, [postFilter, companyFilter])

  useEffect(() => {
    if (!companyFilter || !postFilter) {
      setOverview(null)
      return
    }
    setOverviewLoading(true)
    reviewApi
      .overview({ company: companyFilter, post: postFilter, days: overviewDays, limit: 80 })
      .then(setOverview)
      .catch(() => setOverview(null))
      .finally(() => setOverviewLoading(false))
  }, [companyFilter, postFilter, overviewDays])

  useEffect(() => {
    const next = new URLSearchParams(searchParams)
    if (postFilter) next.set('post', postFilter)
    else next.delete('post')
    if (companyFilter) next.set('company', companyFilter)
    else next.delete('company')
    setSearchParams(next, { replace: true })
  }, [postFilter, companyFilter])

  const renderOverview = () => {
    if (!companyFilter || !postFilter) {
      return (
        <Card className="interview-insight-card">
          <div className="insight-empty">
            <BarChartOutlined />
            <div>
              <h3>选择一个岗位方向，生成公司面试看板</h3>
              <p>看板会统计样本数、高频问题和知识点分布，适合面试前快速判断复习重点。</p>
            </div>
          </div>
        </Card>
      )
    }

    if (overviewLoading) {
      return (
        <Card className="interview-insight-card">
          <Empty description="正在分析近期面经..." />
        </Card>
      )
    }

    if (!overview || overview.empty) {
      return (
        <Card className="interview-insight-card">
          <Empty description={`${companyFilter} / ${postFilter} 暂无足够样本`} />
        </Card>
      )
    }

    return (
      <Card className="interview-insight-card">
        <div className="insight-header">
          <div>
            <Text type="secondary">Interview Radar</Text>
            <h2>{companyFilter} / {postFilter} 高频面试看板</h2>
          </div>
          <Select
            value={overviewDays}
            onChange={setOverviewDays}
            options={[
              { label: '近 7 天', value: 7 },
              { label: '近 30 天', value: 30 },
              { label: '近 90 天', value: 90 },
            ]}
            style={{ width: 120 }}
          />
        </div>
        <div className="insight-metrics">
          <div>
            <strong>{overview.record_count}</strong>
            <span>分析面经</span>
          </div>
          <div>
            <strong>{overview.question_count}</strong>
            <span>提取问题</span>
          </div>
          <div>
            <strong>{overview.categories.length}</strong>
            <span>知识分类</span>
          </div>
        </div>
        <Row gutter={[14, 14]}>
          <Col xs={24} lg={15}>
            <div className="insight-panel">
              <h3><FireOutlined /> 高频问题 Top</h3>
              <div className="top-question-list">
                {overview.top_questions.slice(0, 8).map((item, index) => (
                  <div key={`${item.question}-${index}`} className="top-question-item">
                    <span>{index + 1}</span>
                    <p>{item.question}</p>
                    <Tag color={index < 3 ? 'red' : 'blue'}>{item.count} 次</Tag>
                  </div>
                ))}
              </div>
            </div>
          </Col>
          <Col xs={24} lg={9}>
            <div className="insight-panel">
              <h3><BarChartOutlined /> 知识点分布</h3>
              <div className="category-list">
                {overview.categories.map((item) => (
                  <div key={item.name}>
                    <span>{item.name}</span>
                    <b>{item.count}</b>
                  </div>
                ))}
              </div>
            </div>
          </Col>
        </Row>
      </Card>
    )
  }

  return (
    <div className="public-page interview-page">
      <header className="public-nav">
        <button className="public-brand" onClick={() => navigate('/')}>
          <img src="/offerlens.svg" alt="OfferLens" />
          <strong>OfferLens</strong>
        </button>
        <nav>
          <Button type="text" icon={<HomeOutlined />} onClick={() => navigate('/')}>首页</Button>
          <Button type="primary" onClick={() => navigate('/admin')}>后台入口</Button>
        </nav>
      </header>

      <main>
        <section className="interview-hero">
          <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate('/')}>返回首页</Button>
          <Title>面试情报库</Title>
          <Paragraph>
            默认优先展示热门大厂面经。你也可以按公司和岗位方向快速筛选真实面经，
            适合面试前扫高频问题，也适合整理成自己的 Markdown 笔记。
          </Paragraph>
        </section>

        <Card className="public-filter-card">
          <div className="hot-company-strip">
            {hotInterviewCompanies.map((company) => {
              const companyValue = company.searchName || company.name
              return (
              <button
                key={company.name}
                className={companyFilter === companyValue ? 'active' : ''}
                onClick={() => setCompanyFilter(companyValue)}
              >
                <img src={company.logo} alt={`${company.name} logo`} loading="lazy" decoding="async" />
                <span>{company.name}</span>
              </button>
              )
            })}
            <button className={!companyFilter ? 'active muted' : 'muted'} onClick={() => setCompanyFilter('')}>
              <span>全部公司</span>
            </button>
          </div>

          <Row gutter={[12, 12]} align="middle">
            <Col xs={24} md={7}>
              <Select value={postFilter} onChange={setPostFilter} options={postOptions} style={{ width: '100%' }} showSearch optionFilterProp="label" />
            </Col>
            <Col xs={24} md={7}>
              <Select value={companyFilter} onChange={setCompanyFilter} options={companyOptions} style={{ width: '100%' }} showSearch optionFilterProp="label" />
            </Col>
            <Col xs={24} md={7}>
              <Input prefix={<SearchOutlined />} value={keyword} onChange={(e) => setKeyword(e.target.value)} placeholder="搜索标题、公司、正文关键词" />
            </Col>
            <Col xs={24} md={3}>
              <Button block type="primary" loading={loading} onClick={() => fetchRecords(1)}>刷新</Button>
            </Col>
          </Row>
        </Card>

        {renderOverview()}

        {visibleRecords.length > 0 ? (
          <Row gutter={[16, 16]} className="interview-grid">
            {visibleRecords.map((record) => {
              const progress = progressMap[record.id]
              const meta = masteryMeta(progress?.mastery)
              return (
                <Col xs={24} md={12} xl={8} key={record.id}>
                  <Card className="interview-card" hoverable onClick={() => openDetail(record)}>
                    <div className="interview-card-top">
                      <Space size={8} wrap>
                        <Tag color="blue">{record.company || '未知公司'}</Tag>
                        <Tag>{record.post}</Tag>
                        <Tag color={meta.color}>{meta.label}</Tag>
                      </Space>
                      <Button
                        type="text"
                        className={progress?.favorite ? 'favorite-button active' : 'favorite-button'}
                        icon={progress?.favorite ? <StarFilled /> : <StarOutlined />}
                        onClick={(event) => {
                          event.stopPropagation()
                          updateRecordProgress(record.id, { favorite: !progress?.favorite })
                        }}
                      />
                    </div>
                    <h3>{record.title}</h3>
                    <Paragraph ellipsis={{ rows: 3 }}>{record.content || '暂无正文摘要'}</Paragraph>
                    <div className="interview-card-actions" onClick={(event) => event.stopPropagation()}>
                      <Select
                        size="small"
                        value={progress?.mastery || 'new'}
                        options={masteryOptions.map((item) => ({ label: item.label, value: item.value }))}
                        onChange={(value) => updateRecordProgress(record.id, { mastery: value })}
                        style={{ width: 96 }}
                      />
                      <Button type="link" size="small" onClick={() => openDetail(record)}>查看详情</Button>
                    </div>
                    <div className="interview-card-footer">
                      <Text type="secondary">{formatDisplayTime(record.edit_time)}</Text>
                    </div>
                  </Card>
                </Col>
              )
            })}
          </Row>
        ) : (
          <Card className="surface-card">
            <Empty description={loading ? '加载中...' : '暂无匹配面经'} />
          </Card>
        )}

        <div className="public-pagination">
          <Pagination
            current={pagination.current}
            pageSize={pagination.pageSize}
            total={pagination.total}
            showSizeChanger={false}
            onChange={(page) => fetchRecords(page, pagination.pageSize)}
          />
        </div>
      </main>

      <Drawer
        title={null}
        open={drawerOpen}
        width={Math.min(window.innerWidth - 24, 980)}
        onClose={() => setDrawerOpen(false)}
        loading={detailLoading}
        className="interview-detail-drawer"
        extra={null}
      >
        {selectedRecord && (
          <div className="interview-detail">
            <div className="detail-hero-card">
              <Space size={8} wrap>
                <Tag color="blue">{selectedRecord.company || '未知公司'}</Tag>
                <Tag>{selectedRecord.post}</Tag>
                <Tag color="default">{formatDisplayTime(selectedRecord.edit_time)}</Tag>
              </Space>
              <h2>{selectedRecord.title}</h2>
              <p>
                这篇面经已整理为原文、Markdown 复盘和复习卡片三个视图。建议先看原文语境，
                再切到卡片梳理高频问题。
              </p>
              <Space wrap>
                {selectedRecord.content_id && (
                  <Button href={getNowcoderUrl(selectedRecord)} target="_blank">
                    查看牛客原文
                  </Button>
                )}
                <Button
                  icon={selectedProgress?.favorite ? <StarFilled /> : <StarOutlined />}
                  onClick={() => updateRecordProgress(selectedRecord.id, { favorite: !selectedProgress?.favorite })}
                >
                  {selectedProgress?.favorite ? '已收藏' : '收藏'}
                </Button>
                <Select
                  value={selectedProgress?.mastery || 'new'}
                  options={masteryOptions.map((item) => ({ label: item.label, value: item.value }))}
                  onChange={(value) => updateRecordProgress(selectedRecord.id, { mastery: value })}
                  style={{ width: 112 }}
                />
                <Button icon={<CopyOutlined />} onClick={copyMarkdown}>
                  复制 Markdown
                </Button>
                <Button type="primary" onClick={() => setDetailTab('cards')}>
                  查看复习卡片
                </Button>
                <Button type="primary" ghost icon={<RobotOutlined />} loading={aiLoading} onClick={() => loadAiReview(false)}>
                  AI 复盘
                </Button>
              </Space>
            </div>

            <Tabs
              activeKey={detailTab}
              onChange={setDetailTab}
              items={[
                {
                  key: 'raw',
                  label: '原文内容',
                  children: (
                    <div className="detail-reading-card raw">
                      <Paragraph>
                        {selectedRecord.content || '暂无内容'}
                      </Paragraph>
                    </div>
                  ),
                },
                {
                  key: 'markdown',
                  label: 'Markdown 复盘',
                  children: (
                    <div className="detail-reading-card markdown-body markdown-review-body">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{selectedMarkdown}</ReactMarkdown>
                    </div>
                  ),
                },
                {
                  key: 'cards',
                  label: '复习卡片',
                  children: (
                    <div className="review-card-grid">
                      {reviewCards.length > 0 ? reviewCards.map((card, index) => (
                        <div className="review-mini-card" key={`${card.title}-${index}`}>
                          <div>
                            <span>{String(index + 1).padStart(2, '0')}</span>
                            <Tag color={index < 3 ? 'red' : 'blue'}>{card.tag}</Tag>
                          </div>
                          <h3>{card.title}</h3>
                          <p>建议补充：核心概念、30 秒答法、常见追问、项目落地点。</p>
                        </div>
                      )) : <Empty description="暂无可提取的复习卡片" />}
                    </div>
                  ),
                },
                {
                  key: 'ai',
                  label: 'AI 复盘',
                  children: (
                    <div className="detail-reading-card ai-review-body">
                      {!aiReview ? (
                        <div className="ai-review-empty">
                          <RobotOutlined />
                          <h3>让 AI 帮你把这篇面经变成复习清单</h3>
                          <p>会生成考察特点、30 秒回答思路、追问方向和行动计划。首次生成可能需要一点时间。</p>
                          <Space>
                            <Button type="primary" icon={<RobotOutlined />} loading={aiLoading} onClick={() => loadAiReview(false)}>
                              生成 AI 复盘
                            </Button>
                            <Button loading={aiLoading} onClick={() => loadAiReview(true)}>
                              重新生成
                            </Button>
                          </Space>
                        </div>
                      ) : (
                        <div className="ai-review-content">
                          <Alert
                            type="info"
                            showIcon
                            message={`${aiReview.review.difficulty} · 优先级 ${aiReview.review.priority}`}
                            description={aiReview.review.summary}
                          />
                          <div className="ai-review-section">
                            <h3>高频问题与 30 秒答法</h3>
                            {aiReview.review.questions.map((item, index) => (
                              <div className="ai-question-card" key={`${item.question}-${index}`}>
                                <div>
                                  <span>{String(index + 1).padStart(2, '0')}</span>
                                  <h4>{item.question}</h4>
                                </div>
                                <p>{item.answer}</p>
                                {!!item.tags?.length && (
                                  <Space size={6} wrap>
                                    {item.tags.map((tag) => <Tag key={tag}>{tag}</Tag>)}
                                  </Space>
                                )}
                                {!!item.followups?.length && (
                                  <ul>
                                    {item.followups.map((followup) => <li key={followup}>{followup}</li>)}
                                  </ul>
                                )}
                              </div>
                            ))}
                          </div>
                          <Row gutter={[14, 14]}>
                            <Col xs={24} lg={12}>
                              <div className="ai-review-section compact">
                                <h3>知识点补齐</h3>
                                {aiReview.review.knowledge_points.map((item) => (
                                  <div className="knowledge-item" key={item.name}>
                                    <b>{item.name}</b>
                                    <p>{item.why}</p>
                                    <small>{item.review_tip}</small>
                                  </div>
                                ))}
                              </div>
                            </Col>
                            <Col xs={24} lg={12}>
                              <div className="ai-review-section compact">
                                <h3>复习行动</h3>
                                <ol>
                                  {aiReview.review.action_plan.map((item) => <li key={item}>{item}</li>)}
                                </ol>
                                <Button loading={aiLoading} onClick={() => loadAiReview(true)}>
                                  重新生成复盘
                                </Button>
                              </div>
                            </Col>
                          </Row>
                        </div>
                      )}
                    </div>
                  ),
                },
              ]}
            />
          </div>
        )}
      </Drawer>
    </div>
  )
}

export default PublicInterviews
