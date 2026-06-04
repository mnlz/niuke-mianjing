import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { Alert, Button, Card, Checkbox, Col, Form, Input, InputNumber, message, Row, Select, Space, Tag, Typography, Upload } from 'antd'
import type { UploadProps } from 'antd'
import { BarChartOutlined, DeleteOutlined, DatabaseOutlined, SendOutlined, ThunderboltOutlined, UploadOutlined } from '@ant-design/icons'
import { useLocation } from 'react-router-dom'
import { logApi } from '@/api'
import { wechatApi } from '@/api/wechat'
import type { FilterOptions, NiukeRecord, WeChatArticleData, WeChatQuestionAnalysisData } from '@/api/types'
import { buildRecordMarkdown } from '@/utils/markdown'

const { Text, Title } = Typography
const { TextArea } = Input

type SourceMode = 'single' | 'analysis' | 'manual'
type ContentType =
  | 'single_interpretation'
  | 'knowledge_deep_dive'
  | 'trend_analysis'
  | 'manual_rewrite'
  | 'quick_checklist'
  | 'interviewer_chain'

type CustomCover = {
  base64: string
  mime: string
  name: string
}

const contentTypeOptions: Array<{ label: string; value: ContentType }> = [
  { label: '单篇面经解读', value: 'single_interpretation' },
  { label: '技术知识点精讲', value: 'knowledge_deep_dive' },
  { label: '面试趋势分析', value: 'trend_analysis' },
  { label: '手动粘贴', value: 'manual_rewrite' },
  { label: '高频题速查清单', value: 'quick_checklist' },
  { label: '面试官追问链路', value: 'interviewer_chain' },
]

const contentTypeGuides: Record<ContentType, { title: string; text: string; button: string }> = {
  single_interpretation: {
    title: '单篇面经解读',
    text: '围绕一篇真实面经，拆解面试过程、问题难度、考点和复习建议。少用表格，更像一篇完整解读文章。',
    button: '生成单篇解读',
  },
  knowledge_deep_dive: {
    title: '技术知识点精讲',
    text: '从一篇面经里挑 3-5 个重要知识点，展开讲原理、面试问法、答题模板和常见追问。',
    button: '生成知识点精讲',
  },
  trend_analysis: {
    title: '面试趋势分析',
    text: '按公司、岗位和时间范围分析多篇面经，输出高频题、趋势观察和备考优先级。这个类型可以使用榜单表格。',
    button: '分析趋势并生成',
  },
  manual_rewrite: {
    title: '手动粘贴',
    text: '自由粘贴 Markdown 或草稿，由 AI 改写成公众号文章。适合临时素材和外部整理内容。',
    button: '按粘贴内容生成',
  },
  quick_checklist: {
    title: '高频题速查清单',
    text: '按公司和岗位抽取多篇真实面经，整理成适合收藏的速查清单：题目、30 秒答法、易错点、复习优先级。尽量不用大表格。',
    button: '生成速查清单',
  },
  interviewer_chain: {
    title: '面试官追问链路',
    text: '从核心问题出发，还原面试官可能怎么追问、候选人怎么接、哪些回答容易被继续深挖。',
    button: '生成追问链路',
  },
}

const getSourceMode = (contentType: ContentType): SourceMode => {
  if (contentType === 'trend_analysis' || contentType === 'quick_checklist') return 'analysis'
  if (contentType === 'manual_rewrite') return 'manual'
  return 'single'
}

const analysisRangeOptions = [
  { label: '最近 7 天', value: 7 },
  { label: '最近 30 天', value: 30 },
  { label: '最近 90 天', value: 90 },
]

const defaultMarkdown = '# 面经标题\n\n请选择一条面经，或在这里粘贴 Markdown 内容。'

const readImageAsCover = (file: File): Promise<CustomCover> =>
  new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const value = String(reader.result || '')
      const match = value.match(/^data:(image\/[^;]+);base64,(.+)$/)
      if (!match) {
        reject(new Error('封面图片读取失败'))
        return
      }
      resolve({ mime: match[1], base64: match[2], name: file.name })
    }
    reader.onerror = () => reject(new Error('封面图片读取失败'))
    reader.readAsDataURL(file)
  })

const parseSseChunk = (buffer: string) => {
  const events: Array<Record<string, unknown>> = []
  const parts = buffer.split('\n\n')
  const rest = parts.pop() || ''
  parts.forEach((part) => {
    const line = part
      .split('\n')
      .find((item) => item.startsWith('data:'))
      ?.slice(5)
      .trim()
    if (!line) return
    try {
      events.push(JSON.parse(line))
    } catch {
      // ignore malformed event
    }
  })
  return { events, rest }
}

const Wechat: React.FC = () => {
  const location = useLocation()
  const state = location.state as { markdown?: string; recordId?: number } | null
  const [form] = Form.useForm()
  const selectedContentType = (Form.useWatch('style', form) || 'single_interpretation') as ContentType
  const sourceMode = getSourceMode(selectedContentType)
  const [records, setRecords] = useState<NiukeRecord[]>([])
  const [selectedId, setSelectedId] = useState<number | undefined>(state?.recordId)
  const [selectedRecord, setSelectedRecord] = useState<NiukeRecord | null>(null)
  const [markdown, setMarkdown] = useState(state?.markdown || defaultMarkdown)
  const [html, setHtml] = useState('')
  const [previewHtml, setPreviewHtml] = useState('')
  const [customCover, setCustomCover] = useState<CustomCover | null>(null)
  const [streaming, setStreaming] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [htmlCollapsed, setHtmlCollapsed] = useState(false)
  const [saving, setSaving] = useState(false)
  const [publishing, setPublishing] = useState(false)
  const [recordLoading, setRecordLoading] = useState(false)
  const [postFilter, setPostFilter] = useState('')
  const [companyFilter, setCompanyFilter] = useState('')
  const [analysisDays, setAnalysisDays] = useState(30)
  const [checklistLimit, setChecklistLimit] = useState(10)
  const [checklistOrderByTime, setChecklistOrderByTime] = useState(false)
  const [checklistDays, setChecklistDays] = useState(30)
  const [analysisData, setAnalysisData] = useState<WeChatQuestionAnalysisData | null>(null)
  const [filterOptions, setFilterOptions] = useState<FilterOptions>({ posts: [], companies: [] })
  const [article, setArticle] = useState<WeChatArticleData | null>(null)

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

  const activeTypeGuide = contentTypeGuides[selectedContentType] || contentTypeGuides.single_interpretation

  const loadRecords = useCallback(async () => {
    try {
      setRecordLoading(true)
      const data = await logApi.records({
        post: postFilter || undefined,
        company: companyFilter || undefined,
        limit: 100,
        offset: 0,
      })
      setRecords(data?.data || [])
    } catch {
      message.warning('面经列表加载失败，可以手动粘贴 Markdown')
    } finally {
      setRecordLoading(false)
    }
  }, [companyFilter, postFilter])

  useEffect(() => {
    form.setFieldsValue({
      title: '面经拆解：高频问题与复习提示',
      author: '萌钠粒鲨',
      style: state?.markdown && !state?.recordId ? 'manual_rewrite' : 'single_interpretation',
    })
    logApi
      .filters()
      .then((data) => setFilterOptions(data || { posts: [], companies: [] }))
      .catch(() => message.warning('筛选项加载失败，可继续手动编辑 Markdown'))
  }, [form])

  useEffect(() => {
    loadRecords()
  }, [loadRecords])

  useEffect(() => {
    if (!selectedId) return
    logApi
      .record(selectedId)
      .then((record) => {
        const md = buildRecordMarkdown(record)
        setSelectedRecord(record)
        setMarkdown(md)
        setHtml('')
        setPreviewHtml('')
        setCustomCover(null)
        setAnalysisData(null)
        setArticle(null)
        const currentType = form.getFieldValue('style') as ContentType
        const nextType = getSourceMode(currentType) === 'single' ? currentType : 'single_interpretation'
        form.setFieldsValue({
          title: record.title,
          author: form.getFieldValue('author') || '萌钠粒鲨',
          digest: `${record.company || '大厂'} ${record.post} 面经拆解，整理高频问题、简答关键词和复习提醒。`,
          style: nextType,
        })
      })
      .catch((e: unknown) => message.error((e as Error).message || '加载面经详情失败'))
  }, [form, selectedId])

  const handleStreamEvents = async (response: Response, successText: string) => {
    if (!response.ok || !response.body) {
      throw new Error(`生成失败：HTTP ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''
    let liveHtml = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const parsed = parseSseChunk(buffer)
      buffer = parsed.rest
      parsed.events.forEach((event) => {
        if (event.type === 'analysis') {
          const data = event as unknown as WeChatQuestionAnalysisData & { type: string }
          setAnalysisData(data)
          setMarkdown('')
          form.setFieldsValue({
            title: data.title,
            digest: data.digest,
            author: form.getFieldValue('author') || '萌钠粒鲨',
            style: 'trend_analysis',
          })
        }
        if (event.type === 'meta' && event.title) {
          form.setFieldValue('title', event.title)
        }
        if (event.type === 'delta') {
          liveHtml += String(event.delta || '')
          setHtml(liveHtml)
        }
        if (event.type === 'done') {
          liveHtml = String(event.html || liveHtml)
          setHtml(liveHtml)
          setPreviewHtml(liveHtml)
          if (event.title) form.setFieldValue('title', event.title)
        }
        if (event.type === 'error') {
          throw new Error(String(event.message || 'AI 生成失败'))
        }
      })
    }
    message.success(successText)
  }

  const streamGenerate = async () => {
    try {
      const values = await form.validateFields()
      setStreaming(true)
      setHtmlCollapsed(false)
      setHtml('')
      setPreviewHtml('')
      setArticle(null)
      setAnalysisData(null)

      if (!markdown.trim() || markdown.trim() === defaultMarkdown.trim()) {
        message.warning(sourceMode === 'single' ? '请先选择一条面经' : '请先粘贴 Markdown 内容')
        setStreaming(false)
        return
      }

      const response = await fetch('/api/wechat/ai-stream', {
        method: 'POST',
        headers: {
          Accept: 'text/event-stream',
          'Content-Type': 'application/json; charset=utf-8',
        },
        body: JSON.stringify({
          markdown,
          title: values.title,
          author: values.author,
          digest: values.digest,
          source_record_id: selectedRecord?.id,
          style: values.style,
        }),
      })
      await handleStreamEvents(response, 'AI 正文生成完成，可以继续编辑后保存')
    } catch (e: unknown) {
      if (e instanceof Error) message.error(e.message || 'AI 生成失败')
    } finally {
      setStreaming(false)
    }
  }

  const streamQuestionAnalysis = async () => {
    if (!companyFilter || !postFilter) {
      message.warning('请先选择公司和岗位方向')
      return
    }
    try {
      setAnalyzing(true)
      setStreaming(true)
      setHtmlCollapsed(false)
      setHtml('')
      setPreviewHtml('')
      setArticle(null)
      setSelectedId(undefined)
      setSelectedRecord(null)
      setCustomCover(null)
      setMarkdown('')
      form.setFieldValue('style', 'trend_analysis')

      const response = await fetch('/api/wechat/question-analysis-stream', {
        method: 'POST',
        headers: {
          Accept: 'text/event-stream',
          'Content-Type': 'application/json; charset=utf-8',
        },
        body: JSON.stringify({
          company: companyFilter,
          post: postFilter,
          days: analysisDays,
          limit: 200,
        }),
      })
      await handleStreamEvents(response, 'AI 已完成高频题分析和公众号正文生成')
    } catch (e: unknown) {
      if (e instanceof Error) message.error(e.message || 'AI 分析生成失败')
    } finally {
      setAnalyzing(false)
      setStreaming(false)
    }
  }

  const streamQuickChecklist = async () => {
    if (!companyFilter || !postFilter) {
      message.warning('请先选择公司和岗位方向')
      return
    }
    try {
      setAnalyzing(true)
      setStreaming(true)
      setHtmlCollapsed(false)
      setHtml('')
      setPreviewHtml('')
      setArticle(null)
      setSelectedId(undefined)
      setSelectedRecord(null)
      setCustomCover(null)
      setMarkdown('')
      form.setFieldValue('style', 'quick_checklist')

      const response = await fetch('/api/wechat/quick-checklist-stream', {
        method: 'POST',
        headers: {
          Accept: 'text/event-stream',
          'Content-Type': 'application/json; charset=utf-8',
        },
        body: JSON.stringify({
          company: companyFilter,
          post: postFilter,
          limit: checklistLimit,
          order_by_time: checklistOrderByTime,
          days: checklistOrderByTime ? checklistDays : undefined,
        }),
      })
      await handleStreamEvents(response, 'AI 已完成高频题速查清单生成')
    } catch (e: unknown) {
      if (e instanceof Error) message.error(e.message || 'AI 速查清单生成失败')
    } finally {
      setAnalyzing(false)
      setStreaming(false)
    }
  }

  const streamMultiRecordArticle = () => {
    if (selectedContentType === 'quick_checklist') {
      return streamQuickChecklist()
    }
    return streamQuestionAnalysis()
  }

  const saveArticle = async () => {
    try {
      const values = await form.validateFields()
      if (!html.trim()) {
        message.warning('请先生成或填写公众号 HTML')
        return
      }
      setSaving(true)
      const sourceMarkdown = markdown || (analysisData ? JSON.stringify({ stats: analysisData.stats, records: analysisData.records }, null, 2) : '')
      const saved = await wechatApi.saveGenerated({
        markdown: sourceMarkdown,
        html,
        title: values.title,
        author: values.author,
        digest: values.digest,
        source_record_id: selectedRecord?.id,
        style: values.style,
        cover_prompt: values.cover_prompt,
        cover_base64: customCover?.base64,
        cover_mime: customCover?.mime,
      })
      setArticle(saved)
      setHtml(saved.html || html)
      setPreviewHtml(saved.html || html)
      message.success(`已保存稿件 #${saved.id}，${customCover ? '自定义封面已保存' : '封面已生成'}`)
    } catch (e: unknown) {
      if (e instanceof Error) message.error(e.message || '保存失败')
    } finally {
      setSaving(false)
    }
  }

  const publishDraft = async () => {
    if (!article?.id) {
      message.warning('请先保存稿件，再推送草稿箱')
      return
    }
    try {
      setPublishing(true)
      const data = await wechatApi.publishSaved(article.id)
      message.success(`草稿创建成功：${data.media_id}`)
    } catch (e: unknown) {
      if (e instanceof Error) message.error(e.message || '推送草稿失败')
    } finally {
      setPublishing(false)
    }
  }

  const handleCoverUpload: UploadProps['beforeUpload'] = async (file) => {
    if (!file.type.startsWith('image/')) {
      message.warning('请上传图片文件')
      return Upload.LIST_IGNORE
    }
    if (file.size > 2 * 1024 * 1024) {
      message.warning('公众号封面建议小于 2MB')
      return Upload.LIST_IGNORE
    }
    try {
      const cover = await readImageAsCover(file)
      setCustomCover(cover)
      setArticle(null)
      message.success('自定义封面已选择，保存时会写入数据库')
    } catch (e: unknown) {
      message.error((e as Error).message || '读取封面失败')
    }
    return Upload.LIST_IGNORE
  }

  const coverPreview = customCover
    ? {
        title: '自定义封面',
        src: `data:${customCover.mime};base64,${customCover.base64}`,
        hint: customCover.name,
      }
    : article?.cover_base64
      ? {
          title: 'AI 封面',
          src: `data:${article.cover_mime || 'image/png'};base64,${article.cover_base64}`,
          hint: '已保存到数据库',
        }
      : null

  const clearSelectedRecord = () => {
    setSelectedId(undefined)
    setSelectedRecord(null)
    setMarkdown(defaultMarkdown)
    setHtml('')
    setPreviewHtml('')
    setArticle(null)
  }

  return (
    <div>
      <div className="page-title">
        <h2>公众号工坊</h2>
        <p>先选择内容类型，再生成、编辑、保存封面并推送到微信公众号草稿箱。</p>
      </div>

      <Form form={form} layout="vertical">
        <Row gutter={[16, 16]}>
          <Col xs={24} xl={9}>
            <Card title="内容类型" className="surface-card">
              <Space direction="vertical" size={14} style={{ width: '100%' }}>
                <Form.Item name="style" label="选择公众号内容类型" style={{ marginBottom: 0 }}>
                  <Select
                    options={contentTypeOptions}
                    onChange={(value) => {
                    const type = value as ContentType
                    const mode = getSourceMode(type)
                    setAnalysisData(null)
                    setArticle(null)
                    setPreviewHtml('')
                    if (mode === 'manual') {
                      setSelectedId(undefined)
                      setSelectedRecord(null)
                      if (!markdown.trim()) setMarkdown(defaultMarkdown)
                    }
                    if (mode === 'analysis') {
                      setSelectedId(undefined)
                      setSelectedRecord(null)
                      setMarkdown('')
                    }
                    if (mode === 'single' && !selectedRecord && !markdown.trim()) {
                      setMarkdown(defaultMarkdown)
                    }
                  }}
                  />
                </Form.Item>
                <Alert
                  type="info"
                  showIcon
                  message={activeTypeGuide.title}
                  description={activeTypeGuide.text}
                />
              </Space>
            </Card>

            {sourceMode === 'single' && (
              <Card title="选择一篇面经" className="surface-card" style={{ marginTop: 16 }}>
                <Space direction="vertical" size={12} style={{ width: '100%' }}>
                  <Row gutter={12}>
                    <Col xs={24} md={12}>
                      <Text type="secondary">筛选公司</Text>
                      <Select
                        value={companyFilter}
                        onChange={(value) => {
                          setCompanyFilter(value)
                          clearSelectedRecord()
                        }}
                        options={companyOptions}
                        style={{ width: '100%', marginTop: 6 }}
                        showSearch
                        optionFilterProp="label"
                      />
                    </Col>
                    <Col xs={24} md={12}>
                      <Text type="secondary">筛选方向</Text>
                      <Select
                        value={postFilter}
                        onChange={(value) => {
                          setPostFilter(value)
                          clearSelectedRecord()
                        }}
                        options={postOptions}
                        style={{ width: '100%', marginTop: 6 }}
                        showSearch
                        optionFilterProp="label"
                      />
                    </Col>
                  </Row>
                  <Select
                    allowClear
                    showSearch
                    loading={recordLoading}
                    placeholder="选择一条真实面经，生成单篇公众号稿"
                    value={selectedId}
                    optionFilterProp="label"
                    onChange={(value) => {
                      if (value) setSelectedId(value)
                      else clearSelectedRecord()
                    }}
                    options={records.map((record) => ({
                      label: `${record.company || '未知公司'} / ${record.post} / ${record.title}`,
                      value: record.id,
                    }))}
                    style={{ width: '100%' }}
                  />
                  {selectedRecord ? (
                    <Alert
                      type="success"
                      showIcon
                      message={`${selectedRecord.company || '未知公司'} / ${selectedRecord.post}`}
                      description={selectedRecord.title}
                    />
                  ) : (
                    <Alert type="warning" showIcon message="请先选择一条面经，或切换到“手动粘贴”。" />
                  )}
                  <Space wrap>
                    <Button onClick={loadRecords} loading={recordLoading}>
                      刷新列表
                    </Button>
                    <Button
                      type="primary"
                      icon={<ThunderboltOutlined />}
                      loading={streaming && !analyzing && sourceMode === 'single'}
                      onClick={streamGenerate}
                    >
                      {activeTypeGuide.button}
                    </Button>
                  </Space>
                </Space>
              </Card>
            )}

            {sourceMode === 'analysis' && (
              <Card title={selectedContentType === 'quick_checklist' ? '速查清单样本条件' : '趋势分析条件'} className="surface-card" style={{ marginTop: 16 }}>
                <Space direction="vertical" size={12} style={{ width: '100%' }}>
                  <Row gutter={12}>
                    <Col xs={24} md={12}>
                      <Text type="secondary">公司（必填）</Text>
                      <Select
                        value={companyFilter}
                        onChange={setCompanyFilter}
                        options={companyOptions}
                        style={{ width: '100%', marginTop: 6 }}
                        showSearch
                        optionFilterProp="label"
                      />
                    </Col>
                    <Col xs={24} md={12}>
                      <Text type="secondary">岗位方向（必填）</Text>
                      <Select
                        value={postFilter}
                        onChange={setPostFilter}
                        options={postOptions}
                        style={{ width: '100%', marginTop: 6 }}
                        showSearch
                        optionFilterProp="label"
                      />
                    </Col>
                  </Row>
                  {selectedContentType === 'quick_checklist' ? (
                    <>
                      <Row gutter={12}>
                        <Col xs={24} md={12}>
                          <Text type="secondary">面经条数（选填）</Text>
                          <InputNumber
                            min={1}
                            max={50}
                            value={checklistLimit}
                            onChange={(value) => setChecklistLimit(Number(value || 10))}
                            style={{ width: '100%', marginTop: 6 }}
                          />
                        </Col>
                        <Col xs={24} md={12}>
                          <Text type="secondary">抽样方式</Text>
                          <div style={{ marginTop: 10 }}>
                            <Checkbox checked={checklistOrderByTime} onChange={(e) => setChecklistOrderByTime(e.target.checked)}>
                              按时间倒序抽取
                            </Checkbox>
                          </div>
                        </Col>
                      </Row>
                      {checklistOrderByTime && (
                        <div>
                          <Text type="secondary">时间范围</Text>
                          <Select
                            value={checklistDays}
                            onChange={setChecklistDays}
                            options={analysisRangeOptions}
                            style={{ width: '100%', marginTop: 6 }}
                          />
                        </div>
                      )}
                      <Alert
                        type="info"
                        showIcon
                        message={
                          checklistOrderByTime
                            ? `将按时间倒序抽取最近 ${checklistDays} 天内 ${checklistLimit} 条 ${companyFilter || '所选公司'} / ${postFilter || '所选岗位'} 面经。`
                            : `将随机抽取 ${checklistLimit} 条 ${companyFilter || '所选公司'} / ${postFilter || '所选岗位'} 面经。`
                        }
                      />
                    </>
                  ) : (
                    <div>
                      <Text type="secondary">统计范围</Text>
                      <Select
                        value={analysisDays}
                        onChange={setAnalysisDays}
                        options={analysisRangeOptions}
                        style={{ width: '100%', marginTop: 6 }}
                      />
                    </div>
                  )}
                  <Button type="primary" icon={<BarChartOutlined />} loading={analyzing} onClick={streamMultiRecordArticle}>
                    {activeTypeGuide.button}
                  </Button>
                  {analysisData && (
                    <Tag color="blue">
                      样本 {analysisData.stats.record_count} 篇 / 高频题 {analysisData.stats.unique_question_count} 个
                    </Tag>
                  )}
                </Space>
              </Card>
            )}

            {sourceMode === 'manual' && (
              <Card title="手动粘贴 Markdown" className="surface-card" style={{ marginTop: 16 }}>
                <Space direction="vertical" size={12} style={{ width: '100%' }}>
                  <Alert type="info" showIcon message="适合临时粘贴一篇面经、文章草稿或从卡片工坊带来的 Markdown。" />
                  <Button
                    type="primary"
                    icon={<ThunderboltOutlined />}
                    loading={streaming && !analyzing && sourceMode === 'manual'}
                    onClick={streamGenerate}
                  >
                    {activeTypeGuide.button}
                  </Button>
                </Space>
              </Card>
            )}

            <Card title="文章参数" className="surface-card" style={{ marginTop: 16 }}>
              <Row gutter={12}>
                <Col xs={24} md={12}>
                  <Form.Item name="title" label="公众号标题" rules={[{ required: true, message: '请输入标题' }]}>
                    <Input maxLength={64} />
                  </Form.Item>
                </Col>
                <Col xs={24} md={6}>
                  <Form.Item name="author" label="作者">
                    <Input maxLength={12} />
                  </Form.Item>
                </Col>
                <Col xs={24}>
                  <Form.Item name="digest" label="摘要">
                    <TextArea autoSize={{ minRows: 2, maxRows: 3 }} maxLength={120} />
                  </Form.Item>
                </Col>
                <Col xs={24}>
                  <Form.Item name="cover_prompt" label="封面提示词">
                    <TextArea
                      autoSize={{ minRows: 4, maxRows: 8 }}
                      placeholder="选填。可以写封面风格、画面元素、配色，比如：深蓝白底、技术报告风、代码与表格元素、不要文字和水印。"
                    />
                  </Form.Item>
                </Col>
              </Row>
            </Card>

            <Card
              title={analysisData ? '真实面经素材已直接交给 AI' : '原始 Markdown'}
              className="surface-card"
              style={{ marginTop: 16 }}
              extra={analysisData ? <Tag color="geekblue">不使用中间 Markdown</Tag> : null}
            >
              {analysisData ? (
                <Space direction="vertical" size={12} style={{ width: '100%' }}>
                  <Alert
                    type="success"
                    showIcon
                    message={`已将 ${analysisData.stats.record_count} 篇真实面经样本直接交给 AI 分析，未生成中间 Markdown。`}
                  />
                  <div style={{ color: '#64748b', fontSize: 13, lineHeight: 1.9 }}>
                    识别问题：{analysisData.stats.unique_question_count} 个；最高频模块：
                    {analysisData.stats.categories[0]?.name || '暂无'}。
                  </div>
                </Space>
              ) : (
                <TextArea
                  value={markdown}
                  onChange={(e) => {
                    setMarkdown(e.target.value)
                    setPreviewHtml('')
                    setArticle(null)
                  }}
                  autoSize={{ minRows: sourceMode === 'manual' ? 24 : 14, maxRows: 38 }}
                  style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace' }}
                />
              )}
            </Card>
          </Col>

          <Col xs={24} xl={14}>
            <Card
              title="AI 成稿与编辑"
              className="surface-card"
              extra={
                <Space>
                  {streaming ? <Tag color="processing">生成中</Tag> : article ? <Tag color="success">已保存 #{article.id}</Tag> : null}
                  <Button size="small" disabled={!html && !streaming} onClick={() => setHtmlCollapsed((value) => !value)}>
                    {htmlCollapsed ? '展开 HTML' : '折叠 HTML'}
                  </Button>
                </Space>
              }
            >
              <Alert
                type="info"
                showIcon
                style={{ marginBottom: 12 }}
                message="AI 生成的微信 HTML 会先进入编辑区，你可以改标题、改段落、删改观点，再保存封面并推送草稿箱。"
              />
              <Space wrap style={{ marginBottom: 12 }}>
                <Button icon={<DatabaseOutlined />} loading={saving} onClick={saveArticle}>
                  生成封面并保存
                </Button>
                <Button type="primary" icon={<SendOutlined />} loading={publishing} disabled={!article?.id} onClick={publishDraft}>
                  推送草稿箱
                </Button>
              </Space>
              {htmlCollapsed ? (
                <Alert
                  type="success"
                  showIcon
                  message="HTML 编辑区已折叠"
                  description={`当前稿件约 ${html.length.toLocaleString()} 个字符。需要修改正文或样式时，点击右上角“展开 HTML”。`}
                />
              ) : (
                <TextArea
                  value={html}
                  onChange={(e) => {
                    setHtml(e.target.value)
                    if (!streaming) setPreviewHtml(e.target.value)
                    setArticle(null)
                  }}
                  autoSize={{ minRows: 30, maxRows: 46 }}
                  placeholder="点击上方“AI 分析并生成微信稿”后，AI 回复会实时出现在这里；预览会在生成完成后刷新。"
                  style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace' }}
                />
              )}
            </Card>

            <Card title="封面与公众号预览" className="surface-card" style={{ marginTop: 16 }}>
              <Space wrap style={{ marginBottom: 14 }}>
                <Upload accept="image/*" showUploadList={false} beforeUpload={handleCoverUpload}>
                  <Button icon={<UploadOutlined />}>上传自定义封面</Button>
                </Upload>
                {customCover && (
                  <Button icon={<DeleteOutlined />} onClick={() => setCustomCover(null)}>
                    改用 AI 封面
                  </Button>
                )}
              </Space>

              {coverPreview ? (
                <div style={{ marginBottom: 14 }}>
                  <Title level={5} style={{ marginTop: 0 }}>
                    {coverPreview.title}
                  </Title>
                  <img
                    alt="微信公众号封面"
                    src={coverPreview.src}
                    style={{ width: '100%', maxHeight: 260, objectFit: 'cover', borderRadius: 8, border: '1px solid #e5e7eb' }}
                  />
                  <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
                    {coverPreview.hint}
                  </Text>
                </div>
              ) : (
                <Alert
                  type="warning"
                  showIcon
                  style={{ marginBottom: 14 }}
                  message="可以先上传自定义封面；未上传时，保存稿件会调用 AI 生成封面并以 base64 保存到数据库。"
                />
              )}

              {article?.id && (
                <Alert
                  type="success"
                  showIcon
                  style={{ marginBottom: 14 }}
                  message={`数据库稿件 #${article.id}，状态：${article.status}`}
                />
              )}

              <div className="wechat-preview-shell">
                {previewHtml ? (
                  <iframe title="公众号预览" className="wechat-preview-frame" srcDoc={previewHtml} />
                ) : (
                  <div className="wechat-preview-empty">生成完成后，这里会刷新公众号预览</div>
                )}
              </div>
              <Text type="secondary" style={{ display: 'block', marginTop: 10 }}>
                这里只是浏览器预览，最终仍建议在公众号后台草稿箱里手机预览。
              </Text>
            </Card>
          </Col>
        </Row>
      </Form>
    </div>
  )
}

export default Wechat
