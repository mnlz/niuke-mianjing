import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Button, Card, Col, Input, message, Row, Select, Space, Tag, Typography } from 'antd'
import {
  CopyOutlined,
  FileImageOutlined,
  FileMarkdownOutlined,
  SearchOutlined,
  SendOutlined,
} from '@ant-design/icons'
import { toPng } from 'html-to-image'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useLocation, useNavigate } from 'react-router-dom'
import { logApi } from '@/api'
import type { CardTheme, FilterOptions, NiukeRecord } from '@/api/types'
import { buildRecordMarkdown, buildXhsDraft } from '@/utils/markdown'

const { Text, Title } = Typography
const { TextArea } = Input

type ThemeConfig = {
  pageBg: string
  accent: string
  accentSoft: string
  heading: string
  text: string
  muted: string
  tableHead: string
}

const CARD_WIDTH = 440
const CARD_HEIGHT = 586
const CONTENT_LIMIT = 475

const themeOptions: Array<{ label: string; value: CardTheme }> = [
  { label: '小红书清新', value: 'xiaohongshu' },
  { label: '字节蓝', value: 'bytedance' },
  { label: '阿里橙', value: 'alibaba' },
  { label: '极简黑白', value: 'minimal' },
  { label: '商务简报', value: 'business' },
]

const themes: Record<CardTheme, ThemeConfig> = {
  xiaohongshu: {
    pageBg: '#ffffff',
    accent: '#ffb000',
    accentSoft: '#fff1bf',
    heading: '#262626',
    text: '#2f2f2f',
    muted: '#8c8c8c',
    tableHead: '#fff2bf',
  },
  bytedance: {
    pageBg: '#ffffff',
    accent: '#1677ff',
    accentSoft: '#eaf3ff',
    heading: '#102033',
    text: '#24364b',
    muted: '#64748b',
    tableHead: '#eaf3ff',
  },
  alibaba: {
    pageBg: '#ffffff',
    accent: '#ff7a00',
    accentSoft: '#fff0dc',
    heading: '#332112',
    text: '#3d3329',
    muted: '#8a6b4a',
    tableHead: '#ffe5c2',
  },
  minimal: {
    pageBg: '#ffffff',
    accent: '#111827',
    accentSoft: '#f3f4f6',
    heading: '#111827',
    text: '#1f2937',
    muted: '#6b7280',
    tableHead: '#f3f4f6',
  },
  business: {
    pageBg: '#ffffff',
    accent: '#4f46e5',
    accentSoft: '#eef2ff',
    heading: '#172033',
    text: '#334155',
    muted: '#64748b',
    tableHead: '#eef2ff',
  },
}

const defaultMarkdown = '# 面经卡片\n\n选择一条面经，或在这里粘贴 Markdown 内容。'

const downloadText = (filename: string, content: string, type: string) => {
  const blob = new Blob([content], { type })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

const safeName = (value: string) => value.replace(/[\\/:*?"<>|]/g, '_').slice(0, 48)

const normalizeMarkdown = (value: string) =>
  value
    .replace(/\r\n/g, '\n')
    .replace(/^(\d+[.)、])(?=\S)/gm, '$1 ')
    .trim()

const splitBlocks = (value: string) => {
  const lines = normalizeMarkdown(value).split('\n')
  const blocks: string[] = []
  let i = 0

  while (i < lines.length) {
    const line = lines[i]
    if (!line.trim()) {
      i += 1
      continue
    }

    if (/^\|/.test(line.trim())) {
      const table: string[] = []
      while (i < lines.length && /^\|/.test(lines[i].trim())) {
        table.push(lines[i])
        i += 1
      }
      blocks.push(table.join('\n'))
      continue
    }

    if (/^#{1,6}\s+/.test(line.trim())) {
      blocks.push(line)
      i += 1
      continue
    }

    if (/^\d+[.)、]\s+/.test(line.trim())) {
      blocks.push(line)
      i += 1
      continue
    }

    const paragraph: string[] = []
    while (
      i < lines.length &&
      lines[i].trim() &&
      !/^\|/.test(lines[i].trim()) &&
      !/^#{1,6}\s+/.test(lines[i].trim()) &&
      !/^\d+[.)、]\s+/.test(lines[i].trim())
    ) {
      paragraph.push(lines[i])
      i += 1
    }
    blocks.push(paragraph.join('\n'))
  }

  return blocks
}

const estimateBlockHeight = (block: string) => {
  const text = block.replace(/[#>*_`|[\]()]/g, '').trim()
  if (/^#\s+/.test(block)) return 56
  if (/^##\s+/.test(block)) return 42
  if (/^#{3,6}\s+/.test(block)) return 34
  if (/^\|/.test(block.trim())) {
    const rows = block.split('\n').filter((line) => /^\|/.test(line.trim()))
    return Math.max(80, rows.length * 36 + 12)
  }
  if (/^\d+[.)、]\s+/.test(block.trim())) {
    return Math.max(28, Math.ceil(text.length / 27) * 24)
  }
  return Math.max(38, Math.ceil(text.length / 25) * 28 + 8)
}

const paginateMarkdown = (value: string) => {
  const blocks = splitBlocks(value)
  const pages: string[] = []
  let current: string[] = []
  let height = 0

  blocks.forEach((block) => {
    const blockHeight = estimateBlockHeight(block)
    if (current.length && height + blockHeight > CONTENT_LIMIT) {
      pages.push(current.join('\n\n'))
      current = []
      height = 0
    }
    current.push(block)
    height += blockHeight
  })

  if (current.length) pages.push(current.join('\n\n'))
  return pages.length ? pages : [defaultMarkdown]
}

const CardPage: React.FC<{
  content: string
  page: number
  total: number
  theme: ThemeConfig
  innerRef: (node: HTMLDivElement | null) => void
}> = ({ content, page, total, theme, innerRef }) => (
  <div
    ref={innerRef}
    className="md2-card-page"
    style={{
      width: CARD_WIDTH,
      height: CARD_HEIGHT,
      background: theme.pageBg,
      color: theme.text,
      padding: '28px 32px',
      boxShadow: '0 18px 46px rgba(15, 23, 42, 0.10)',
      overflow: 'hidden',
      position: 'relative',
    }}
  >
    <div className="md2-card-topbar" style={{ color: theme.accent }}>
      <span>‹ 备忘录</span>
      <span>分享 · · ·</span>
    </div>
    <div
      className="md2-card-content"
      style={
        {
          '--accent': theme.accent,
          '--accent-soft': theme.accentSoft,
          '--table-head': theme.tableHead,
          '--heading': theme.heading,
          '--text': theme.text,
          '--muted': theme.muted,
        } as React.CSSProperties
      }
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
    {total > 1 && (
      <div className="md2-page-no" style={{ color: theme.muted }}>
        {page + 1}/{total}
      </div>
    )}
  </div>
)

const Cards: React.FC = () => {
  const location = useLocation()
  const navigate = useNavigate()
  const initialRecordId = (location.state as { recordId?: number } | null)?.recordId
  const cardRefs = useRef<Array<HTMLDivElement | null>>([])
  const [records, setRecords] = useState<NiukeRecord[]>([])
  const [selectedId, setSelectedId] = useState<number | undefined>(initialRecordId)
  const [selectedRecord, setSelectedRecord] = useState<NiukeRecord | null>(null)
  const [markdown, setMarkdown] = useState(defaultMarkdown)
  const [theme, setTheme] = useState<CardTheme>('xiaohongshu')
  const [exporting, setExporting] = useState(false)
  const [recordLoading, setRecordLoading] = useState(false)
  const [postFilter, setPostFilter] = useState('')
  const [companyFilter, setCompanyFilter] = useState('')
  const [filterOptions, setFilterOptions] = useState<FilterOptions>({ posts: [], companies: [] })

  const xhsDraft = useMemo(() => buildXhsDraft(selectedRecord, markdown), [selectedRecord, markdown])
  const currentTheme = themes[theme]
  const pages = useMemo(() => paginateMarkdown(markdown), [markdown])

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
    logApi
      .filters()
      .then((data) => setFilterOptions(data || { posts: [], companies: [] }))
      .catch(() => message.warning('筛选项加载失败，可继续手动编辑 Markdown'))
  }, [])

  useEffect(() => {
    loadRecords()
  }, [loadRecords])

  useEffect(() => {
    if (!selectedId) return
    logApi
      .record(selectedId)
      .then((record) => {
        setSelectedRecord(record)
        setMarkdown(buildRecordMarkdown(record))
      })
      .catch((e: unknown) => message.error((e as Error).message || '加载面经详情失败'))
  }, [selectedId])

  const handleExportPng = async () => {
    try {
      setExporting(true)
      for (let i = 0; i < pages.length; i += 1) {
        const node = cardRefs.current[i]
        if (!node) continue
        const dataUrl = await toPng(node, {
          pixelRatio: 2,
          cacheBust: true,
          backgroundColor: '#ffffff',
        })
        const a = document.createElement('a')
        a.href = dataUrl
        a.download = `${safeName(xhsDraft.title)}_${i + 1}.png`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
      }
      message.success(`已导出 ${pages.length} 张卡片`)
    } catch (e: unknown) {
      message.error((e as Error).message || '导出 PNG 失败')
    } finally {
      setExporting(false)
    }
  }

  const copyCaption = async () => {
    await navigator.clipboard.writeText(xhsDraft.caption)
    message.success('小红书文案已复制')
  }

  return (
    <div>
      <div className="page-title">
        <h2>卡片工坊</h2>
        <p>按固定卡片尺寸自动拆分 Markdown，也可以转换为微信公众号 HTML 并推送草稿箱。</p>
      </div>

      <Card className="toolbar-card">
        <Space wrap>
          <Select
            value={postFilter}
            onChange={(value) => {
              setPostFilter(value)
              setSelectedId(undefined)
            }}
            options={postOptions}
            style={{ width: 170 }}
            showSearch
            optionFilterProp="label"
          />
          <Select
            value={companyFilter}
            onChange={(value) => {
              setCompanyFilter(value)
              setSelectedId(undefined)
            }}
            options={companyOptions}
            style={{ width: 200 }}
            showSearch
            optionFilterProp="label"
          />
          <Button icon={<SearchOutlined />} onClick={loadRecords}>
            刷新面经
          </Button>
          <Select
            allowClear
            showSearch
            loading={recordLoading}
            placeholder="选择一条面经"
            value={selectedId}
            style={{ minWidth: 320 }}
            optionFilterProp="label"
            onChange={(value) => setSelectedId(value)}
            options={records.map((record) => ({
              label: `${record.company || '未知公司'} / ${record.post} / ${record.title}`,
              value: record.id,
            }))}
          />
          <Select<CardTheme> value={theme} onChange={setTheme} options={themeOptions} style={{ width: 160 }} />
          <Tag color="blue">自动拆分：{pages.length} 张</Tag>
          <Button icon={<FileImageOutlined />} type="primary" loading={exporting} onClick={handleExportPng}>
            导出全部 PNG
          </Button>
          <Button icon={<SendOutlined />} onClick={() => navigate('/wechat', { state: { markdown, recordId: selectedRecord?.id } })}>
            去公众号工坊
          </Button>
          <Button icon={<CopyOutlined />} onClick={copyCaption}>
            复制文案
          </Button>
          <Button
            icon={<FileMarkdownOutlined />}
            onClick={() => downloadText(`${xhsDraft.title}.md`, markdown, 'text/markdown;charset=utf-8')}
          >
            下载 Markdown
          </Button>
        </Space>
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={10}>
          <Card title="Markdown 编辑" className="surface-card">
            <TextArea
              value={markdown}
              onChange={(e) => setMarkdown(e.target.value)}
              autoSize={{ minRows: 24, maxRows: 36 }}
              style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace' }}
            />
          </Card>

          <Card title="小红书文案" className="surface-card" style={{ marginTop: 16 }}>
            <Title level={5} style={{ marginTop: 0 }}>
              {xhsDraft.title}
            </Title>
            <TextArea value={xhsDraft.caption} readOnly autoSize={{ minRows: 7, maxRows: 12 }} />
            <div style={{ marginTop: 12 }}>
              <Space wrap>
                {xhsDraft.tags.map((tag) => (
                  <Tag key={tag}>#{tag}</Tag>
                ))}
              </Space>
            </div>
          </Card>
        </Col>

        <Col xs={24} lg={14}>
          <Card title="卡片预览" className="surface-card">
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 18,
                overflow: 'auto',
                padding: 12,
                background: '#f7f7fb',
              }}
            >
              {pages.map((pageContent, index) => (
                <CardPage
                  key={`${index}-${pageContent.slice(0, 12)}`}
                  content={pageContent}
                  page={index}
                  total={pages.length}
                  theme={currentTheme}
                  innerRef={(node) => {
                    cardRefs.current[index] = node
                  }}
                />
              ))}
            </div>
          </Card>
        </Col>
      </Row>

    </div>
  )
}

export default Cards
