import React from 'react'
import { Button, Checkbox, Empty, Tag, Typography } from 'antd'
import { RobotOutlined } from '@ant-design/icons'
import type { NiukeRecord } from '@/api/types'
import { formatDisplayTime } from '@/utils/datetime'

const { Text } = Typography

interface Props {
  companyFilter: string
  postFilter: string
  records: NiukeRecord[]
  selectedIds: number[]
  onToggle: (recordId: number, checked: boolean) => void
  onToggleAll: () => void
  onAnalyze: () => void
}

const ReviewOverviewCard: React.FC<Props> = ({
  companyFilter,
  postFilter,
  records,
  selectedIds,
  onToggle,
  onToggleAll,
  onAnalyze,
}) => {
  const sampleRecords = records.slice(0, 8)
  const allSelected = sampleRecords.length > 0 && sampleRecords.every((record) => selectedIds.includes(record.id))

  return (
    <div className="interview-ai-card">
      <div className="interview-ai-header">
        <div>
          <Text>AI Interview Analysis</Text>
          <h2>{companyFilter || '全部公司'} / {postFilter || '全部方向'} AI 面经分析</h2>
          <p>选择要交给 AI 的面经，下一步生成岗位考点、准备顺序和风险提示。</p>
        </div>
        <div>
          <Button onClick={onToggleAll} disabled={!sampleRecords.length}>
            {allSelected ? '取消全选' : '全选当前'}
          </Button>
          <Button type="primary" icon={<RobotOutlined />} onClick={onAnalyze} disabled={!selectedIds.length}>
            分析已选 {selectedIds.length} 篇
          </Button>
        </div>
      </div>

      {sampleRecords.length ? (
        <div className="interview-ai-picker">
          {sampleRecords.map((record) => (
            <label key={record.id}>
              <Checkbox
                checked={selectedIds.includes(record.id)}
                onChange={(event) => onToggle(record.id, event.target.checked)}
              />
              <span>
                <b>{record.title}</b>
                <small>
                  <Tag color="blue">{record.company || '未知公司'}</Tag>
                  <Tag>{record.post}</Tag>
                  {formatDisplayTime(record.edit_time)}
                </small>
              </span>
            </label>
          ))}
        </div>
      ) : (
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="当前筛选下暂无可分析面经" />
      )}
    </div>
  )
}

export default ReviewOverviewCard
