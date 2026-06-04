import React from 'react'
import { Tag } from 'antd'

interface StatusTagProps {
  status: string
}

const statusMap: Record<string, { color: string; label: string }> = {
  success: { color: 'success', label: '成功' },
  failed: { color: 'error', label: '失败' },
  running: { color: 'processing', label: '运行中' },
  done: { color: 'success', label: '已完成' },
  error: { color: 'error', label: '出错' },
}

const StatusTag: React.FC<StatusTagProps> = ({ status }) => {
  const cfg = statusMap[status] || { color: 'default', label: status }
  return <Tag color={cfg.color}>{cfg.label}</Tag>
}

export default StatusTag
