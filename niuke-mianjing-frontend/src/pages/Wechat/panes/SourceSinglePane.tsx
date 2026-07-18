import React from 'react'
import { Alert, Button, Card, Col, Row, Select, Space, Typography } from 'antd'
import { ThunderboltOutlined } from '@ant-design/icons'
import type { NiukeRecord } from '@/api/types'

const { Text } = Typography

interface Props {
  postOptions: Array<{ label: string; value: string }>
  companyOptions: Array<{ label: string; value: string }>
  postFilter: string
  companyFilter: string
  records: NiukeRecord[]
  recordLoading: boolean
  selectedId: number | undefined
  selectedRecord: NiukeRecord | null
  streaming: boolean
  analyzing: boolean
  activeTypeGuide: { button: string }
  onPostFilterChange: (value: string) => void
  onCompanyFilterChange: (value: string) => void
  onSelectedIdChange: (value: number | undefined) => void
  onRefreshRecords: () => void
  onGenerate: () => void
}

const SourceSinglePane: React.FC<Props> = ({
  postOptions,
  companyOptions,
  postFilter,
  companyFilter,
  records,
  recordLoading,
  selectedId,
  selectedRecord,
  streaming,
  analyzing,
  activeTypeGuide,
  onPostFilterChange,
  onCompanyFilterChange,
  onSelectedIdChange,
  onRefreshRecords,
  onGenerate,
}) => {
  return (
    <Card title="面经来源" className="surface-card wechat-panel-card">
      <Space direction="vertical" size={12} style={{ width: '100%' }}>
        <Row gutter={12}>
          <Col xs={24} md={12} xl={24} xxl={12}>
            <Text type="secondary">筛选公司</Text>
            <Select
              value={companyFilter}
              onChange={onCompanyFilterChange}
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
              onChange={onPostFilterChange}
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
          onChange={(value) => onSelectedIdChange(value)}
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
          <Alert type="warning" showIcon message="请先选择一条面经，或切换到手动粘贴。" />
        )}
        <Space wrap>
          <Button onClick={onRefreshRecords} loading={recordLoading}>
            刷新列表
          </Button>
          <Button
            type="primary"
            icon={<ThunderboltOutlined />}
            loading={streaming && !analyzing}
            onClick={onGenerate}
          >
            {activeTypeGuide.button}
          </Button>
        </Space>
      </Space>
    </Card>
  )
}

export default SourceSinglePane
