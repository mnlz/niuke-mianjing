import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Form, message, Upload } from 'antd'
import type { UploadProps } from 'antd'
import { useLocation } from 'react-router-dom'
import { logApi } from '@/api'
import { wechatApi } from '@/api/wechat'
import type { NiukeRecord, WeChatArticleData, WeChatQuestionAnalysisData, WeChatThemeGroup } from '@/api/types'
import { useFilterOptions } from '@/hooks/useFilterOptions'
import { useRecords } from '@/hooks/useRecords'
import { useErrorMessage } from '@/hooks/useErrorMessage'
import { buildRecordMarkdown } from '@/utils/markdown'
import {
  contentTypeGuides,
  defaultMarkdown,
  getSourceMode,
  type ContentType,
  type GenerateMode,
} from './wechatConfig'
import { computeCoverPreview, parseSseChunk, readImageAsCover, type CustomCover } from './wechatUtils'
import WechatPreviewPane from './WechatPreviewPane'
import ConfigPane from './panes/ConfigPane'
import SourceSinglePane from './panes/SourceSinglePane'
import SourceAnalysisPane from './panes/SourceAnalysisPane'
import SourceManualPane from './panes/SourceManualPane'
import EditorPane from './panes/EditorPane'

const Wechat: React.FC = () => {
  const location = useLocation()
  const state = location.state as { markdown?: string; recordId?: number } | null
  const [form] = Form.useForm()
  const selectedContentType = (Form.useWatch('style', form) || 'single_interpretation') as ContentType
  const selectedWechatTheme = (Form.useWatch('wechat_theme', form) || 'auto') as string
  const sourceMode = getSourceMode(selectedContentType)
  const activeTypeGuide = contentTypeGuides[selectedContentType] || contentTypeGuides.single_interpretation
  const errMsg = useErrorMessage()

  const [generateMode, setGenerateMode] = useState<GenerateMode>('markdown')
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
  const [postFilter, setPostFilter] = useState('')
  const [companyFilter, setCompanyFilter] = useState('')
  const [analysisDays, setAnalysisDays] = useState(30)
  const [checklistLimit, setChecklistLimit] = useState(10)
  const [checklistOrderByTime, setChecklistOrderByTime] = useState(false)
  const [checklistDays, setChecklistDays] = useState(30)
  const [analysisData, setAnalysisData] = useState<WeChatQuestionAnalysisData | null>(null)
  const [wechatThemeGroups, setWechatThemeGroups] = useState<WeChatThemeGroup[]>([])
  const [article, setArticle] = useState<WeChatArticleData | null>(null)
  const previewRequestId = useRef(0)

  const { postOptions, companyOptions } = useFilterOptions()
  const { records, loading: recordLoading, reload: loadRecords } = useRecords(postFilter, companyFilter, { pageSize: 100 })

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

  const coverPreview = useMemo(
    () => computeCoverPreview(customCover, generatedCover, article),
    [customCover, generatedCover, article],
  )

  const resetGenerated = useCallback(() => {
    setArticleMarkdown('')
    setHtml('')
    setPreviewHtml('')
    setArticle(null)
    setAnalysisData(null)
  }, [])

  const clearSelectedRecord = useCallback(() => {
    setSelectedId(undefined)
    setSelectedRecord(null)
    setSourceMarkdown(defaultMarkdown)
    setCustomCover(null)
    setGeneratedCover(null)
    resetGenerated()
  }, [resetGenerated])

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
      .catch((e: unknown) => errMsg(e, '加载面经详情失败'))
  }, [form, selectedId, errMsg, resetGenerated])

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
      if (e instanceof Error) errMsg(e, 'AI 生成失败')
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
      errMsg(e, '生成封面失败')
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
      errMsg(e, '保存失败')
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
      errMsg(e, '推送草稿失败')
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
      errMsg(e, '读取封面失败')
    }
    return Upload.LIST_IGNORE
  }

  const handleContentTypeChange = (value: ContentType) => {
    const mode = getSourceMode(value)
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
  }

  const handleGenerateModeChange = (mode: GenerateMode) => {
    setGenerateMode(mode)
    setArticle(null)
    setHtml('')
    setPreviewHtml('')
    setArticleMarkdown('')
  }

  return (
    <div className="wechat-workbench-page">
      <div className="page-title">
        <h2>公众号工坊</h2>
        <p>左侧配置生成规则，中间编辑内容，右侧固定预览。Markdown 模式下可以边改边看排版效果。</p>
      </div>

      <Form form={form} layout="vertical">
        <div className="wechat-workbench-grid">
          <aside className="wechat-config-pane">
            <ConfigPane
              form={form}
              generateMode={generateMode}
              selectedContentType={selectedContentType}
              activeTypeGuide={activeTypeGuide}
              wechatThemeOptions={wechatThemeOptions}
              onGenerateModeChange={handleGenerateModeChange}
              onContentTypeChange={handleContentTypeChange}
              onWechatThemeChange={() => setArticle(null)}
            />

            {sourceMode === 'single' && (
              <SourceSinglePane
                postOptions={postOptions}
                companyOptions={companyOptions}
                postFilter={postFilter}
                companyFilter={companyFilter}
                records={records}
                recordLoading={recordLoading}
                selectedId={selectedId}
                selectedRecord={selectedRecord}
                streaming={streaming}
                analyzing={analyzing}
                activeTypeGuide={activeTypeGuide}
                onPostFilterChange={(value) => {
                  setPostFilter(value)
                  clearSelectedRecord()
                }}
                onCompanyFilterChange={(value) => {
                  setCompanyFilter(value)
                  clearSelectedRecord()
                }}
                onSelectedIdChange={(value) => {
                  if (value) setSelectedId(value)
                  else clearSelectedRecord()
                }}
                onRefreshRecords={() => loadRecords()}
                onGenerate={generateArticle}
              />
            )}

            {sourceMode === 'analysis' && (
              <SourceAnalysisPane
                postOptions={postOptions}
                companyOptions={companyOptions}
                postFilter={postFilter}
                companyFilter={companyFilter}
                isChecklist={selectedContentType === 'quick_checklist'}
                analysisDays={analysisDays}
                checklistLimit={checklistLimit}
                checklistOrderByTime={checklistOrderByTime}
                checklistDays={checklistDays}
                analyzing={analyzing}
                analysisData={analysisData}
                activeTypeGuide={activeTypeGuide}
                onPostFilterChange={setPostFilter}
                onCompanyFilterChange={setCompanyFilter}
                onAnalysisDaysChange={setAnalysisDays}
                onChecklistLimitChange={setChecklistLimit}
                onChecklistOrderByTimeChange={setChecklistOrderByTime}
                onChecklistDaysChange={setChecklistDays}
                onGenerate={generateArticle}
              />
            )}

            {sourceMode === 'manual' && (
              <SourceManualPane
                streaming={streaming}
                activeTypeGuide={activeTypeGuide}
                onGenerate={generateArticle}
              />
            )}
          </aside>

          <main className="wechat-editor-pane">
            <EditorPane
              generateMode={generateMode}
              streaming={streaming}
              previewing={previewing}
              articleMarkdown={articleMarkdown}
              html={html}
              sourceMarkdown={sourceMarkdown}
              analysisData={analysisData}
              article={article}
              activeTypeGuide={activeTypeGuide}
              onArticleMarkdownChange={(value) => {
                setArticleMarkdown(value)
                setArticle(null)
              }}
              onHtmlChange={(value) => {
                setHtml(value)
                if (!streaming) setPreviewHtml(value)
                setArticle(null)
              }}
              onSourceMarkdownChange={(value) => {
                setSourceMarkdown(value)
                resetGenerated()
              }}
              onRefreshPreview={() => renderMarkdownPreview(articleMarkdown, false)}
              onGenerate={generateArticle}
            />
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
