import React, { useEffect, useMemo, useState } from 'react'
import { BarChartOutlined, CheckCircleOutlined, ClockCircleOutlined, DatabaseOutlined } from '@ant-design/icons'
import { Card, Col, Empty, List, Progress, Row, Space, Spin, Statistic, Tag, Typography } from 'antd'
import { logApi, scheduleApi } from '@/api'
import type { CrawlLog, ScheduleJob, StatsData } from '@/api/types'
import CrawlProgress from '@/components/CrawlProgress'
import RealtimeEvents from '@/components/RealtimeEvents'

const { Text } = Typography

const statusColor = (status: string) => {
  if (status === 'success') return 'success'
  if (status === 'running') return 'processing'
  if (status === 'failed') return 'error'
  return 'default'
}

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<StatsData | null>(null)
  const [jobs, setJobs] = useState<ScheduleJob[]>([])
  const [logs, setLogs] = useState<CrawlLog[]>([])
  const [loading, setLoading] = useState(true)

  const fetchDashboard = async () => {
    try {
      const [statsData, jobData, logData] = await Promise.all([
        logApi.stats(),
        scheduleApi.list().catch(() => [] as ScheduleJob[]),
        logApi.logs({ limit: 5 }).catch(() => [] as CrawlLog[]),
      ])
      setStats(statsData)
      setJobs(jobData || [])
      setLogs(logData || [])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDashboard()
    const timer = window.setInterval(fetchDashboard, 30000)
    return () => window.clearInterval(timer)
  }, [])

  const maxPostCount = useMemo(
    () => Math.max(...(stats?.post_stats?.map((item) => item.count) || [1])),
    [stats],
  )

  const nextJobs = useMemo(
    () =>
      [...jobs]
        .filter((job) => job.next_run_time)
        .sort((a, b) => String(a.next_run_time).localeCompare(String(b.next_run_time)))
        .slice(0, 4),
    [jobs],
  )

  if (loading) {
    return (
      <div className="page-loading">
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div>
      <div className="page-title">
        <h2>首页</h2>
        <p>查看面经采集概览、方向分布、定时任务执行计划和实时爬取状态。</p>
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} md={6}>
          <Card className="surface-card">
            <Statistic
              title="面经总数"
              value={stats?.total_records ?? 0}
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: '#1677ff', fontWeight: 700 }}
            />
          </Card>
        </Col>
        <Col xs={24} md={6}>
          <Card className="surface-card">
            <Statistic
              title="有效记录"
              value={stats?.active_records ?? 0}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#16a34a', fontWeight: 700 }}
            />
          </Card>
        </Col>
        <Col xs={24} md={6}>
          <Card className="surface-card">
            <Statistic
              title="方向数量"
              value={stats?.post_stats?.length ?? 0}
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#f97316', fontWeight: 700 }}
            />
          </Card>
        </Col>
        <Col xs={24} md={6}>
          <Card className="surface-card">
            <Statistic
              title="定时任务"
              value={jobs.length}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#4f46e5', fontWeight: 700 }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={14}>
          <Card title="各方向面经数量" className="surface-card">
            {stats?.post_stats?.length ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                {stats.post_stats.map((item) => {
                  const percent = Math.round((item.count / maxPostCount) * 100)
                  return (
                    <div key={item.post}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                        <Text strong>{item.post}</Text>
                        <Text type="secondary">{item.count.toLocaleString()} 条</Text>
                      </div>
                      <Progress percent={percent} showInfo={false} strokeColor="#1677ff" />
                    </div>
                  )
                })}
              </div>
            ) : (
              <Empty description="暂无方向统计" />
            )}
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card title="定时任务执行情况" className="surface-card">
            {nextJobs.length ? (
              <List
                size="small"
                dataSource={nextJobs}
                renderItem={(job) => (
                  <List.Item style={{ paddingLeft: 0, paddingRight: 0 }}>
                    <List.Item.Meta
                      title={<Text strong>{job.name}</Text>}
                      description={
                        <Space direction="vertical" size={4}>
                          <Text type="secondary">下次执行：{job.next_run_time}</Text>
                          <Text type="secondary">方向：{job.posts.join('、') || '-'}</Text>
                        </Space>
                      }
                    />
                    <Tag color={job.schedule_type === 'cron' ? 'purple' : 'green'}>
                      {job.schedule_type === 'cron' ? '定时' : '间隔'}
                    </Tag>
                  </List.Item>
                )}
              />
            ) : (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无可执行的定时任务" />
            )}
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <CrawlProgress />
        </Col>
        <Col xs={24} lg={12}>
          <RealtimeEvents />
        </Col>
      </Row>

      <Card title="最近爬取日志" className="surface-card" style={{ marginTop: 16 }}>
        {logs.length ? (
          <List
            size="small"
            dataSource={logs}
            renderItem={(item) => (
              <List.Item style={{ paddingLeft: 0, paddingRight: 0 }}>
                <Space wrap>
                  <Tag color={statusColor(item.status)}>{item.status}</Tag>
                  <Text strong>{item.post}</Text>
                  <Text type="secondary">
                    新增 {item.new_records} · 更新 {item.updated_records} · {item.end_time || item.start_time || '-'}
                  </Text>
                </Space>
              </List.Item>
            )}
          />
        ) : (
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无爬取日志" />
        )}
      </Card>
    </div>
  )
}

export default Dashboard
