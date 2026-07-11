import React from 'react'
import { Alert, Button, Card, Input, Space, Tag } from 'antd'
import { EyeOutlined, ThunderboltOutlined } from '@ant-design/icons'
import type { WeChatQuestionAnalysisData } from '@/api/types'
import type { GenerateMode } from '../wechatConfig'

const { TextArea } = Input

interface Props {
  generateMode: GenerateMode
  streaming: boolean
  previewing: boolean
  articleMarkdown: string
  html: string
  sourceMarkdown: string
  analysisData: WeChatQuestionAnalysisData | null
  article: { id?: number } | null
  activeTypeGuide: { button: string }
  onArticleMarkdownChange: (value: string) => void
  onHtmlChange: (value: string) => void
  onSourceMarkdownChange: (value: string) => void
  onRefreshPreview: () => void
  onGenerate: () => void
}

const EditorPane: React.FC<Props> = ({
  generateMode,
  streaming,
  previewing,
  articleMarkdown,
  html,
  sourceMarkdown,
  analysisData,
  article,
  activeTypeGuide,
  onArticleMarkdownChange,
  onHtmlChange,
  onSourceMarkdownChange,
  onRefreshPreview,
  onGenerate,
}) => {
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
          onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => onSourceMarkdownChange(e.target.value)}
          autoSize={false}
          className="wechat-source-editor"
          style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace' }}
        />
      )}
    </Card>
  )

  if (generateMode === 'markdown') {
    return (
      <>
        <Card
          title="AI 生成 Markdown"
          className="surface-card wechat-editor-card"
          extra={
            streaming ? (
              <Tag color="processing">生成中</Tag>
            ) : previewing ? (
              <Tag color="blue">预览刷新中</Tag>
            ) : (
              <Tag color="green">可编辑</Tag>
            )
          }
        >
          <Alert
            type="info"
            showIcon
            style={{ marginBottom: 12 }}
            message="主编辑区。修改 Markdown 或切换排版风格后，右侧预览会自动刷新。"
          />
          <TextArea
            value={articleMarkdown}
            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => onArticleMarkdownChange(e.target.value)}
            autoSize={false}
            className="wechat-main-editor"
            placeholder="点击生成后，AI 的 Markdown 会流式出现在这里。"
            style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace' }}
          />
          <Space wrap style={{ marginTop: 12 }}>
            <Button icon={<EyeOutlined />} loading={previewing} onClick={onRefreshPreview}>
              立即刷新预览
            </Button>
            <Button type="primary" icon={<ThunderboltOutlined />} loading={streaming} onClick={onGenerate}>
              {activeTypeGuide.button}
            </Button>
          </Space>
        </Card>
        {renderSourceCard()}
      </>
    )
  }

  return (
    <>
      <Card
        title="AI 生成 HTML"
        className="surface-card wechat-editor-card"
        extra={
          streaming ? (
            <Tag color="processing">生成中</Tag>
          ) : article ? (
            <Tag color="success">已保存 #{article.id}</Tag>
          ) : null
        }
      >
        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 12 }}
          message="后端会直接生成微信公众号 HTML。生成完成后，右侧预览刷新。"
        />
        <TextArea
          value={html}
          onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => onHtmlChange(e.target.value)}
          autoSize={false}
          className="wechat-main-editor"
          placeholder="点击生成后，AI HTML 会流式出现在这里。"
          style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace' }}
        />
        <Button
          type="primary"
          icon={<ThunderboltOutlined />}
          loading={streaming}
          style={{ marginTop: 12 }}
          onClick={onGenerate}
        >
          {activeTypeGuide.button}
        </Button>
      </Card>
      {renderSourceCard()}
    </>
  )
}

export default EditorPane
