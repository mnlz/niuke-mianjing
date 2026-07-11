import React from 'react'
import { Alert, Button, Card, Space } from 'antd'
import { ThunderboltOutlined } from '@ant-design/icons'

interface Props {
  streaming: boolean
  activeTypeGuide: { button: string }
  onGenerate: () => void
}

const SourceManualPane: React.FC<Props> = ({ streaming, activeTypeGuide, onGenerate }) => {
  return (
    <Card title="手动素材" className="surface-card wechat-panel-card">
      <Space direction="vertical" size={12} style={{ width: '100%' }}>
        <Alert
          type="info"
          showIcon
          message="适合临时粘贴一篇面经、文章草稿或从卡片工坊带来的 Markdown。"
        />
        <Button type="primary" icon={<ThunderboltOutlined />} loading={streaming} onClick={onGenerate}>
          {activeTypeGuide.button}
        </Button>
      </Space>
    </Card>
  )
}

export default SourceManualPane
