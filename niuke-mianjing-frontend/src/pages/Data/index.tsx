import React, { useEffect, useMemo, useState } from 'react'
import { Button, Card, Drawer, message, Select, Space, Table, Tabs, Tag, Typography } from 'antd'
import { FileMarkdownOutlined, SearchOutlined } from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useNavigate } from 'react-router-dom'
import { logApi } from '@/api'
import type { FilterOptions, NiukeRecord } from '@/api/types'
import { buildRecordMarkdown, getNowcoderUrl } from '@/utils/markdown'

const { Paragraph, Text } = Typography

const Data: React.FC = () => {
  const navigate = useNavigate()
  const [records, setRecords] = useState<NiukeRecord[]>([])
  const [selectedRecord, setSelectedRecord] = useState<NiukeRecord | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [detailLoading, setDetailLoading] = useState(false)
  const [postFilter, setPostFilter] = useState('')
  const [companyFilter, setCompanyFilter] = useState('')
  const [filterOptions, setFilterOptions] = useState<FilterOptions>({ posts: [], companies: [] })
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 })

  const selectedMarkdown = useMemo(
    () => (selectedRecord ? buildRecordMarkdown(selectedRecord) : ''),
    [selectedRecord],
  )

  const postOptions = useMemo(
    () => [{ label: '全部方向', value: '' }, ...filterOptions.posts.map((post) => ({ label: post, value: post }))],
    [filterOptions.posts],
  )

  const companyOptions = useMemo(
    () => [
      { label: '全部公司', value: '' },
      ...filterOptions.companies.map((company) => ({ label: company, value: company })),
    ],
    [filterOptions.companies],
  )

  const fetchRecords = async (page = 1, pageSize = pagination.pageSize) => {
    try {
      setLoading(true)
      const offset = (page - 1) * pageSize
      const data = await logApi.records({
        post: postFilter || undefined,
        company: companyFilter || undefined,
        limit: pageSize,
        offset,
      })
      setRecords(data?.data || [])
      setPagination((prev) => ({
        ...prev,
        current: page,
        pageSize,
        total: data?.total || 0,
      }))
    } catch (e: unknown) {
      message.error((e as Error).message || '获取面经数据失败')
    } finally {
      setLoading(false)
    }
  }

  const openDetail = async (record: NiukeRecord) => {
    setDrawerOpen(true)
    setSelectedRecord(record)
    try {
      setDetailLoading(true)
      const detail = await logApi.record(record.id)
      setSelectedRecord(detail)
    } catch (e: unknown) {
      message.error((e as Error).message || '获取详情失败')
    } finally {
      setDetailLoading(false)
    }
  }

  useEffect(() => {
    logApi
      .filters()
      .then((data) => setFilterOptions(data || { posts: [], companies: [] }))
      .catch(() => message.warning('筛选项加载失败，可继续查看已有数据'))
  }, [])

  useEffect(() => {
    fetchRecords(1)
  }, [])

  const columns = [
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
      render: (value: string, record: NiukeRecord) => (
        <Button type="link" style={{ padding: 0, maxWidth: '100%' }} onClick={() => openDetail(record)}>
          <span style={{ display: 'inline-block', maxWidth: 360, overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {value}
          </span>
        </Button>
      ),
    },
    {
      title: '公司',
      dataIndex: 'company',
      key: 'company',
      width: 140,
      render: (value: string) => <Tag color="blue">{value || '未知公司'}</Tag>,
    },
    {
      title: '方向',
      dataIndex: 'post',
      key: 'post',
      width: 140,
      render: (value: string) => <Text>{value}</Text>,
    },
    {
      title: '编辑时间',
      dataIndex: 'edit_time',
      key: 'edit_time',
      width: 190,
      render: (value: string | null) => <Text type="secondary">{value || '-'}</Text>,
    },
    {
      title: '操作',
      key: 'action',
      width: 190,
      render: (_: unknown, record: NiukeRecord) => (
        <Space>
          <Button size="small" onClick={() => openDetail(record)}>
            详情
          </Button>
          <Button
            size="small"
            type="primary"
            ghost
            icon={<FileMarkdownOutlined />}
            onClick={() => navigate('/cards', { state: { recordId: record.id } })}
          >
            生成卡片
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div className="page-title">
        <h2>面经数据</h2>
        <p>按公司、岗位方向查看已采集面经，打开详情后可查看原文和 Markdown 预览。</p>
      </div>

      <Card className="toolbar-card">
        <Space wrap>
          <Select
            value={postFilter}
            onChange={setPostFilter}
            options={postOptions}
            style={{ width: 180 }}
            showSearch
            optionFilterProp="label"
          />
          <Select
            value={companyFilter}
            onChange={setCompanyFilter}
            options={companyOptions}
            style={{ width: 220 }}
            showSearch
            optionFilterProp="label"
          />
          <Button type="primary" icon={<SearchOutlined />} onClick={() => fetchRecords(1)}>
            查询
          </Button>
        </Space>
      </Card>

      <Card className="surface-card">
        <Table
          columns={columns}
          dataSource={records}
          rowKey="id"
          loading={loading}
          pagination={{
            ...pagination,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (page, pageSize) => fetchRecords(page, pageSize),
          }}
        />
      </Card>

      <Drawer
        title={selectedRecord?.title || '面经详情'}
        open={drawerOpen}
        width={Math.min(window.innerWidth - 24, 860)}
        onClose={() => setDrawerOpen(false)}
        extra={
          selectedRecord && (
            <Space>
              {selectedRecord.content_id && (
                <Button href={getNowcoderUrl(selectedRecord)} target="_blank">
                  查看原文
                </Button>
              )}
              <Button type="primary" onClick={() => navigate('/cards', { state: { recordId: selectedRecord.id } })}>
                去卡片工坊
              </Button>
            </Space>
          )
        }
        loading={detailLoading}
      >
        {selectedRecord && (
          <Tabs
            items={[
              {
                key: 'raw',
                label: '原文内容',
                children: (
                  <Paragraph style={{ whiteSpace: 'pre-wrap', lineHeight: 1.9 }}>
                    {selectedRecord.content || '暂无内容'}
                  </Paragraph>
                ),
              },
              {
                key: 'markdown',
                label: 'Markdown 预览',
                children: (
                  <div className="markdown-body">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{selectedMarkdown}</ReactMarkdown>
                  </div>
                ),
              },
            ]}
          />
        )}
      </Drawer>
    </div>
  )
}

export default Data
