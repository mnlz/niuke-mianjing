import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  Alert,
  Button,
  Card,
  Checkbox,
  Col,
  Form,
  Input,
  InputNumber,
  message,
  Row,
  Segmented,
  Select,
  Space,
  Tag,
  Typography,
  Upload,
} from 'antd'
import type { UploadProps } from 'antd'
import {
  BarChartOutlined,
  EyeOutlined,
  FileMarkdownOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import { useLocation } from 'react-router-dom'
import { logApi } from '@/api'
import { wechatApi } from '@/api/wechat'
import type { FilterOptions, NiukeRecord, WeChatArticleData, WeChatQuestionAnalysisData, WeChatThemeGroup } from '@/api/types'
import { buildRecordMarkdown } from '@/utils/markdown'
import {
  analysisRangeOptions,
  contentTypeGuides,
  contentTypeOptions,
  defaultMarkdown,
  getSourceMode,
  type ContentType,
  type GenerateMode,
} from './wechatConfig'
import { parseSseChunk, readImageAsCover, type CustomCover } from './wechatUtils'
import WechatPreviewPane from './WechatPreviewPane'

const { Text } = Typography
const { TextArea } = Input

const Wechat: React.FC = () => {
  const location = useLocation()
  const state = location.state as { markdown?: string; recordId?: number } | null
  const [form] = Form.useForm()
  const selectedContentType = (Form.useWatch('style', form) || 'single_interpretation') as ContentType
  const selectedWechatTheme = (Form.useWatch('wechat_theme', form) || 'auto') as string
  const sourceMode = getSourceMode(selectedContentType)
  const activeTypeGuide = contentTypeGuides[selectedContentType] || contentTypeGuides.single_interpretation

  const [generateMode, setGenerateMode] = useState<GenerateMode>('markdown')
  const [records, setRecords] = useState<NiukeRecord[]>([])
  const [selectedId, setSelectedId] = useState<number | undefined>(state?.recordId)
  const [selectedRecord, setSelectedRecord] = useState<NiukeRecord | null>(null)
  const [sourceMarkdown, setSourceMarkdown] = useState(state?.markdown || defaultMarkdown)
  const [articleMarkdown, setArticleMarkdown] = useState('')
  const [html, setHtml] = useState('')
  const [previewHtml, setPreviewHtml] = useState('')
  const [customCover, setCustomCover] = useState<CustomCover | null>(null)
  const [generatedCover, setGeneratedCover] = useState<CustomCover | null>(null)
  const [streaming, setStreaming] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [previewing, setPreviewing] = useState(false)
  const [coverGenerating, setCoverGenerating] = useState(false)
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
  const [wechatThemeGroups, setWechatThemeGroups] = useState<WeChatThemeGroup[]>([])
  const [article, setArticle] = useState<WeChatArticleData | null>(null)
  const previewRequestId = useRef(0)

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

  const wechatThemeOptions = useMemo(
    () => [
      { label: '自动匹配内容类型', value: 'auto' },
      ...wechatThemeGroups.map((group) => ({
        label: group.label,
        options: group.themes.map((theme) => ({
          label: `${theme.name}（${theme.id}）`,
          value: theme.id,
        })),
      })),
    ],
    [wechatThemeGroups],
  )

  const resetGenerated = () => {
    setArticleMarkdown('')
    setHtml('')
    setPreviewHtml('')
    setArticle(null)
    setAnalysisData(null)
  }

  const clearSelectedRecord = () => {
    setSelectedId(undefined)
    setSelectedRecord(null)
    setSourceMarkdown(defaultMarkdown)
    setCustomCover(null)
    setGeneratedCover(null)
    resetGenerated()
  }

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
      message.warning('面经列表加载失败，可以继续手动粘贴 Markdown')
    } finally {
      setRecordLoading(false)
    }
  }, [companyFilter, postFilter])

  const renderMarkdownPreview = useCallback(
    async (markdownValue: string, silent = true) => {
      if (!markdownValue.trim()) {
        setHtml('')
        setPreviewHtml('')
        return ''
      }
      const requestId = ++previewRequestId.current
      if (!silent) setPreviewing(true)
      try {
        const rendered = await wechatApi.preview({
          markdown: markdownValue,
          title: form.getFieldValue('title') || '未命名文章',
          wechat_theme: selectedWechatTheme,
        })
        if (requestId === previewRequestId.current) {
          setHtml(rendered.html)
          setPreviewHtml(rendered.html)
        }
        return rendered.html
      } finally {
        if (!silent) setPreviewing(false)
      }
    },
    [form, selectedWechatTheme],
  )

  useEffect(() => {
    form.setFieldsValue({
      title: '面经拆解：高频问题与复习提示',
      author: '萌钠粒鲨',
      style: state?.markdown && !state?.recordId ? 'manual_rewrite' : 'single_interpretation',
      wechat_theme: 'auto',
    })
    logApi
      .filters()
      .then((data) => setFilterOptions(data || { posts: [], companies: [] }))
      .catch(() => message.warning('筛选项加载失败，可继续手动编辑 Markdown'))
    wechatApi
      .themes()
      .then((data) => setWechatThemeGroups(data || []))
      .catch(() => message.warning('公众号排版主题加载失败，将使用默认主题'))
  }, [form, state?.markdown, state?.recordId])

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
      setSourceMarkdown(md)
      resetGenerated()
      setCustomCover(null)
      setGeneratedCover(null)
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

  useEffect(() => {
    if (generateMode !== 'markdown' || !articleMarkdown.trim()) return
    const timer = window.setTimeout(() => {
      renderMarkdownPreview(articleMarkdown).catch(() => {
        message.warning('Markdown 预览刷新失败')
      })
    }, 650)
    return () => window.clearTimeout(timer)
  }, [articleMarkdown, generateMode, renderMarkdownPreview])

  const handleStreamEvents = async (response: Response, successText: string, mode: GenerateMode) => {
    if (!response.ok || !response.body) {
      throw new Error(`生成失败：HTTP ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''
    let liveContent = ''

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
          setSourceMarkdown('')
          form.setFieldsValue({
            title: data.title,
            digest: data.digest,
            author: form.getFieldValue('author') || '萌钠粒鲨',
          })
        }
        if (event.type === 'meta' && event.title) {
          form.setFieldValue('title', event.title)
        }
        if (event.type === 'delta') {
          liveContent += String(event.delta || '')
          if (mode === 'markdown') setArticleMarkdown(liveContent)
          else setHtml(liveContent)
        }
        if (event.type === 'done') {
          if (mode === 'markdown') {
            liveContent = String(event.markdown || liveContent)
            setArticleMarkdown(liveContent)
          } else {
            liveContent = String(event.html || liveContent)
            setHtml(liveContent)
            setPreviewHtml(liveContent)
          }
          if (event.title) form.setFieldValue('title', event.title)
        }
        if (event.type === 'error') {
          throw new Error(String(event.message || 'AI 生成失败'))
        }
      })
    }
    message.success(successText)
  }

  const buildAnalysisBody = (values: Record<string, unknown>, mode: GenerateMode) => {
    if (selectedContentType === 'quick_checklist') {
      return {
        url: mode === 'markdown' ? '/api/wechat/quick-checklist-md-stream' : '/api/wechat/quick-checklist-stream',
        body: {
          company: companyFilter,
          post: postFilter,
          limit: checklistLimit,
          order_by_time: checklistOrderByTime,
          days: checklistOrderByTime ? checklistDays : undefined,
          wechat_theme: values.wechat_theme,
        },
      }
    }
    return {
      url: mode === 'markdown' ? '/api/wechat/question-analysis-md-stream' : '/api/wechat/question-analysis-stream',
      body: {
        company: companyFilter,
        post: postFilter,
        days: analysisDays,
        limit: 200,
        wechat_theme: values.wechat_theme,
      },
    }
  }

  const generateArticle = async () => {
    try {
      const values = await form.validateFields()
      if (sourceMode === 'analysis' && (!companyFilter || !postFilter)) {
        message.warning('请先选择公司和岗位方向')
        return
      }
      if (sourceMode !== 'analysis' && (!sourceMarkdown.trim() || sourceMarkdown.trim() === defaultMarkdown.trim())) {
        message.warning(sourceMode === 'single' ? '请先选择一条面经' : '请先粘贴 Markdown 内容')
        return
      }

      setStreaming(true)
      setAnalyzing(sourceMode === 'analysis')
      setArticle(null)
      setHtml('')
      setPreviewHtml('')
      setArticleMarkdown('')
      setAnalysisData(null)

      let url = generateMode === 'markdown' ? '/api/wechat/md-stream' : '/api/wechat/ai-stream'
      let body: Record<string, unknown> = {
        markdown: sourceMarkdown,
        title: values.title,
        author: values.author,
        digest: values.digest,
        source_record_id: selectedRecord?.id,
        style: values.style,
        wechat_theme: values.wechat_theme,
      }

      if (sourceMode === 'analysis') {
        const analysisRequest = buildAnalysisBody(values, generateMode)
        url = analysisRequest.url
        body = analysisRequest.body
      }

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          Accept: 'text/event-stream',
          'Content-Type': 'application/json; charset=utf-8',
        },
        body: JSON.stringify(body),
      })
      await handleStreamEvents(
        response,
        generateMode === 'markdown' ? 'AI 已生成 Markdown，可继续编辑并实时预览' : 'AI 已生成公众号 HTML，可继续编辑后保存',
        generateMode,
      )
    } catch (e: unknown) {
      if (e instanceof Error) message.error(e.message || 'AI 生成失败')
    } finally {
      setStreaming(false)
      setAnalyzing(false)
    }
  }

  const generateCover = async () => {
    try {
      const values = await form.validateFields()
      const markdownForCover =
        (generateMode === 'markdown' ? articleMarkdown : sourceMarkdown) ||
        sourceMarkdown ||
        articleMarkdown ||
        html ||
        (analysisData ? JSON.stringify({ stats: analysisData.stats, records: analysisData.records }, null, 2) : '')
      if (!markdownForCover.trim()) {
        message.warning('请先生成或填写正文内容，再生成封面')
        return
      }
      setCoverGenerating(true)
      const cover = await wechatApi.generateCover({
        markdown: markdownForCover,
        title: values.title,
        style: values.style,
        cover_prompt: values.cover_prompt,
      })
      setGeneratedCover({
        base64: cover.cover_base64,
        mime: cover.cover_mime || 'image/png',
        name: 'AI 生成封面',
      })
      setCustomCover(null)
      setArticle(null)
      if (cover.cover_prompt) form.setFieldValue('cover_prompt', cover.cover_prompt)
      message.success('AI 封面已生成，确认后可保存稿件')
    } catch (e: unknown) {
      if (e instanceof Error) message.error(e.message || '生成封面失败')
    } finally {
      setCoverGenerating(false)
    }
  }

  const saveArticle = async () => {
    try {
      const values = await form.validateFields()
      let finalHtml = html
      if (generateMode === 'markdown') {
        finalHtml = previewHtml || (await renderMarkdownPreview(articleMarkdown, false))
      }
      if (!finalHtml.trim()) {
        message.warning('请先生成或填写公众号内容')
        return
      }
      setSaving(true)
      const sourceForSave =
        generateMode === 'markdown'
          ? articleMarkdown
          : sourceMarkdown || (analysisData ? JSON.stringify({ stats: analysisData.stats, records: analysisData.records }, null, 2) : '')
      const activeCover = customCover || generatedCover
      const saved = await wechatApi.saveGenerated({
        markdown: sourceForSave,
        html: finalHtml,
        title: values.title,
        author: values.author,
        digest: values.digest,
        source_record_id: selectedRecord?.id,
        style: values.style,
        wechat_theme: values.wechat_theme,
        cover_prompt: values.cover_prompt,
        cover_base64: activeCover?.base64,
        cover_mime: activeCover?.mime,
      })
      setArticle(saved)
      setHtml(saved.html || finalHtml)
      setPreviewHtml(saved.html || finalHtml)
      if (saved.cover_base64 && !customCover) {
        setGeneratedCover({
          base64: saved.cover_base64,
          mime: saved.cover_mime || 'image/png',
          name: 'AI 生成封面',
        })
      }
      message.success(`已保存稿件 #${saved.id}，${activeCover ? '封面已一并保存' : '尚未保存封面'}`)
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
      setGeneratedCover(null)
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
    : generatedCover
      ? {
          title: 'AI 封面',
          src: `data:${generatedCover.mime};base64,${generatedCover.base64}`,
          hint: generatedCover.name,
        }
    : article?.cover_base64
      ? {
          title: 'AI 封面',
          src: `data:${article.cover_mime || 'image/png'};base64,${article.cover_base64}`,
          hint: '已保存到数据库',
        }
      : null

  const renderSourceCard = () => (
    <Card title={analysisData ? '真实样本摘要' : '原始素材'} className="surface-card wechat-editor-card secondary">
      {analysisData ? (
        <Alert
          type="success"
          showIcon
          message={`已将 ${analysisData.stats.record_count} 篇真实面经样本直接交给 AI 分析。`}
          description={`识别问题 ${analysisData.stats.unique_question_count} 个；最高频模块：${analysisData.stats.categories[0]?.name || '暂无'}。`}
        />
      ) : (
        <TextArea
          value={sourceMarkdown}
          onChange={(e) => {
            setSourceMarkdown(e.target.value)
            resetGenerated()
          }}
          autoSize={false}
          className="wechat-source-editor"
          style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace' }}
        />
      )}
    </Card>
  )

  return (
    <div className="wechat-workbench-page">
      <div className="page-title">
        <h2>公众号工坊</h2>
        <p>左侧配置生成规则，中间编辑内容，右侧固定预览。Markdown 模式下可以边改边看排版效果。</p>
      </div>

      <Form form={form} layout="vertical">
        <div className="wechat-workbench-grid">
          <aside className="wechat-config-pane">
            <Card title="生成模式" className="surface-card wechat-panel-card">
              <Segmented
                block
                value={generateMode}
                onChange={(value) => {
                  setGenerateMode(value as GenerateMode)
                  setArticle(null)
                  setHtml('')
                  setPreviewHtml('')
                  setArticleMarkdown('')
                }}
                options={[
                  { label: '直接生成 HTML', value: 'html', icon: <ThunderboltOutlined /> },
                  { label: 'Markdown 再排版', value: 'markdown', icon: <FileMarkdownOutlined /> },
                ]}
              />
              <Alert
                type="info"
                showIcon
                style={{ marginTop: 12 }}
                message={generateMode === 'html' ? '后端直接生成 HTML' : 'AI 生成 Markdown，再按主题渲染'}
                description={
                  generateMode === 'html'
                    ? '适合快速出稿。AI 生成完成后，右侧会刷新公众号预览。'
                    : '适合精修内容。中间编辑 Markdown，右侧按当前排版风格实时刷新。'
                }
              />
            </Card>

            <Card title="内容与风格" className="surface-card wechat-panel-card">
              <Space direction="vertical" size={12} style={{ width: '100%' }}>
                <Form.Item name="style" label="内容类型" style={{ marginBottom: 0 }}>
                  <Select
                    options={contentTypeOptions}
                    onChange={(value) => {
                      const type = value as ContentType
                      const mode = getSourceMode(type)
                      resetGenerated()
                      if (mode === 'manual') {
                        setSelectedId(undefined)
                        setSelectedRecord(null)
                      }
                      if (mode === 'analysis') {
                        setSelectedId(undefined)
                        setSelectedRecord(null)
                        setSourceMarkdown('')
                      }
                      if (mode === 'single' && !selectedRecord && !sourceMarkdown.trim()) {
                        setSourceMarkdown(defaultMarkdown)
                      }
                    }}
                  />
                </Form.Item>
                <Form.Item
                  name="wechat_theme"
                  label="排版风格"
                  tooltip="来自 Raphael Publish 的公众号排版主题；自动模式会根据内容类型选择默认风格。"
                  style={{ marginBottom: 0 }}
                >
                  <Select showSearch optionFilterProp="label" options={wechatThemeOptions} onChange={() => setArticle(null)} />
                </Form.Item>
                <Alert type="info" showIcon message={activeTypeGuide.title} description={activeTypeGuide.text} />
              </Space>
            </Card>

            {sourceMode === 'single' && (
              <Card title="面经来源" className="surface-card wechat-panel-card">
                <Space direction="vertical" size={12} style={{ width: '100%' }}>
                  <Row gutter={12}>
                    <Col xs={24} md={12} xl={24} xxl={12}>
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
                    <Col xs={24} md={12} xl={24} xxl={12}>
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
                    placeholder="选择一条真实面经"
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
                    <Alert type="success" showIcon message={`${selectedRecord.company || '未知公司'} / ${selectedRecord.post}`} description={selectedRecord.title} />
                  ) : (
                    <Alert type="warning" showIcon message="请先选择一条面经，或切换到手动粘贴。" />
                  )}
                  <Space wrap>
                    <Button onClick={loadRecords} loading={recordLoading}>
                      刷新列表
                    </Button>
                    <Button type="primary" icon={<ThunderboltOutlined />} loading={streaming && !analyzing} onClick={generateArticle}>
                      {activeTypeGuide.button}
                    </Button>
                  </Space>
                </Space>
              </Card>
            )}

            {sourceMode === 'analysis' && (
              <Card title={selectedContentType === 'quick_checklist' ? '速查样本条件' : '趋势分析条件'} className="surface-card wechat-panel-card">
                <Space direction="vertical" size={12} style={{ width: '100%' }}>
                  <Row gutter={12}>
                    <Col xs={24} md={12} xl={24} xxl={12}>
                      <Text type="secondary">公司（必填）</Text>
                      <Select value={companyFilter} onChange={setCompanyFilter} options={companyOptions} style={{ width: '100%', marginTop: 6 }} showSearch optionFilterProp="label" />
                    </Col>
                    <Col xs={24} md={12} xl={24} xxl={12}>
                      <Text type="secondary">岗位方向（必填）</Text>
                      <Select value={postFilter} onChange={setPostFilter} options={postOptions} style={{ width: '100%', marginTop: 6 }} showSearch optionFilterProp="label" />
                    </Col>
                  </Row>
                  {selectedContentType === 'quick_checklist' ? (
                    <>
                      <Row gutter={12}>
                        <Col xs={24} md={12}>
                          <Text type="secondary">面经条数</Text>
                          <InputNumber min={1} max={50} value={checklistLimit} onChange={(value) => setChecklistLimit(Number(value || 10))} style={{ width: '100%', marginTop: 6 }} />
                        </Col>
                        <Col xs={24} md={12}>
                          <Text type="secondary">抽样方式</Text>
                          <div style={{ marginTop: 10 }}>
                            <Checkbox checked={checklistOrderByTime} onChange={(e) => setChecklistOrderByTime(e.target.checked)}>
                              按时间倒序
                            </Checkbox>
                          </div>
                        </Col>
                      </Row>
                      {checklistOrderByTime && <Select value={checklistDays} onChange={setChecklistDays} options={analysisRangeOptions} style={{ width: '100%' }} />}
                    </>
                  ) : (
                    <Select value={analysisDays} onChange={setAnalysisDays} options={analysisRangeOptions} style={{ width: '100%' }} />
                  )}
                  <Button type="primary" icon={<BarChartOutlined />} loading={analyzing} onClick={generateArticle}>
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
              <Card title="手动素材" className="surface-card wechat-panel-card">
                <Space direction="vertical" size={12} style={{ width: '100%' }}>
                  <Alert type="info" showIcon message="适合临时粘贴一篇面经、文章草稿或从卡片工坊带来的 Markdown。" />
                  <Button type="primary" icon={<ThunderboltOutlined />} loading={streaming} onClick={generateArticle}>
                    {activeTypeGuide.button}
                  </Button>
                </Space>
              </Card>
            )}

            <Card title="文章参数" className="surface-card wechat-panel-card">
              <Row gutter={12}>
                <Col xs={24}>
                  <Form.Item name="title" label="公众号标题" rules={[{ required: true, message: '请输入标题' }]}>
                    <Input maxLength={64} />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12} xl={24} xxl={12}>
                  <Form.Item name="author" label="作者">
                    <Input maxLength={12} />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12} xl={24} xxl={12}>
                  <Form.Item name="digest" label="摘要">
                    <Input maxLength={120} />
                  </Form.Item>
                </Col>
                <Col xs={24}>
                  <Form.Item name="cover_prompt" label="封面提示词">
                    <TextArea autoSize={{ minRows: 3, maxRows: 6 }} placeholder="选填。写封面风格、画面元素、配色，例如：深蓝白底、技术报告风、不要文字和水印。" />
                  </Form.Item>
                </Col>
              </Row>
            </Card>
          </aside>

          <main className="wechat-editor-pane">
            {generateMode === 'markdown' ? (
              <>
                <Card
                  title="AI 生成 Markdown"
                  className="surface-card wechat-editor-card"
                  extra={streaming ? <Tag color="processing">生成中</Tag> : previewing ? <Tag color="blue">预览刷新中</Tag> : <Tag color="green">可编辑</Tag>}
                >
                  <Alert type="info" showIcon style={{ marginBottom: 12 }} message="主编辑区。修改 Markdown 或切换排版风格后，右侧预览会自动刷新。" />
                  <TextArea
                    value={articleMarkdown}
                    onChange={(e) => {
                      setArticleMarkdown(e.target.value)
                      setArticle(null)
                    }}
                    autoSize={false}
                    className="wechat-main-editor"
                    placeholder="点击生成后，AI 的 Markdown 会流式出现在这里。"
                    style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace' }}
                  />
                  <Space wrap style={{ marginTop: 12 }}>
                    <Button icon={<EyeOutlined />} loading={previewing} onClick={() => renderMarkdownPreview(articleMarkdown, false)}>
                      立即刷新预览
                    </Button>
                    <Button type="primary" icon={<ThunderboltOutlined />} loading={streaming} onClick={generateArticle}>
                      {activeTypeGuide.button}
                    </Button>
                  </Space>
                </Card>
                {renderSourceCard()}
              </>
            ) : (
              <>
                <Card
                  title="AI 生成 HTML"
                  className="surface-card wechat-editor-card"
                  extra={streaming ? <Tag color="processing">生成中</Tag> : article ? <Tag color="success">已保存 #{article.id}</Tag> : null}
                >
                  <Alert type="info" showIcon style={{ marginBottom: 12 }} message="后端会直接生成微信公众号 HTML。生成完成后，右侧预览刷新。" />
                  <TextArea
                    value={html}
                    onChange={(e) => {
                      setHtml(e.target.value)
                      if (!streaming) setPreviewHtml(e.target.value)
                      setArticle(null)
                    }}
                    autoSize={false}
                    className="wechat-main-editor"
                    placeholder="点击生成后，AI HTML 会流式出现在这里。"
                    style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace' }}
                  />
                  <Button type="primary" icon={<ThunderboltOutlined />} loading={streaming} style={{ marginTop: 12 }} onClick={generateArticle}>
                    {activeTypeGuide.button}
                  </Button>
                </Card>
                {renderSourceCard()}
              </>
            )}
          </main>

          <WechatPreviewPane
            generateMode={generateMode}
            selectedWechatTheme={selectedWechatTheme}
            previewHtml={previewHtml}
            customCover={customCover}
            generatedCover={generatedCover}
            coverPreview={coverPreview}
            article={article}
            coverGenerating={coverGenerating}
            saving={saving}
            publishing={publishing}
            handleCoverUpload={handleCoverUpload}
            generateCover={generateCover}
            saveArticle={saveArticle}
            publishDraft={publishDraft}
            clearCustomCover={() => setCustomCover(null)}
            clearGeneratedCover={() => setGeneratedCover(null)}
          />
        </div>
      </Form>
    </div>
  )
}

export default Wechat
