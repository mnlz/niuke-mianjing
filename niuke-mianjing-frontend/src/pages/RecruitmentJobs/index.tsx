import React, { useEffect, useMemo, useState } from 'react'
import { Button, Card, Input, message, Select, Space, Table, Tag, Typography } from 'antd'
import { ReloadOutlined, SearchOutlined } from '@ant-design/icons'
import { recruitmentApi } from '@/api'
import type { RecruitmentJob, RecruitmentSource, RecruitmentTrack, RecruitmentType, RecruitmentVersion } from '@/api/types'

const { Paragraph, Text } = Typography
const PAGE_SIZE = 20

const typeOptions: Array<{ label: string; value: RecruitmentType | 'all' }> = [
  { label: '全部类型', value: 'all' },
  { label: '校招', value: 'campus' },
  { label: '实习', value: 'intern' },
  { label: '社招', value: 'social' },
]

const typeName = (value?: string) => typeOptions.find((item) => item.value === value)?.label || '校招'

const RecruitmentJobs: React.FC = () => {
  const [sources, setSources] = useState<RecruitmentSource[]>([])
  const [tracks, setTracks] = useState<RecruitmentTrack[]>([])
  const [versions, setVersions] = useState<RecruitmentVersion[]>([])
  const [source, setSource] = useState('tencent')
  const [recruitmentType, setRecruitmentType] = useState<RecruitmentType>('campus')
  const [track, setTrack] = useState('')
  const [keyword, setKeyword] = useState('')
  const [refreshSource, setRefreshSource] = useState('all')
  const [jobs, setJobs] = useState<RecruitmentJob[]>([])
  const [loading, setLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [pagination, setPagination] = useState({ current: 1, total: 0 })

  const sourceOptions = useMemo(
    () => sources.map((item) => ({ label: item.company, value: item.source })),
    [sources],
  )
  const refreshSourceOptions = useMemo(
    () => [{ label: '全部公司', value: 'all' }, ...sourceOptions],
    [sourceOptions],
  )
  const availableTypeOptions = useMemo(() => {
    const supported = sources.find((item) => item.source === source)?.supported_recruitment_types
    if (!supported?.length) return typeOptions.filter((item) => item.value !== 'all')
    return typeOptions.filter((item) => item.value !== 'all' && supported.includes(item.value as RecruitmentType))
  }, [source, sources])
  const trackOptions = useMemo(
    () => [{ label: '全部方向', value: '' }, ...tracks.map((item) => ({ label: item.name, value: item.id }))],
    [tracks],
  )
  const latestVersion = versions.find((item) => item.source === source && item.recruitment_type === recruitmentType)

  const loadJobs = async (page = 1) => {
    try {
      setLoading(true)
      const data = await recruitmentApi.jobs({
        source,
        recruitment_type: recruitmentType,
        track: keyword ? undefined : track || undefined,
        keyword: keyword || undefined,
        page,
        page_size: PAGE_SIZE,
      })
      setJobs(data.items || [])
      setPagination({ current: page, total: data.total || 0 })
    } catch (e: unknown) {
      message.error((e as Error).message || '岗位数据加载失败')
      setJobs([])
      setPagination((prev) => ({ ...prev, total: 0 }))
    } finally {
      setLoading(false)
    }
  }

  const refreshJobs = async (refreshSource = source, refreshType: RecruitmentType | 'all' = recruitmentType) => {
    try {
      setRefreshing(true)
      const result = await recruitmentApi.refresh({ source: refreshSource, recruitment_type: refreshType })
      message.success(`刷新完成：${result.refresh_version}，${result.total_jobs} 条`)
      const nextVersions = await recruitmentApi.versions()
      setVersions(nextVersions || [])
      await loadJobs(1)
    } catch (e: unknown) {
      message.error((e as Error).message || '岗位刷新失败')
    } finally {
      setRefreshing(false)
    }
  }

  useEffect(() => {
    recruitmentApi.sources().then((data) => setSources(data || [])).catch(() => setSources([]))
    recruitmentApi.tracks().then((data) => setTracks(data || [])).catch(() => setTracks([]))
    recruitmentApi.versions().then((data) => setVersions(data || [])).catch(() => setVersions([]))
    void loadJobs(1)
  }, [])

  useEffect(() => {
    if (availableTypeOptions.some((item) => item.value === recruitmentType)) return
    setRecruitmentType((availableTypeOptions[0]?.value as RecruitmentType) || 'campus')
  }, [availableTypeOptions, recruitmentType])

  const columns = [
    {
      title: '岗位',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
      render: (value: string, record: RecruitmentJob) => (
        <a href={record.source_url} target="_blank" rel="noreferrer">{value}</a>
      ),
    },
    { title: '公司', dataIndex: 'company', key: 'company', width: 100 },
    {
      title: '类型',
      dataIndex: 'recruitment_type',
      key: 'recruitment_type',
      width: 90,
      render: (value: string) => <Tag>{typeName(value)}</Tag>,
    },
    {
      title: '分类',
      key: 'category',
      width: 130,
      render: (_: unknown, record: RecruitmentJob) => <Tag color="blue">{record.display_category || record.category || '综合岗位'}</Tag>,
    },
    { title: '地点', dataIndex: 'location', key: 'location', width: 180, ellipsis: true },
    { title: '版本', dataIndex: 'refresh_version', key: 'refresh_version', width: 170, ellipsis: true },
    {
      title: '详情',
      dataIndex: 'detail_status',
      key: 'detail_status',
      width: 100,
      render: (value: string) => <Tag color={value === 'complete' ? 'green' : 'orange'}>{value || '-'}</Tag>,
    },
  ]

  return (
    <div>
      <div className="page-title">
        <h2>岗位管理</h2>
        <p>查看已入库的官方招聘岗位，按公司、类型、方向或关键词筛选。</p>
      </div>

      <Card className="toolbar-card">
        <Space wrap>
          <Select value={source} onChange={setSource} options={sourceOptions} style={{ width: 160 }} />
          <Select value={recruitmentType} onChange={setRecruitmentType} options={availableTypeOptions} style={{ width: 120 }} />
          <Select value={track} onChange={setTrack} options={trackOptions} style={{ width: 160 }} />
          <Input
            value={keyword}
            onChange={(event) => setKeyword(event.target.value)}
            onPressEnter={() => loadJobs(1)}
            allowClear
            prefix={<SearchOutlined />}
            placeholder="搜索岗位"
            style={{ width: 260 }}
          />
          <Button type="primary" icon={<SearchOutlined />} loading={loading} onClick={() => loadJobs(1)}>查询</Button>
          <Button icon={<ReloadOutlined />} loading={refreshing} onClick={() => refreshJobs()}>刷新当前</Button>
          <Select
            value={refreshSource}
            options={refreshSourceOptions}
            style={{ width: 150 }}
            onChange={setRefreshSource}
            disabled={refreshing}
          />
          <Button icon={<ReloadOutlined />} loading={refreshing} onClick={() => refreshJobs(refreshSource, 'all')}>刷新选中</Button>
          <Text type="secondary">
            {latestVersion ? `版本 ${latestVersion.refresh_version || '历史数据'} · ${latestVersion.job_count} 条` : '暂无版本'}
          </Text>
        </Space>
      </Card>

      <Card className="surface-card">
        <Table
          columns={columns}
          dataSource={jobs}
          rowKey={(record) => `${record.source}-${record.recruitment_type}-${record.source_job_id}`}
          loading={loading}
          expandable={{
            expandedRowRender: (record) => (
              <Space direction="vertical" size={8} style={{ width: '100%' }}>
                <Text strong>岗位职责</Text>
                <Paragraph style={{ whiteSpace: 'pre-wrap' }}>{record.description || '暂无'}</Paragraph>
                <Text strong>任职要求</Text>
                <Paragraph style={{ whiteSpace: 'pre-wrap' }}>{record.requirements || '暂无'}</Paragraph>
              </Space>
            ),
          }}
          pagination={{
            current: pagination.current,
            pageSize: PAGE_SIZE,
            total: pagination.total,
            showSizeChanger: false,
            showTotal: (total) => `共 ${total} 条`,
            onChange: loadJobs,
          }}
        />
      </Card>
    </div>
  )
}

export default RecruitmentJobs
