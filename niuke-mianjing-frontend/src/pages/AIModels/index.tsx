import React, { useEffect, useState } from 'react'
import { Button, Card, Form, Input, message, Modal, Popconfirm, Space, Switch, Table, Tag } from 'antd'
import { ApiOutlined, DeleteOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons'
import { recruitmentApi } from '@/api'
import type { AIModelAdmin, AIModelInput } from '@/api/types'
import './style.css'

const AIModels: React.FC = () => {
  const [models, setModels] = useState<AIModelAdmin[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState<number | null>(null)
  const [editing, setEditing] = useState<AIModelAdmin | null>(null)
  const [open, setOpen] = useState(false)
  const [form] = Form.useForm<AIModelInput>()

  const load = async () => {
    setLoading(true)
    try { setModels(await recruitmentApi.adminAIModels()) }
    catch (error) { message.error((error as Error).message) }
    finally { setLoading(false) }
  }

  useEffect(() => { void load() }, [])

  const edit = (model?: AIModelAdmin) => {
    setEditing(model || null)
    form.resetFields()
    form.setFieldsValue(model ? { ...model, api_key: '' } : { channel_name: '默认线路', enabled: true, is_default: false })
    setOpen(true)
  }

  const close = () => {
    setOpen(false)
    setEditing(null)
    form.resetFields()
  }

  const save = async () => {
    const values = await form.validateFields()
    setSaving(true)
    try {
      setModels(editing ? await recruitmentApi.updateAIModel(editing.id, values) : await recruitmentApi.createAIModel(values))
      setOpen(false)
      form.resetFields()
      message.success('模型配置已保存')
    } catch (error) { message.error((error as Error).message) }
    finally { setSaving(false) }
  }

  const test = async (modelId: number) => {
    setTesting(modelId)
    try {
      const result = await recruitmentApi.testAIModel(modelId)
      message.success(`连接成功，耗时 ${result.elapsed_ms} ms`)
    } catch (error) { message.error((error as Error).message) }
    finally { setTesting(null) }
  }

  const remove = async (modelId: number) => {
    try { await recruitmentApi.deleteAIModel(modelId); await load(); message.success('模型配置已删除') }
    catch (error) { message.error((error as Error).message) }
  }

  return <div className="ai-model-admin-page">
    <div className="page-header">
      <div><h1>AI 模型</h1><p>配置 OpenAI 兼容模型，密钥仅在后端加密保存。</p></div>
      <Button type="primary" icon={<PlusOutlined />} onClick={() => edit()}>新增模型</Button>
    </div>
    <Card>
      <Table rowKey="id" loading={loading} dataSource={models} pagination={false} scroll={{ x: 1060 }} columns={[
        { title: 'ID', dataIndex: 'id', width: 70 },
        { title: '模型', dataIndex: 'model', width: 140, render: (value, row) => <Space><b>{value}</b>{row.is_default && <Tag color="blue">默认</Tag>}</Space> },
        { title: '渠道', dataIndex: 'channel_name', width: 120 },
        { title: 'Endpoint', dataIndex: 'endpoint', width: 360, render: (value) => <span className="ai-model-endpoint">{value}</span> },
        { title: '密钥', dataIndex: 'api_key_masked', width: 150 },
        { title: '来源', dataIndex: 'source', width: 100, render: (value) => <Tag>{value === 'database' ? '数据库' : '环境变量'}</Tag> },
        { title: '状态', dataIndex: 'enabled', width: 80, render: (value) => <Tag color={value ? 'green' : 'default'}>{value ? '启用' : '停用'}</Tag> },
        { title: '操作', width: 230, render: (_, row) => <Space>
          <Button size="small" icon={<ApiOutlined />} loading={testing === row.id} onClick={() => test(row.id)}>连接测试</Button>
          <Button size="small" icon={<EditOutlined />} onClick={() => edit(row)}>编辑</Button>
          <Popconfirm title="删除模型配置？" onConfirm={() => remove(row.id)} disabled={row.source !== 'database'}>
            <Button size="small" danger icon={<DeleteOutlined />} disabled={row.source !== 'database'} />
          </Popconfirm>
        </Space> },
      ]} />
    </Card>
    <Modal title={editing ? '编辑模型' : '新增模型'} open={open} confirmLoading={saving} onOk={save} onCancel={close} forceRender>
      <Form form={form} layout="vertical" preserve={false}>
        <Form.Item name="model" label="真实模型名" rules={[{ required: true }]}><Input placeholder="例如 deepseek-chat" /></Form.Item>
        <Form.Item name="channel_name" label="渠道名称" rules={[{ required: true }]}><Input placeholder="例如 主线路" /></Form.Item>
        <Form.Item name="endpoint" label="Endpoint" rules={[{ required: true }, { type: 'url' }]}><Input placeholder="https://api.example.com/v1" /></Form.Item>
        <Form.Item name="api_key" label="API Key" extra={editing ? '留空则保留当前密钥' : undefined}><Input.Password placeholder={editing ? '留空保留当前密钥' : 'sk-...'} /></Form.Item>
        <Form.Item name="description" label="说明"><Input placeholder="展示给用户的模型说明" /></Form.Item>
        <Space size="large">
          <Form.Item name="enabled" label="启用" valuePropName="checked"><Switch /></Form.Item>
          <Form.Item name="is_default" label="设为默认" valuePropName="checked"><Switch /></Form.Item>
        </Space>
      </Form>
    </Modal>
  </div>
}

export default AIModels
