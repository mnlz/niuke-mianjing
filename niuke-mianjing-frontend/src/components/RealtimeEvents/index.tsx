import React, { useMemo } from 'react'
import { Badge, Card, Empty, List, Tag, Typography } from 'antd'
import { useCrawlStore } from '@/store/crawlStore'
import type { WSMessageType } from '@/api/types'

const { Text } = Typography

const typeLabels: Record<WSMessageType, string> = {
  crawl_start: '开始爬取',
  crawl_page_done: '页面完成',
  crawl_post_done: '方向完成',
  crawl_all_done: '全部完成',
  crawl_error: '爬取异常',
  job_status_change: '任务状态',
}

const typeColors: Record<WSMessageType, string> = {
  crawl_start: 'processing',
  crawl_page_done: 'blue',
  crawl_post_done: 'green',
  crawl_all_done: 'success',
  crawl_error: 'error',
  job_status_change: 'purple',
}

const describeMessage = (msg: { type: WSMessageType; data?: unknown; message?: string }) => {
  const data = (msg.data || {}) as Record<string, unknown>
  if (msg.message) return msg.message
  if (msg.type === 'crawl_page_done') {
    return `${data.post || '未知方向'} 第 ${data.page || '-'} 页完成，新增 ${data.new_count || 0}，更新 ${data.updated_count || 0}`
  }
  if (msg.type === 'crawl_post_done') {
    return `${data.post || '未知方向'} 完成，新增 ${data.new_count || 0}，更新 ${data.updated_count || 0}`
  }
  if (msg.type === 'crawl_start') return `${data.post || '未知方向'} 开始爬取`
  if (msg.type === 'crawl_all_done') return '本轮爬取已全部完成'
  return JSON.stringify(data)
}

const RealtimeEvents: React.FC = () => {
  const connected = useCrawlStore((s) => s.connected)
  const lastMessages = useCrawlStore((s) => s.lastMessages)
  const items = useMemo(() => lastMessages.slice(-5).reverse(), [lastMessages])

  return (
    <Card
      className="surface-card"
      title="实时事件"
      extra={<Badge status={connected ? 'success' : 'default'} text={connected ? '已连接' : '未连接'} />}
    >
      {items.length === 0 ? (
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无实时事件，启动爬取后会在这里更新" />
      ) : (
        <List
          size="small"
          dataSource={items}
          renderItem={(item) => (
            <List.Item style={{ paddingLeft: 0, paddingRight: 0 }}>
              <div style={{ width: '100%' }}>
                <Tag color={typeColors[item.type]}>{typeLabels[item.type]}</Tag>
                <Text type="secondary" style={{ fontSize: 13 }}>
                  {describeMessage(item)}
                </Text>
              </div>
            </List.Item>
          )}
        />
      )}
    </Card>
  )
}

export default RealtimeEvents
