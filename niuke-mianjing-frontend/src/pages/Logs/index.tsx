import React, { useEffect, useMemo, useState } from 'react'
import { Button, Card, DatePicker, InputNumber, message, Select, Space, Table, Typography } from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import { logApi } from '@/api'
import type { CrawlLog, FilterOptions } from '@/api/types'
import StatusTag from '@/components/StatusTag'

const { Text } = Typography
const { RangePicker } = DatePicker

const STATUS_OPTIONS = [
  { label: '全部状态', value: '' },
  { label: '成功', value: 'success' },
  { label: '运行中', value: 'running' },
  { label: '失败', value: 'failed' },
]

const Logs: React.FC = () => {
  const [logs, setLogs] = useState<CrawlLog[]>([])
  const [loading, setLoading] = useState(false)
  const [filterOptions, setFilterOptions] = useState<FilterOptions>({ posts: [], companies: [] })
  const [postFilter, setPostFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [dateRange, setDateRange] = useState<[string, string] | null>(null)
  const [limit, setLimit] = useState(20)

  const postOptions = useMemo(
    () => [{ label: '全部方向', value: '' }, ...filterOptions.posts.map((post) => ({ label: post, value: post }))],
    [filterOptions.posts],
  )

  const fetchLogs = async () => {
    try {
      setLoading(true)
      const params: Parameters<typeof logApi.logs>[0] = { limit }
      if (postFilter) params.post = postFilter
      if (statusFilter) params.status = statusFilter
      if (dateRange) {
        params.start_date = dateRange[0]
        params.end_date = dateRange[1]
      }
      const data = await logApi.logs(params)
      setLogs(Array.isArray(data) ? data : [])
    } catch (e: unknown) {
      message.error((e as Error).message || '获取日志失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    logApi
      .filters()
      .then((data) => setFilterOptions(data || { posts: [], companies: [] }))
      .catch(() => message.warning('方向筛选项加载失败'))
  }, [])

  useEffect(() => {
    fetchLogs()
  }, [])

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
    { title: '方向', dataIndex: 'post', key: 'post', width: 160 },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (value: string) => <StatusTag status={value} />,
    },
    {
      title: '开始时间',
      dataIndex: 'start_time',
      key: 'start_time',
      width: 190,
      render: (value: string | null) => <Text type="secondary">{value || '-'}</Text>,
    },
    {
      title: '结束时间',
      dataIndex: 'end_time',
      key: 'end_time',
      width: 190,
      render: (value: string | null) => <Text type="secondary">{value || '-'}</Text>,
    },
    { title: '页数', dataIndex: 'total_pages', key: 'total_pages', width: 90 },
    { title: '新增', dataIndex: 'new_records', key: 'new_records', width: 90 },
    { title: '更新', dataIndex: 'updated_records', key: 'updated_records', width: 90 },
    {
      title: '错误信息',
      dataIndex: 'error_message',
      key: 'error_message',
      ellipsis: true,
      render: (value: string | null) => <Text type={value ? 'danger' : 'secondary'}>{value || '-'}</Text>,
    },
  ]

  return (
    <div>
      <div className="page-title">
        <h2>爬取日志</h2>
        <p>查看每次爬取任务的执行结果、时间和新增数量。</p>
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
          <Select value={statusFilter} onChange={setStatusFilter} options={STATUS_OPTIONS} style={{ width: 120 }} />
          <RangePicker
            onChange={(_, dateStrings) => {
              setDateRange(dateStrings[0] && dateStrings[1] ? [dateStrings[0], dateStrings[1]] : null)
            }}
          />
          <InputNumber min={1} max={100} value={limit} onChange={(value) => setLimit(value || 20)} addonAfter="条" />
          <Button type="primary" icon={<SearchOutlined />} onClick={fetchLogs}>
            查询
          </Button>
        </Space>
      </Card>

      <Card className="surface-card">
        <Table
          columns={columns}
          dataSource={logs}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 20, showTotal: (total) => `共 ${total} 条` }}
        />
      </Card>
    </div>
  )
}

export default Logs
