import React from 'react'
import { Result, Button } from 'antd'

interface State {
  hasError: boolean
  error: Error | null
}

class ErrorBoundary extends React.Component<{ children: React.ReactNode }, State> {
  state: State = { hasError: false, error: null }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('[ErrorBoundary]', error, info.componentStack)
  }

  handleReload = () => {
    this.setState({ hasError: false, error: null })
    window.location.reload()
  }

  handleGoHome = () => {
    this.setState({ hasError: false, error: null })
    const isAdmin = window.location.pathname.startsWith('/admin') || window.location.pathname.startsWith('/quick-crawl') || window.location.pathname.startsWith('/schedule') || window.location.pathname.startsWith('/logs') || window.location.pathname.startsWith('/data') || window.location.pathname.startsWith('/recruitment-jobs') || window.location.pathname.startsWith('/cards') || window.location.pathname.startsWith('/wechat')
    window.location.href = isAdmin ? '/admin' : '/'
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', padding: 24 }}>
          <Result
            status="error"
            title="页面出错了"
            subTitle={this.state.error?.message || '渲染过程中发生未知错误，请尝试刷新页面。'}
            extra={[
              <Button key="reload" type="primary" onClick={this.handleReload}>
                刷新页面
              </Button>,
              <Button key="home" onClick={this.handleGoHome}>
                返回首页
              </Button>,
            ]}
          />
        </div>
      )
    }
    return this.props.children
  }
}

export default ErrorBoundary
