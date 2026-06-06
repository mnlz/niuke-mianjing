import React, { useState } from 'react'
import { Button, Card, Input, message, Typography } from 'antd'
import { LockOutlined } from '@ant-design/icons'
import { useLocation, useNavigate } from 'react-router-dom'

import { authApi } from '@/api'
import { setAdminToken } from '@/utils/auth'


const { Paragraph, Title } = Typography

const AdminLogin: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const [apiKey, setApiKey] = useState('')
  const [loading, setLoading] = useState(false)

  const login = async () => {
    if (!apiKey.trim()) {
      message.warning('请输入管理员密钥')
      return
    }
    try {
      setLoading(true)
      const session = await authApi.login(apiKey.trim())
      setAdminToken(session.token)
      await authApi.me()
      message.success('登录成功')
      const from = (location.state as { from?: string } | null)?.from || '/admin'
      navigate(from, { replace: true })
    } catch (error) {
      message.error((error as Error).message || '登录失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="admin-login-page">
      <Card className="admin-login-card">
        <img src="/offerlens.svg" alt="OfferLens" />
        <Title level={2}>OfferLens 管理后台</Title>
        <Paragraph type="secondary">爬取、定时任务、AI 内容生成与公众号发布仅对管理员开放。</Paragraph>
        <Input.Password
          size="large"
          prefix={<LockOutlined />}
          value={apiKey}
          onChange={(event) => setApiKey(event.target.value)}
          onPressEnter={login}
          placeholder="请输入 .env 中配置的 API_KEY"
        />
        <Button block size="large" type="primary" loading={loading} onClick={login}>
          登录后台
        </Button>
        <Button block type="text" onClick={() => navigate('/')}>
          返回公开首页
        </Button>
      </Card>
    </div>
  )
}

export default AdminLogin
