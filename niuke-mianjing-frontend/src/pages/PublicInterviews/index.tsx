import React, { useEffect, useMemo, useRef, useState } from 'react'
import { Button, Card, Col, Empty, Input, message, Pagination, Row, Select, Space, Tag, Typography } from 'antd'
import {
  ArrowLeftOutlined,
  HomeOutlined,
  SearchOutlined,
  StarFilled,
  StarOutlined,
} from '@ant-design/icons'
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { logApi, reviewApi } from '@/api'
import type { NiukeRecord, ReviewMastery, ReviewProgress } from '@/api/types'
import { useFilterOptions } from '@/hooks/useFilterOptions'
import { useRecords } from '@/hooks/useRecords'
import { useErrorMessage } from '@/hooks/useErrorMessage'
import { hotInterviewCompanies } from '@/constants/companies'
import { formatDisplayTime } from '@/utils/datetime'
import { buildRecordMarkdown } from '@/utils/markdown'
import { extractReviewCards, filterRecordsByKeyword } from './interviewUtils'
import ReviewOverviewCard from './ReviewOverviewCard'
import InterviewDetailDrawer from './InterviewDetailDrawer'
import UserSessionButton from '@/components/UserSessionButton'
import { getUserToken, isAnonymousPageAllowed, userLoginPath } from '@/utils/auth'

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

const PublicInterviews: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams, setSearchParams] = useSearchParams()
  const initialPost = searchParams.get('post') || ''
  const initialCompany = searchParams.get('company') || defaultCompany
  const [selectedRecord, setSelectedRecord] = useState<NiukeRecord | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [detailTab, setDetailTab] = useState('raw')
  const [detailLoading, setDetailLoading] = useState(false)
  const [postFilter, setPostFilter] = useState(initialPost)
  const [companyFilter, setCompanyFilter] = useState(initialCompany)
  const [keyword, setKeyword] = useState('')
  const [progressMap, setProgressMap] = useState<Record<number, ReviewProgress>>({})
  const [analysisIds, setAnalysisIds] = useState<number[]>([])
  const openedRecordIdRef = useRef<number | null>(null)

  const errMsg = useErrorMessage()
  const { postOptions, companyOptions } = useFilterOptions()
  const { records, loading, pagination, reload: fetchRecords } = useRecords(postFilter, companyFilter, {
    paged: true,
    pageSize: PAGE_SIZE,
    errorMessage: '获取面经失败',
  })

  const selectedMarkdown = useMemo(
    () => (selectedRecord ? buildRecordMarkdown(selectedRecord) : ''),
    [selectedRecord],
  )

  const reviewCards = useMemo(() => extractReviewCards(selectedRecord), [selectedRecord])

  const selectedProgress = selectedRecord ? progressMap[selectedRecord.id] : null

  const visibleRecords = useMemo(() => {
    return filterRecordsByKeyword(records, keyword)
  }, [keyword, records])

  useEffect(() => {
    fetchRecords(1)
  }, [fetchRecords])

  useEffect(() => {
    if (records.length === 0 || !getUserToken()) return
    const ids = records.map((record) => record.id)
    reviewApi
      .progress(ids)
      .then((progressRows) => {
        setProgressMap((prev) => ({
          ...prev,
          ...Object.fromEntries((progressRows || []).map((item) => [item.record_id, item])),
        }))
      })
      .catch(() => undefined)
  }, [records])

  const openDetail = async (record: NiukeRecord) => {
    setDrawerOpen(true)
    setDetailTab('raw')
    setSelectedRecord(record)
    try {
      setDetailLoading(true)
      const detail = await logApi.record(record.id)
      setSelectedRecord(detail)
    } catch (e: unknown) {
      errMsg(e, '获取详情失败')
    } finally {
      setDetailLoading(false)
    }
  }

  const openRecordById = async (recordId: number) => {
    setDrawerOpen(true)
    setDetailTab('raw')
    try {
      setDetailLoading(true)
      const detail = await logApi.record(recordId)
      setSelectedRecord(detail)
    } catch (e: unknown) {
      openedRecordIdRef.current = null
      errMsg(e, '获取详情失败')
    } finally {
      setDetailLoading(false)
    }
  }

  const closeDetail = () => {
    setDrawerOpen(false)
    const next = new URLSearchParams(searchParams)
    if (next.has('record')) {
      next.delete('record')
      setSearchParams(next, { replace: true })
      openedRecordIdRef.current = null
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
    if (!getUserToken()) {
      message.info('登录后可以收藏和保存复习进度')
      navigate(userLoginPath(`${location.pathname}${location.search}`))
      return
    }
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
      errMsg(e, '保存复习状态失败')
    }
  }

  useEffect(() => {
    const next = new URLSearchParams(searchParams)
    if (postFilter) next.set('post', postFilter)
    else next.delete('post')
    if (companyFilter) next.set('company', companyFilter)
    else next.delete('company')
    setSearchParams(next, { replace: true })
  }, [postFilter, companyFilter])

  useEffect(() => {
    const recordId = Number(searchParams.get('record'))
    if (!Number.isInteger(recordId) || recordId <= 0 || openedRecordIdRef.current === recordId) return
    openedRecordIdRef.current = recordId
    void openRecordById(recordId)
  }, [searchParams])

  useEffect(() => {
    setAnalysisIds(records.slice(0, 4).map((record) => record.id))
  }, [records])

  const toggleAnalysisRecord = (recordId: number, checked: boolean) => {
    setAnalysisIds((prev) => checked ? Array.from(new Set([...prev, recordId])) : prev.filter((id) => id !== recordId))
  }

  const toggleAllAnalysisRecords = () => {
    const ids = visibleRecords.slice(0, 8).map((record) => record.id)
    const allSelected = ids.length > 0 && ids.every((id) => analysisIds.includes(id))
    setAnalysisIds(allSelected ? [] : ids)
  }

  const companySourceMap: Record<string, string> = {
    腾讯: 'tencent',
    阿里巴巴: 'alibaba',
    京东: 'jd',
    美团: 'meituan',
    百度: 'baidu',
    字节跳动: 'bytedance',
    华为: 'huawei',
    快手: 'kuaishou',
  }
  const postTrackMap: Record<string, string> = {
    后端开发: 'backend',
    前端开发: 'frontend',
    客户端开发: 'client',
    测试: 'testing',
    数据开发: 'data',
    '人工智能/算法': 'ai',
  }

  const openAiAnalysis = () => {
    if (!analysisIds.length) {
      message.warning('请至少选择 1 篇面经')
      return
    }
    const source = companySourceMap[companyFilter] || 'tencent'
    const track = postTrackMap[postFilter] || 'backend'
    const params = new URLSearchParams({
      report: 'job_interviews',
      ids: analysisIds.slice(0, 8).join(','),
      source,
      track,
      type: source === 'alibaba' ? 'intern' : 'campus',
    })
    navigate(`/ai-analysis/create?${params.toString()}`)
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
          <Button type="text" onClick={() => navigate('/jobs')}>职位雷达</Button>
          <Button type="text" onClick={() => navigate('/ai-analysis')}>AI 分析</Button>
          <Button type="primary" onClick={() => navigate('/admin')}>后台入口</Button>
          <UserSessionButton />
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

          <div className="post-filter-strip">
            {postOptions.map((option) => {
              const value = String(option.value ?? '')
              return (
                <button key={value || 'all'} className={postFilter === value ? 'active' : ''} onClick={() => setPostFilter(value)}>
                  {option.label}
                </button>
              )
            })}
          </div>

          <Row gutter={[12, 12]} align="middle">
            <Col xs={24} md={8}>
              <Select value={companyFilter} onChange={setCompanyFilter} options={companyOptions} style={{ width: '100%' }} showSearch optionFilterProp="label" />
            </Col>
            <Col xs={24} md={11}>
              <Input prefix={<SearchOutlined />} value={keyword} onChange={(e) => setKeyword(e.target.value)} placeholder="搜索标题、公司、正文关键词" />
            </Col>
            <Col xs={24} md={5}>
              <Button block type="primary" loading={loading} onClick={() => fetchRecords(1)}>刷新</Button>
            </Col>
          </Row>
        </Card>

        <ReviewOverviewCard
          companyFilter={companyFilter}
          postFilter={postFilter}
          records={visibleRecords}
          selectedIds={analysisIds}
          onToggle={toggleAnalysisRecord}
          onToggleAll={toggleAllAnalysisRecords}
          onAnalyze={openAiAnalysis}
        />

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
            onChange={(page) => {
              if (!isAnonymousPageAllowed(page)) {
                message.info('登录后可以继续浏览更多面经')
                navigate(userLoginPath(`${location.pathname}${location.search}`))
                return
              }
              void fetchRecords(page, pagination.pageSize)
            }}
          />
        </div>
      </main>

      <InterviewDetailDrawer
        open={drawerOpen}
        loading={detailLoading}
        record={selectedRecord}
        selectedProgress={selectedProgress}
        selectedMarkdown={selectedMarkdown}
        reviewCards={reviewCards}
        detailTab={detailTab}
        masteryOptions={masteryOptions}
        onClose={closeDetail}
        onDetailTabChange={setDetailTab}
        onCopyMarkdown={copyMarkdown}
        onUpdateProgress={updateRecordProgress}
      />
    </div>
  )
}

export default PublicInterviews
