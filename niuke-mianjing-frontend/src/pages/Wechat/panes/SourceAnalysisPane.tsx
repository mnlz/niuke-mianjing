import React from 'react'
import { Button, Card, Checkbox, Col, InputNumber, Row, Select, Space, Tag, Typography } from 'antd'
import { BarChartOutlined } from '@ant-design/icons'
import type { WeChatQuestionAnalysisData } from '@/api/types'
import { analysisRangeOptions } from '../wechatConfig'

const { Text } = Typography

interface Props {
  postOptions: Array<{ label: string; value: string }>
  companyOptions: Array<{ label: string; value: string }>
  postFilter: string
  companyFilter: string
  isChecklist: boolean
  analysisDays: number
  checklistLimit: number
  checklistOrderByTime: boolean
  checklistDays: number
  analyzing: boolean
  analysisData: WeChatQuestionAnalysisData | null
  activeTypeGuide: { button: string }
  onPostFilterChange: (value: string) => void
  onCompanyFilterChange: (value: string) => void
  onAnalysisDaysChange: (value: number) => void
  onChecklistLimitChange: (value: number) => void
  onChecklistOrderByTimeChange: (checked: boolean) => void
  onChecklistDaysChange: (value: number) => void
  onGenerate: () => void
}

const SourceAnalysisPane: React.FC<Props> = ({
  postOptions,
  companyOptions,
  postFilter,
  companyFilter,
  isChecklist,
  analysisDays,
  checklistLimit,
  checklistOrderByTime,
  checklistDays,
  analyzing,
  analysisData,
  activeTypeGuide,
  onPostFilterChange,
  onCompanyFilterChange,
  onAnalysisDaysChange,
  onChecklistLimitChange,
  onChecklistOrderByTimeChange,
  onChecklistDaysChange,
  onGenerate,
}) => {
  return (
    <Card
      title={isChecklist ? '速查样本条件' : '趋势分析条件'}
      className="surface-card wechat-panel-card"
    >
      <Space direction="vertical" size={12} style={{ width: '100%' }}>
        <Row gutter={12}>
          <Col xs={24} md={12} xl={24} xxl={12}>
            <Text type="secondary">公司（必填）</Text>
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
            <Text type="secondary">岗位方向（必填）</Text>
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
        {isChecklist ? (
          <>
            <Row gutter={12}>
              <Col xs={24} md={12}>
                <Text type="secondary">面经条数</Text>
                <InputNumber
                  min={1}
                  max={50}
                  value={checklistLimit}
                  onChange={(value) => onChecklistLimitChange(Number(value || 10))}
                  style={{ width: '100%', marginTop: 6 }}
                />
              </Col>
              <Col xs={24} md={12}>
                <Text type="secondary">抽样方式</Text>
                <div style={{ marginTop: 10 }}>
                  <Checkbox checked={checklistOrderByTime} onChange={(e) => onChecklistOrderByTimeChange(e.target.checked)}>
                    按时间倒序
                  </Checkbox>
                </div>
              </Col>
            </Row>
            {checklistOrderByTime && (
              <Select
                value={checklistDays}
                onChange={onChecklistDaysChange}
                options={analysisRangeOptions}
                style={{ width: '100%' }}
              />
            )}
          </>
        ) : (
          <Select
            value={analysisDays}
            onChange={onAnalysisDaysChange}
            options={analysisRangeOptions}
            style={{ width: '100%' }}
          />
        )}
        <Button type="primary" icon={<BarChartOutlined />} loading={analyzing} onClick={onGenerate}>
          {activeTypeGuide.button}
        </Button>
        {analysisData && (
          <Tag color="blue">
            样本 {analysisData.stats.record_count} 篇 / 高频题 {analysisData.stats.unique_question_count} 个
          </Tag>
        )}
      </Space>
    </Card>
  )
}

export default SourceAnalysisPane
