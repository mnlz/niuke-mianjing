import React, { useEffect, useMemo, useState } from 'react'
import {
  Button,
  Card,
  Form,
  Input,
  InputNumber,
  message,
  Modal,
  Popconfirm,
  Radio,
  Select,
  Space,
  Table,
  Tag,
  Typography,
} from 'antd'
import { DeleteOutlined, PlusOutlined } from '@ant-design/icons'
import { quickCrawlApi, scheduleApi } from '@/api'
import type { CreateScheduleRequest, JobTreeItem, ScheduleJob } from '@/api/types'

const { Text } = Typography

type ScheduleMode = 'daily' | 'weekly' | 'interval' | 'cron'

const hourOptions = Array.from({ length: 24 }, (_, hour) => ({
  label: `${hour.toString().padStart(2, '0')} 时`,
  value: hour,
}))

const minuteOptions = [0, 5, 10, 15, 20, 30, 40, 45, 50].map((minute) => ({
  label: `${minute.toString().padStart(2, '0')} 分`,
  value: minute,
}))

const weekdayOptions = [
  { label: '周一', value: 1 },
  { label: '周二', value: 2 },
  { label: '周三', value: 3 },
  { label: '周四', value: 4 },
  { label: '周五', value: 5 },
  { label: '周六', value: 6 },
  { label: '周日', value: 0 },
]

const toCron = (values: Record<string, unknown>) => {
  const hour = Number(values.hour ?? 9)
  const minute = Number(values.minute ?? 0)
  if (values.schedule_mode === 'weekly') {
    return `${minute} ${hour} * * ${values.weekday ?? 1}`
  }
  return `${minute} ${hour} * * *`
}

const describeSchedule = (job: ScheduleJob) => {
  if (job.schedule_type === 'interval') return `每隔 ${job.schedule}`
  const parts = job.schedule.split(/\s+/)
  if (parts.length === 5) {
    const [minute, hour, , , weekday] = parts
    const time = `${hour.padStart(2, '0')}:${minute.padStart(2, '0')}`
    if (weekday !== '*') {
      const match = weekdayOptions.find((item) => String(item.value) === weekday)
      return `${match?.label || `周 ${weekday}`} ${time}`
    }
    return `每天 ${time}`
  }
  return job.schedule
}

const Schedule: React.FC = () => {
  const [jobs, setJobs] = useState<ScheduleJob[]>([])
  const [postOptions, setPostOptions] = useState<{ label: string; value: string }[]>([])
  const [loading, setLoading] = useState(true)
  const [postsLoading, setPostsLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [form] = Form.useForm()
  const scheduleMode = Form.useWatch('schedule_mode', form) as ScheduleMode

  const fetchJobs = async () => {
    try {
      setLoading(true)
      const data = await scheduleApi.list()
      setJobs(data || [])
    } catch (e: unknown) {
      message.error((e as Error).message || '获取任务列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchJobs()
  }, [])

  useEffect(() => {
    quickCrawlApi
      .getPosts()
      .then((data) => {
        const tree: JobTreeItem[] = data.tree || []
        setPostOptions(
          tree.flatMap((top) =>
            top.children.map((child) => ({ label: `${top.name} / ${child.name}`, value: child.name })),
          ),
        )
      })
      .catch(() => message.warning('爬取方向加载失败'))
      .finally(() => setPostsLoading(false))
  }, [])

  const handleCreate = async () => {
    try {
      const values = await form.validateFields()
      const mode = values.schedule_mode as ScheduleMode
      if (mode === 'interval' && !values.interval_hours && !values.interval_minutes) {
        message.warning('固定间隔不能为 0，请至少填写小时或分钟')
        return
      }
      const req: CreateScheduleRequest =
        mode === 'interval'
          ? {
              posts: values.posts,
              schedule_type: 'interval',
              schedule: `${values.interval_hours || 0}h ${values.interval_minutes || 0}m`,
              max_pages: values.max_pages,
            }
          : {
              posts: values.posts,
              schedule_type: 'cron',
              schedule: mode === 'cron' ? values.cron : toCron(values),
              max_pages: values.max_pages,
            }

      await scheduleApi.create(req)
      message.success('任务创建成功')
      setModalOpen(false)
      form.resetFields()
      fetchJobs()
    } catch (e: unknown) {
      if (e instanceof Error) message.error(e.message || '创建失败')
    }
  }

  const handleDelete = async (jobId: string) => {
    try {
      await scheduleApi.delete(jobId)
      message.success('删除成功')
      fetchJobs()
    } catch (e: unknown) {
      message.error((e as Error).message || '删除失败')
    }
  }

  const jobSummary = useMemo(() => {
    const active = jobs.filter((job) => job.next_run_time).length
    return `当前 ${jobs.length} 个任务，${active} 个有下次执行时间`
  }, [jobs])

  const columns = [
    {
      title: '任务名称',
      dataIndex: 'name',
      key: 'name',
      render: (value: string) => <Text strong>{value}</Text>,
    },
    {
      title: '爬取方向',
      dataIndex: 'posts',
      key: 'posts',
      width: 260,
      render: (value: string[]) => (
        <Space wrap>
          {(value || []).map((post) => (
            <Tag color="blue" key={post}>
              {post}
            </Tag>
          ))}
        </Space>
      ),
    },
    {
      title: '调度类型',
      dataIndex: 'schedule_type',
      key: 'schedule_type',
      width: 120,
      render: (value: string) => <Tag color={value === 'cron' ? 'purple' : 'green'}>{value === 'cron' ? '定时' : '间隔'}</Tag>,
    },
    {
      title: '调度规则',
      dataIndex: 'schedule',
      key: 'schedule',
      width: 190,
      render: (_: string, record: ScheduleJob) => describeSchedule(record),
    },
    { title: '最大页数', dataIndex: 'max_pages', key: 'max_pages', width: 110 },
    {
      title: '下次执行',
      dataIndex: 'next_run_time',
      key: 'next_run_time',
      width: 190,
      render: (value: string | null) => <Text type="secondary">{value || '-'}</Text>,
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: unknown, record: ScheduleJob) => (
        <Popconfirm
          title="删除定时任务"
          description="确定删除这个任务吗？"
          onConfirm={() => handleDelete(record.job_id)}
          okText="删除"
          cancelText="取消"
        >
          <Button danger type="link" icon={<DeleteOutlined />}>
            删除
          </Button>
        </Popconfirm>
      ),
    },
  ]

  return (
    <div>
      <div className="page-title">
        <h2>定时任务</h2>
        <p>创建周期性爬取任务，方向从牛客岗位接口加载，执行计划可用每日、每周、固定间隔或高级 Cron。</p>
      </div>

      <Card className="surface-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16, gap: 16 }}>
          <div>
            <Text strong>任务列表</Text>
            <div>
              <Text type="secondary">{jobSummary}</Text>
            </div>
          </div>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
            创建任务
          </Button>
        </div>
        <Table columns={columns} dataSource={jobs} rowKey="job_id" loading={loading} pagination={false} />
      </Card>

      <Modal
        title="创建定时任务"
        open={modalOpen}
        onOk={handleCreate}
        onCancel={() => {
          setModalOpen(false)
          form.resetFields()
        }}
        okText="创建"
        cancelText="取消"
        width={640}
      >
        <Form
          form={form}
          layout="vertical"
          style={{ marginTop: 16 }}
          initialValues={{
            schedule_mode: 'daily',
            max_pages: 10,
            hour: 9,
            minute: 0,
            weekday: 1,
            interval_hours: 2,
            interval_minutes: 0,
            cron: '0 9 * * *',
          }}
        >
          <Form.Item name="posts" label="爬取方向" rules={[{ required: true, message: '请选择方向' }]}>
            <Select
              mode="multiple"
              loading={postsLoading}
              options={postOptions}
              placeholder="选择方向"
              showSearch
              optionFilterProp="label"
              maxTagCount="responsive"
            />
          </Form.Item>
          <Form.Item name="schedule_mode" label="调度方式">
            <Radio.Group>
              <Radio.Button value="daily">每天</Radio.Button>
              <Radio.Button value="weekly">每周</Radio.Button>
              <Radio.Button value="interval">固定间隔</Radio.Button>
              <Radio.Button value="cron">高级 Cron</Radio.Button>
            </Radio.Group>
          </Form.Item>

          {(scheduleMode === 'daily' || scheduleMode === 'weekly') && (
            <Space style={{ width: '100%' }} size={12} align="start">
              {scheduleMode === 'weekly' && (
                <Form.Item name="weekday" label="星期" rules={[{ required: true, message: '请选择星期' }]}>
                  <Select options={weekdayOptions} style={{ width: 120 }} />
                </Form.Item>
              )}
              <Form.Item name="hour" label="小时" rules={[{ required: true, message: '请选择小时' }]}>
                <Select options={hourOptions} style={{ width: 120 }} />
              </Form.Item>
              <Form.Item name="minute" label="分钟" rules={[{ required: true, message: '请选择分钟' }]}>
                <Select options={minuteOptions} style={{ width: 120 }} />
              </Form.Item>
            </Space>
          )}

          {scheduleMode === 'interval' && (
            <Space style={{ width: '100%' }} size={12} align="start">
              <Form.Item
                name="interval_hours"
                label="间隔小时"
                rules={[{ required: true, message: '请输入小时数' }]}
              >
                <InputNumber min={0} max={24} style={{ width: 160 }} />
              </Form.Item>
              <Form.Item
                name="interval_minutes"
                label="间隔分钟"
                rules={[{ required: true, message: '请输入分钟数' }]}
              >
                <InputNumber min={0} max={59} style={{ width: 160 }} />
              </Form.Item>
            </Space>
          )}

          {scheduleMode === 'cron' && (
            <Form.Item
              name="cron"
              label="Cron 表达式"
              tooltip="格式：分钟 小时 日 月 周，例如 0 9 * * * 表示每天 09:00"
              rules={[{ required: true, message: '请输入 Cron 表达式' }]}
            >
              <Input placeholder="0 9 * * *" />
            </Form.Item>
          )}

          <Form.Item name="max_pages" label="最大页数">
            <InputNumber min={1} max={100} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Schedule
