import React from 'react'
import { Button, Drawer, Empty, Select, Space, Tabs, Tag, Typography } from 'antd'
import { CopyOutlined, StarFilled, StarOutlined } from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { NiukeRecord, ReviewMastery, ReviewProgress } from '@/api/types'
import { formatDisplayTime } from '@/utils/datetime'

const { Paragraph } = Typography

interface ReviewCard {
  title: string
  tag: string
}

interface MasteryOption {
  label: string
  value: ReviewMastery
  color: string
}

interface ProgressPatch {
  favorite?: boolean
  mastery?: ReviewMastery
  note?: string | null
}

interface Props {
  open: boolean
  loading: boolean
  record: NiukeRecord | null
  selectedProgress: ReviewProgress | null
  selectedMarkdown: string
  reviewCards: ReviewCard[]
  detailTab: string
  masteryOptions: MasteryOption[]
  onClose: () => void
  onDetailTabChange: (tab: string) => void
  onCopyMarkdown: () => void
  onUpdateProgress: (recordId: number, patch: ProgressPatch) => void
}

const InterviewDetailDrawer: React.FC<Props> = ({
  open,
  loading,
  record,
  selectedProgress,
  selectedMarkdown,
  reviewCards,
  detailTab,
  masteryOptions,
  onClose,
  onDetailTabChange,
  onCopyMarkdown,
  onUpdateProgress,
}) => (
  <Drawer
    title={null}
    open={open}
    width={Math.min(window.innerWidth - 24, 980)}
    onClose={onClose}
    loading={loading}
    className="interview-detail-drawer"
    extra={null}
  >
    {record && (
      <div className="interview-detail">
        <div className="detail-hero-card">
          <Space size={8} wrap>
            <Tag color="blue">{record.company || '未知公司'}</Tag>
            <Tag>{record.role_family_name}</Tag>
            <Tag color="default">{formatDisplayTime(record.edit_time)}</Tag>
          </Space>
          <h2>{record.title}</h2>
          <p>
            这篇面经已整理为站内阅读、Markdown 复盘和复习卡片三个视图，适合面试前快速回看。
          </p>
          <Space wrap>
            <Button
              icon={selectedProgress?.favorite ? <StarFilled /> : <StarOutlined />}
              onClick={() => onUpdateProgress(record.id, { favorite: !selectedProgress?.favorite })}
            >
              {selectedProgress?.favorite ? '已收藏' : '收藏'}
            </Button>
            <Select
              value={selectedProgress?.mastery || 'new'}
              options={masteryOptions.map((item) => ({ label: item.label, value: item.value }))}
              onChange={(value) => onUpdateProgress(record.id, { mastery: value })}
              style={{ width: 112 }}
            />
            <Button icon={<CopyOutlined />} onClick={onCopyMarkdown}>
              复制 Markdown
            </Button>
            <Button type="primary" onClick={() => onDetailTabChange('cards')}>
              查看复习卡片
            </Button>
          </Space>
        </div>

        <Tabs
          activeKey={detailTab}
          onChange={onDetailTabChange}
          items={[
            {
              key: 'raw',
              label: '原文内容',
              children: (
                <div className="detail-reading-card raw">
                  <Paragraph>
                    {record.content || '暂无内容'}
                  </Paragraph>
                </div>
              ),
            },
            {
              key: 'markdown',
              label: 'Markdown 复盘',
              children: (
                <div className="detail-reading-card markdown-body markdown-review-body">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{selectedMarkdown}</ReactMarkdown>
                </div>
              ),
            },
            {
              key: 'cards',
              label: '复习卡片',
              children: (
                <div className="review-card-grid">
                  {reviewCards.length > 0 ? reviewCards.map((card, index) => (
                    <div className="review-mini-card" key={`${card.title}-${index}`}>
                      <div>
                        <span>{String(index + 1).padStart(2, '0')}</span>
                        <Tag color={index < 3 ? 'red' : 'blue'}>{card.tag}</Tag>
                      </div>
                      <h3>{card.title}</h3>
                      <p>建议补充：核心概念、30 秒答法、常见追问、项目落地点。</p>
                    </div>
                  )) : <Empty description="暂无可提取的复习卡片" />}
                </div>
              ),
            },
          ]}
        />
      </div>
    )}
  </Drawer>
)

export default InterviewDetailDrawer
