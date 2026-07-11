import React from 'react'
import { Card, Empty, Progress, Space, Typography } from 'antd'
import { useCrawlStore } from '@/store/crawlStore'
const { Text } = Typography

const CrawlProgress: React.FC = () => {
  const progresses = useCrawlStore((s) => s.progresses)
  const entries = Object.values(progresses)

  return (
    <Card title="实时爬取进度" className="surface-card">
      {entries.length === 0 ? (
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无运行中的爬取任务" />
      ) : (
        <Space direction="vertical" style={{ width: '100%' }} size={14}>
          {entries.map((p) => {
            const percent = p.totalPages > 0 ? Math.round((p.currentPage / p.totalPages) * 100) : 0
            const statusColor = p.status === 'done' ? '#16a34a' : p.status === 'error' ? '#ef4444' : '#1677ff'

            return (
              <div key={p.post}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, gap: 12 }}>
                  <Text strong>{p.post}</Text>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {p.currentPage}/{p.totalPages} 页 · 新增 {p.newRecords || 0} · 更新 {p.updatedRecords || 0}
                  </Text>
                </div>
                <Progress
                  percent={p.status === 'done' ? 100 : percent}
                  status={p.status === 'error' ? 'exception' : undefined}
                  strokeColor={statusColor}
                />
              </div>
            )
          })}
        </Space>
      )}
    </Card>
  )
}

export default CrawlProgress
