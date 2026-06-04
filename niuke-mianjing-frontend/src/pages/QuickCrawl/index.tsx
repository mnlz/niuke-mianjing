import React, { useEffect, useState } from 'react'
import {
  Button,
  Card,
  Col,
  Form,
  InputNumber,
  message,
  Modal,
  Row,
  Select,
  Slider,
  Space,
  Spin,
  Typography,
} from 'antd'
import { DownloadOutlined, ThunderboltOutlined } from '@ant-design/icons'
import { logApi, quickCrawlApi } from '@/api'
import type { ExportMdRequest, FilterOptions, JobTreeItem } from '@/api/types'
import CrawlProgress from '@/components/CrawlProgress'
import RealtimeEvents from '@/components/RealtimeEvents'
import { useCrawlStore } from '@/store/crawlStore'

const { Text } = Typography

const groupOptions: Array<{ label: string; value: ExportMdRequest['group_by'] | '' }> = [
  { label: '不分组', value: '' },
  { label: '按公司分组', value: 'company' },
  { label: '按岗位方向分组', value: 'post' },
]

const QuickCrawl: React.FC = () => {
  const [postOptions, setPostOptions] = useState<{ label: string; value: string }[]>([])
  const [companyOptions, setCompanyOptions] = useState<{ label: string; value: string }[]>([])
  const [selectedPosts, setSelectedPosts] = useState<string[]>([])
  const [maxPages, setMaxPages] = useState(5)
  const [crawling, setCrawling] = useState(false)
  const [loadingPosts, setLoadingPosts] = useState(true)
  const [exporting, setExporting] = useState(false)
  const [exportModalOpen, setExportModalOpen] = useState(false)
  const [exportForm] = Form.useForm()
  const { progresses } = useCrawlStore()
  const isRunning = Object.values(progresses).some((p) => p.status === 'running')

  useEffect(() => {
    const loadOptions = async () => {
      try {
        const [postsData, filters] = await Promise.all([
          quickCrawlApi.getPosts(),
          logApi.filters().catch(() => ({ posts: [], companies: [] } as FilterOptions)),
        ])

        const tree: JobTreeItem[] = postsData.tree || []
        const options = tree.flatMap((top) =>
          top.children.map((child) => ({ label: `${top.name} / ${child.name}`, value: child.name })),
        )
        setPostOptions(options)
        setCompanyOptions((filters.companies || []).map((company) => ({ label: company, value: company })))
        if (options.length > 0) setSelectedPosts([options[0].value])
      } catch {
        message.error('加载爬取方向失败')
      } finally {
        setLoadingPosts(false)
      }
    }

    loadOptions()
  }, [])

  const handleCrawl = async () => {
    if (selectedPosts.length === 0) {
      message.warning('请至少选择一个爬取方向')
      return
    }

    setCrawling(true)
    try {
      await quickCrawlApi.start({ posts: selectedPosts, max_pages: maxPages })
      message.success('快速爬取任务已启动')
    } catch (e: unknown) {
      message.error((e as Error).message || '启动爬取失败')
    } finally {
      setCrawling(false)
    }
  }

  const handleExport = async () => {
    try {
      const values = await exportForm.validateFields()
      setExporting(true)
      const req: ExportMdRequest = { limit: values.limit || 100 }
      if (values.post) req.post = values.post
      if (values.company) req.company = values.company
      if (values.group_by) req.group_by = values.group_by
      await quickCrawlApi.exportMd(req)
      message.success('Markdown 已下载')
      setExportModalOpen(false)
      exportForm.resetFields()
    } catch (e: unknown) {
      if (e instanceof Error) message.error(e.message || '导出失败')
    } finally {
      setExporting(false)
    }
  }

  return (
    <div>
      <div className="page-title">
        <h2>快速爬取</h2>
        <p>选择岗位方向和页数，直接使用公开接口采集最新面经，无需登录凭证。</p>
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={14}>
          <Card className="surface-card" title="启动爬取">
            <Space direction="vertical" size={22} style={{ width: '100%' }}>
              <div>
                <Text strong>爬取方向</Text>
                <Spin spinning={loadingPosts}>
                  <Select
                    mode="multiple"
                    value={selectedPosts}
                    onChange={setSelectedPosts}
                    options={postOptions}
                    style={{ width: '100%', marginTop: 8 }}
                    placeholder="选择方向"
                    maxTagCount="responsive"
                    showSearch
                    optionFilterProp="label"
                  />
                </Spin>
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text strong>爬取页数</Text>
                  <Text type="secondary">{maxPages} 页</Text>
                </div>
                <Slider
                  min={1}
                  max={50}
                  value={maxPages}
                  onChange={setMaxPages}
                  marks={{ 1: '1', 10: '10', 25: '25', 50: '50' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 16 }}>
                <Text type="secondary">
                  当前爬取接口只按岗位方向和页号请求，预计每个方向请求 {maxPages} 页。
                </Text>
                <Button
                  type="primary"
                  icon={<ThunderboltOutlined />}
                  onClick={handleCrawl}
                  loading={crawling}
                  disabled={isRunning}
                  size="large"
                >
                  {isRunning ? '爬取中...' : '开始爬取'}
                </Button>
              </div>
            </Space>
          </Card>
        </Col>

        <Col xs={24} lg={10}>
          <Card className="surface-card" title="Markdown 导出">
            <Text type="secondary">
              将数据库中的面经按方向、公司筛选后导出为 Markdown，支持按公司或岗位方向生成分组章节。
            </Text>
            <Button
              icon={<DownloadOutlined />}
              onClick={() => setExportModalOpen(true)}
              size="large"
              block
              style={{ marginTop: 18 }}
            >
              导出 Markdown
            </Button>
          </Card>
          <div style={{ marginTop: 16 }}>
            <RealtimeEvents />
          </div>
        </Col>
      </Row>

      <div style={{ marginTop: 16 }}>
        <CrawlProgress />
      </div>

      <Modal
        title="导出 Markdown"
        open={exportModalOpen}
        onOk={handleExport}
        onCancel={() => {
          setExportModalOpen(false)
          exportForm.resetFields()
        }}
        okText="导出"
        cancelText="取消"
        confirmLoading={exporting}
      >
        <Form
          form={exportForm}
          layout="vertical"
          style={{ marginTop: 16 }}
          initialValues={{ limit: 100, group_by: '' }}
        >
          <Form.Item name="post" label="岗位方向">
            <Select
              options={[{ label: '全部方向', value: '' }, ...postOptions]}
              placeholder="选择方向"
              allowClear
              showSearch
              optionFilterProp="label"
            />
          </Form.Item>
          <Form.Item name="company" label="公司">
            <Select
              options={[{ label: '全部公司', value: '' }, ...companyOptions]}
              placeholder="选择公司"
              allowClear
              showSearch
              optionFilterProp="label"
            />
          </Form.Item>
          <Form.Item name="group_by" label="导出分组">
            <Select options={groupOptions} />
          </Form.Item>
          <Form.Item name="limit" label="最大导出条数" rules={[{ required: true, message: '请输入导出条数' }]}>
            <InputNumber min={1} max={1000} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default QuickCrawl
