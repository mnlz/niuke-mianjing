import React, { useState } from 'react'
import { Button, Card, Input, message, Segmented } from 'antd'
import { LockOutlined, MailOutlined } from '@ant-design/icons'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { authApi } from '@/api'
import { setUserSession } from '@/utils/auth'
import './style.css'

const UserLogin: React.FC = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async () => {
    if (!email.includes('@')) return message.warning('请输入有效邮箱')
    if (password.length < 8) return message.warning('密码至少 8 位')
    try {
      setLoading(true)
      const session = mode === 'register'
        ? await authApi.userRegister(email.trim(), password)
        : await authApi.userLogin(email.trim(), password)
      setUserSession(session)
      message.success(mode === 'register' ? '注册成功' : '登录成功')
      const from = searchParams.get('from') || '/'
      navigate(from.startsWith('/') && !from.startsWith('//') ? from : '/', { replace: true })
    } catch (error: unknown) {
      message.error((error as Error).message || '登录失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="user-login-page">
      <Card className="user-login-card">
        <button className="user-login-brand" onClick={() => navigate('/')}><img src="/offerlens.svg" alt="OfferLens" /><b>OfferLens</b></button>
        <h1>{mode === 'login' ? '登录后继续探索' : '创建你的求职档案'}</h1>
        <p>收藏面经、生成 AI 报告，并在不同设备查看自己的准备进度。</p>
        <Segmented block value={mode} onChange={(value) => setMode(value as 'login' | 'register')} options={[{ label: '登录', value: 'login' }, { label: '注册', value: 'register' }]} />
        <Input size="large" prefix={<MailOutlined />} value={email} onChange={(event) => setEmail(event.target.value)} placeholder="邮箱" />
        <Input.Password size="large" prefix={<LockOutlined />} value={password} onChange={(event) => setPassword(event.target.value)} onPressEnter={submit} placeholder="密码，至少 8 位" />
        <Button block size="large" type="primary" loading={loading} onClick={submit}>{mode === 'login' ? '登录' : '注册并登录'}</Button>
        <small>注册即表示你同意仅将账号用于保存求职数据。当前版本不发送验证邮件。</small>
      </Card>
    </div>
  )
}

export default UserLogin
