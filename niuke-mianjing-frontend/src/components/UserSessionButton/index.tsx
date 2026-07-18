import React, { useEffect, useState } from 'react'
import { Button, Dropdown } from 'antd'
import { LoginOutlined, LogoutOutlined } from '@ant-design/icons'
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
    <Dropdown trigger={['click']} menu={{ items: [{ key: 'logout', icon: <LogoutOutlined />, label: '退出登录', onClick: () => { clearUserSession(); navigate('/') } }] }}>
      <Button className="ai-account-pill" type="text" title={session.email}><span className="ai-account-avatar">{session.display_name.slice(0, 1)}</span>{session.display_name}</Button>
    </Dropdown>
  )
}

export default UserSessionButton
