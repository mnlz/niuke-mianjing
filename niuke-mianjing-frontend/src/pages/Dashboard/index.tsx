import React, { useEffect, useMemo, useState } from 'react'
import { BarChartOutlined, CheckCircleOutlined, ClockCircleOutlined, DatabaseOutlined } from '@ant-design/icons'
import { Card, Col, Empty, List, Row, Space, Spin, Statistic, Tag, Typography } from 'antd'
import { Pie } from '@ant-design/charts'
import { logApi, scheduleApi } from '@/api'
import type { CrawlLog, ScheduleJob, StatsData } from '@/api/types'
import CrawlProgress from '@/components/CrawlProgress'
import PostStatsChart from '@/components/PostStatsChart'
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

  const nextJobs = useMemo(
    () =>
      [...jobs]
        .filter((job) => job.next_run_time)
        .sort((a, b) => String(a.next_run_time).localeCompare(String(b.next_run_time)))
        .slice(0, 4),
    [jobs],
  )

  const activeRate = useMemo(() => {
    const total = stats?.total_records ?? 0
    const active = stats?.active_records ?? 0
    if (total === 0) return 0
    return Math.round((active / total) * 100)
  }, [stats])

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
            <PostStatsChart data={stats?.post_stats} loading={false} />
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card title="面经有效率" className="surface-card">
            {stats ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8, minHeight: 320 }}>
                <Pie
                  data={[
                    { type: '有效', value: stats.active_records ?? 0 },
                    { type: '待清理', value: Math.max(0, (stats.total_records ?? 0) - (stats.active_records ?? 0)) },
                  ]}
                  angleField="value"
                  colorField="type"
                  color={['#1d1d1f', '#f2f2f7']}
                  innerRadius={0.78}
                  label={false}
                  legend={false}
                  tooltip={{
                    title: (d: { type: string }) => d.type,
                    items: [{ field: 'value', name: '数量' }],
                  }}
                  style={{ height: 220 }}
                />
                <Text style={{ fontSize: 28, fontWeight: 600, color: '#1d1d1f', marginTop: -16 }}>
                  {activeRate}%
                </Text>
                <Text style={{ fontSize: 13, color: '#86868b' }}>有效面经占总数的比例</Text>
              </div>
            ) : (
              <Empty description="暂无统计数据" />
            )}
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
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
        <Col xs={24} lg={12}>
          <Card title="最近爬取日志" className="surface-card">
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
    </div>
  )
}

export default Dashboard
