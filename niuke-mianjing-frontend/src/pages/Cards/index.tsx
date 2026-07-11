import React, { useEffect, useMemo, useRef, useState } from 'react'
import { Button, Card, Col, Input, InputNumber, message, Modal, Row, Select, Space, Switch, Tag, Typography } from 'antd'
import {
  CopyOutlined,
  FileImageOutlined,
  FileMarkdownOutlined,
  SearchOutlined,
  SendOutlined,
} from '@ant-design/icons'
import { toPng } from 'html-to-image'
import { useLocation, useNavigate } from 'react-router-dom'
import { logApi, wechatApi } from '@/api'
import type { CardTheme, NiukeRecord } from '@/api/types'
import { useFilterOptions } from '@/hooks/useFilterOptions'
import { useRecords } from '@/hooks/useRecords'
import { useErrorMessage } from '@/hooks/useErrorMessage'
import { buildRecordMarkdown, buildXhsDraft } from '@/utils/markdown'
import CardPage from './CardPage'
import {
  cardSizeOptions,
  cardSizePresets,
  defaultMarkdown,
  themes,
  themeOptions,
  type CardSizePresetKey,
} from './cardConfig'
import { paginateMarkdown } from './cardPagination'
import { downloadText, parseDataUrlImage, safeName } from './cardUtils'

const { Text, Title } = Typography
const { TextArea } = Input

const Cards: React.FC = () => {
  const location = useLocation()
  const navigate = useNavigate()
  const initialRecordId = (location.state as { recordId?: number } | null)?.recordId
  const cardRefs = useRef<Array<HTMLDivElement | null>>([])
  const [selectedId, setSelectedId] = useState<number | undefined>(initialRecordId)
  const [selectedRecord, setSelectedRecord] = useState<NiukeRecord | null>(null)
  const [markdown, setMarkdown] = useState(defaultMarkdown)
  const [theme, setTheme] = useState<CardTheme>('xiaohongshu')
  const [cardPresetKey, setCardPresetKey] = useState<CardSizePresetKey>('xhs_3_4')
  const [exporting, setExporting] = useState(false)
  const [postFilter, setPostFilter] = useState('')
  const [companyFilter, setCompanyFilter] = useState('')
  const [newspicOpen, setNewspicOpen] = useState(false)
  const [newspicTitle, setNewspicTitle] = useState('')
  const [newspicContent, setNewspicContent] = useState('')
  const [newspicImageCount, setNewspicImageCount] = useState(9)
  const [newspicPublishing, setNewspicPublishing] = useState(false)
  const [newspicCommentEnabled, setNewspicCommentEnabled] = useState(true)

  const errMsg = useErrorMessage()
  const { postOptions, companyOptions } = useFilterOptions()
  const { records, loading: recordLoading, reload: loadRecords } = useRecords(postFilter, companyFilter, { pageSize: 100 })

  const xhsDraft = useMemo(() => buildXhsDraft(selectedRecord, markdown), [selectedRecord, markdown])
  const currentTheme = themes[theme]
  const currentCardPreset = cardSizePresets[cardPresetKey]
  const exportPixelRatio = currentCardPreset.exportWidth / currentCardPreset.width
  const pages = useMemo(() => paginateMarkdown(markdown, currentCardPreset), [currentCardPreset, markdown])
  const newspicMaxImages = Math.min(20, pages.length)

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
      .catch((e: unknown) => errMsg(e, '加载面经详情失败'))
  }, [selectedId, errMsg])

  const handleExportPng = async () => {
    try {
      setExporting(true)
      for (let i = 0; i < pages.length; i += 1) {
        const node = cardRefs.current[i]
        if (!node) continue
        const dataUrl = await toPng(node, {
          pixelRatio: exportPixelRatio,
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
      errMsg(e, '导出 PNG 失败')
    } finally {
      setExporting(false)
    }
  }

  const buildDefaultNewspicContent = () => {
    const source = selectedRecord
      ? `${selectedRecord.company || '目标公司'} / ${selectedRecord.post || '面试方向'}`
      : '面经复习卡片'
    const tags = xhsDraft.tags.map((tag) => `#${tag}`).join(' ')
    return `${xhsDraft.title}\n\n整理了一组 ${source} 的复习卡片，适合通勤、睡前、面试前快速过一遍。\n\n${tags}`
  }

  const openNewspicModal = () => {
    setNewspicTitle((value) => value || xhsDraft.title.slice(0, 64))
    setNewspicContent((value) => value || buildDefaultNewspicContent())
    setNewspicImageCount(Math.min(9, pages.length || 1))
    setNewspicOpen(true)
  }

  const renderCardImages = async (count: number) => {
    const imageCount = Math.min(Math.max(count, 1), pages.length, 20)
    const images: string[] = []
    const imageMimes: string[] = []

    for (let i = 0; i < imageCount; i += 1) {
      const node = cardRefs.current[i]
      if (!node) continue
      const dataUrl = await toPng(node, {
        pixelRatio: exportPixelRatio,
        cacheBust: true,
        backgroundColor: '#ffffff',
      })
      const parsed = parseDataUrlImage(dataUrl)
      images.push(parsed.base64)
      imageMimes.push(parsed.mime)
    }

    if (!images.length) {
      throw new Error('没有可发布的卡片图片，请先确认右侧预览已加载')
    }
    return { images, imageMimes }
  }

  const handleCreateNewspicDraft = async () => {
    if (!newspicTitle.trim()) {
      message.warning('请先填写贴图标题')
      return
    }

    try {
      setNewspicPublishing(true)
      const { images, imageMimes } = await renderCardImages(newspicImageCount)
      const result = await wechatApi.createNewspicDraft({
        title: newspicTitle.trim(),
        content: newspicContent,
        images,
        image_mimes: imageMimes,
        need_open_comment: newspicCommentEnabled ? 1 : 0,
        only_fans_can_comment: 0,
      })
      setNewspicOpen(false)
      Modal.success({
        title: '公众号贴图草稿已创建',
        content: `已上传 ${images.length} 张卡片图，草稿 media_id：${result.media_id}`,
      })
    } catch (e: unknown) {
      errMsg(e, '创建公众号贴图草稿失败')
    } finally {
      setNewspicPublishing(false)
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
        <p>按小红书、微信等平台尺寸智能拆分 Markdown，也可以导出图片或发布公众号贴图草稿。</p>
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
          <Button icon={<SearchOutlined />} onClick={() => loadRecords()}>
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
          <Select<CardSizePresetKey>
            value={cardPresetKey}
            onChange={setCardPresetKey}
            options={cardSizeOptions}
            style={{ width: 240 }}
          />
          <Tag color="blue">自动拆分：{pages.length} 张</Tag>
          <Tag color="geekblue">
            导出 {currentCardPreset.exportWidth}×{currentCardPreset.exportHeight}
          </Tag>
          <Button icon={<FileImageOutlined />} type="primary" loading={exporting} onClick={handleExportPng}>
            导出全部 PNG
          </Button>
          <Button icon={<SendOutlined />} onClick={openNewspicModal}>
            发布公众号贴图
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
                  preset={currentCardPreset}
                  innerRef={(node) => {
                    cardRefs.current[index] = node
                  }}
                />
              ))}
            </div>
          </Card>
        </Col>
      </Row>

      <Modal
        title="发布为公众号贴图草稿"
        open={newspicOpen}
        okText="创建贴图草稿"
        cancelText="取消"
        confirmLoading={newspicPublishing}
        onOk={handleCreateNewspicDraft}
        onCancel={() => setNewspicOpen(false)}
        width={680}
      >
        <Space direction="vertical" size={14} style={{ width: '100%' }}>
          <div>
            <Text strong>标题</Text>
            <Input
              value={newspicTitle}
              onChange={(e) => setNewspicTitle(e.target.value)}
              maxLength={64}
              showCount
              placeholder="请输入公众号贴图标题"
              style={{ marginTop: 8 }}
            />
          </div>

          <div>
            <Text strong>正文说明</Text>
            <TextArea
              value={newspicContent}
              onChange={(e) => setNewspicContent(e.target.value)}
              autoSize={{ minRows: 6, maxRows: 10 }}
              placeholder="显示在贴图草稿里的文字说明，可留空"
              style={{ marginTop: 8 }}
            />
          </div>

          <Space wrap>
            <Text strong>发布图片数</Text>
            <InputNumber
              min={1}
              max={newspicMaxImages || 1}
              value={Math.min(newspicImageCount, newspicMaxImages || 1)}
              onChange={(value) => setNewspicImageCount(value || 1)}
            />
            <Text type="secondary">将使用当前预览里的前 {Math.min(newspicImageCount, newspicMaxImages || 1)} 张卡片</Text>
          </Space>

          <Space>
            <Text strong>开启留言</Text>
            <Switch checked={newspicCommentEnabled} onChange={setNewspicCommentEnabled} />
          </Space>

          <Text type="secondary">
            贴图模式会把卡片上传为公众号永久图片素材，并创建草稿；不会自动群发。建议一次 3-9 张，读者刷起来更舒服。
          </Text>
        </Space>
      </Modal>

    </div>
  )
}

export default Cards
