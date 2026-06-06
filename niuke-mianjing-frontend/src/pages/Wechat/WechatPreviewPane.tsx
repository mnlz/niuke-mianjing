import React from 'react'
import { Alert, Button, Card, Space, Tag, Typography, Upload } from 'antd'
import type { UploadProps } from 'antd'
import {
  DatabaseOutlined,
  DeleteOutlined,
  SendOutlined,
  ThunderboltOutlined,
  UploadOutlined,
} from '@ant-design/icons'

import type { WeChatArticleData } from '@/api/types'
import type { GenerateMode } from './wechatConfig'
import type { CustomCover } from './wechatUtils'

const { Text } = Typography

type CoverPreview = {
  title: string
  src: string
  hint: string
} | null

type WechatPreviewPaneProps = {
  generateMode: GenerateMode
  selectedWechatTheme: string
  previewHtml: string
  customCover: CustomCover | null
  generatedCover: CustomCover | null
  coverPreview: CoverPreview
  article: WeChatArticleData | null
  coverGenerating: boolean
  saving: boolean
  publishing: boolean
  handleCoverUpload: UploadProps['beforeUpload']
  generateCover: () => void
  saveArticle: () => void
  publishDraft: () => void
  clearCustomCover: () => void
  clearGeneratedCover: () => void
}

const WechatPreviewPane: React.FC<WechatPreviewPaneProps> = ({
  generateMode,
  selectedWechatTheme,
  previewHtml,
  customCover,
  generatedCover,
  coverPreview,
  article,
  coverGenerating,
  saving,
  publishing,
  handleCoverUpload,
  generateCover,
  saveArticle,
  publishDraft,
  clearCustomCover,
  clearGeneratedCover,
}) => (
  <aside className="wechat-preview-pane">
    <Card
      title="公众号预览"
      className="surface-card wechat-preview-card"
      extra={
        <Space size={6} wrap>
          {generateMode === 'markdown' ? <Tag color="purple">Markdown 排版</Tag> : <Tag color="geekblue">HTML 出稿</Tag>}
          {selectedWechatTheme && selectedWechatTheme !== 'auto' ? <Tag color="blue">{selectedWechatTheme}</Tag> : <Tag>自动风格</Tag>}
        </Space>
      }
    >
      <Space wrap className="wechat-preview-actions">
        <Upload accept="image/*" showUploadList={false} beforeUpload={handleCoverUpload}>
          <Button icon={<UploadOutlined />}>上传封面</Button>
        </Upload>
        <Button icon={<ThunderboltOutlined />} loading={coverGenerating} onClick={generateCover}>
          生成封面
        </Button>
        {customCover && (
          <Button icon={<DeleteOutlined />} onClick={clearCustomCover}>
            改用 AI
          </Button>
        )}
        {generatedCover && !customCover && (
          <Button icon={<DeleteOutlined />} onClick={clearGeneratedCover}>
            清除封面
          </Button>
        )}
        <Button icon={<DatabaseOutlined />} loading={saving} onClick={saveArticle}>
          保存
        </Button>
        <Button type="primary" icon={<SendOutlined />} loading={publishing} disabled={!article?.id || !article.cover_base64} onClick={publishDraft}>
          推草稿
        </Button>
      </Space>

      <div className="wechat-preview-shell workbench-preview">
        {previewHtml ? <iframe title="公众号预览" className="wechat-preview-frame" srcDoc={previewHtml} /> : <div className="wechat-preview-empty">生成完成后，这里会展示公众号预览</div>}
      </div>

      <div className="wechat-cover-compact">
        {coverPreview ? (
          <>
            <img alt="微信公众号封面" src={coverPreview.src} />
            <div>
              <Text strong>{coverPreview.title}</Text>
              <Text type="secondary" ellipsis style={{ display: 'block', maxWidth: 220 }}>
                {coverPreview.hint}
              </Text>
            </div>
          </>
        ) : (
          <Alert type="warning" showIcon message="还没有封面，请上传图片或点击生成封面。" />
        )}
      </div>

      {article?.id && <Alert type="success" showIcon style={{ marginTop: 12 }} message={`数据库稿件 #${article.id}，状态：${article.status}`} />}
      <Text type="secondary" style={{ display: 'block', marginTop: 10 }}>
        浏览器预览仅用于排版检查，最终仍建议在公众号后台手机预览。
      </Text>
    </Card>
  </aside>
)

export default WechatPreviewPane
