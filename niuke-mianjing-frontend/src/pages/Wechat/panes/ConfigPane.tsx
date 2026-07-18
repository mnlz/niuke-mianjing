import React from 'react'
import { Alert, Card, Col, Form, Input, Row, Segmented, Select, Space } from 'antd'
import { FileMarkdownOutlined, ThunderboltOutlined } from '@ant-design/icons'
import type { FormInstance } from 'antd'
import type { ContentType, GenerateMode } from '../wechatConfig'
import { contentTypeOptions, contentTypeGuides } from '../wechatConfig'

const { TextArea } = Input

interface WechatThemeOption {
  label: string
  value: string
}
interface WechatThemeGroupOption {
  label: string
  options: WechatThemeOption[]
}

interface Props {
  form: FormInstance
  generateMode: GenerateMode
  selectedContentType: ContentType
  activeTypeGuide: { title: string; text: string; button: string }
  wechatThemeOptions: (WechatThemeOption | WechatThemeGroupOption)[]
  onGenerateModeChange: (mode: GenerateMode) => void
  onContentTypeChange: (value: ContentType) => void
  onWechatThemeChange: () => void
}

const ConfigPane: React.FC<Props> = ({
  form,
  generateMode,
  selectedContentType,
  activeTypeGuide,
  wechatThemeOptions,
  onGenerateModeChange,
  onContentTypeChange,
  onWechatThemeChange,
}) => {
  return (
    <>
      <Card title="生成模式" className="surface-card wechat-panel-card">
        <Segmented
          block
          value={generateMode}
          onChange={(value) => onGenerateModeChange(value as GenerateMode)}
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
            <Select options={contentTypeOptions} onChange={(value) => onContentTypeChange(value as ContentType)} />
          </Form.Item>
          <Form.Item
            name="wechat_theme"
            label="排版风格"
            tooltip="来自 Raphael Publish 的公众号排版主题；自动模式会根据内容类型选择默认风格。"
            style={{ marginBottom: 0 }}
          >
            <Select showSearch optionFilterProp="label" options={wechatThemeOptions} onChange={onWechatThemeChange} />
          </Form.Item>
          <Alert type="info" showIcon message={activeTypeGuide.title} description={activeTypeGuide.text} />
        </Space>
      </Card>

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
              <TextArea
                autoSize={{ minRows: 3, maxRows: 6 }}
                placeholder="选填。写封面风格、画面元素、配色，例如：深蓝白底、技术报告风、不要文字和水印。"
              />
            </Form.Item>
          </Col>
        </Row>
      </Card>
    </>
  )
}

export default ConfigPane
