import React, { useEffect, useState } from 'react'
import { Button, Space } from 'antd'
import { LoginOutlined, LogoutOutlined, UserOutlined } from '@ant-design/icons'
import { useLocation, useNavigate } from 'react-router-dom'
import { authApi } from '@/api'
import { clearUserSession, getUserSession, setUserSession, USER_SESSION_CHANGED_EVENT, userLoginPath } from '@/utils/auth'

const UserSessionButton: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const [session, setSession] = useState(getUserSession())

  useEffect(() => {
    const sync = () => setSession(getUserSession())
    window.addEventListener(USER_SESSION_CHANGED_EVENT, sync)
    const current = getUserSession()
    if (current) {
      authApi.userMe().then((profile) => setUserSession({ ...current, ...profile })).catch(() => undefined)
    }
    return () => window.removeEventListener(USER_SESSION_CHANGED_EVENT, sync)
  }, [])

  if (!session) {
    return <Button className="user-session-entry" type="text" icon={<LoginOutlined />} onClick={() => navigate(userLoginPath(`${location.pathname}${location.search}`))}>登录</Button>
  }
  return (
    <Space className="user-session-actions" size={0}>
      <Button type="text" icon={<UserOutlined />} title={session.email}>{session.display_name}</Button>
      <Button type="text" icon={<LogoutOutlined />} onClick={() => { clearUserSession(); navigate('/') }}>退出</Button>
    </Space>
  )
}

export default UserSessionButton
