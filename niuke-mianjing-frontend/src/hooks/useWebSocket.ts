import { useEffect, useRef, useCallback } from 'react'
import { useCrawlStore } from '@/store/crawlStore'
import type { WSMessage } from '@/api/types'
import { getAdminToken } from '@/utils/auth'

function getWsUrl() {
  const loc = window.location
  const proto = loc.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${loc.host}/api/ws/crawl?token=${encodeURIComponent(getAdminToken())}`
}

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>()
  const { setConnected, handleMessage } = useCrawlStore()

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const ws = new WebSocket(getWsUrl())

    ws.onopen = () => {
      setConnected(true)
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current)
        reconnectTimer.current = undefined
      }
    }

    ws.onmessage = (event) => {
      try {
        const msg: WSMessage = JSON.parse(event.data)
        handleMessage(msg)
      } catch {
        // ignore
      }
    }

    ws.onclose = () => {
      setConnected(false)
      reconnectTimer.current = setTimeout(() => connect(), 3000)
    }

    ws.onerror = () => {
      ws.close()
    }

    wsRef.current = ws
  }, [setConnected, handleMessage])

  const disconnect = useCallback(() => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current)
      reconnectTimer.current = undefined
    }
    wsRef.current?.close()
    wsRef.current = null
    setConnected(false)
  }, [setConnected])

  useEffect(() => {
    connect()
    return () => disconnect()
  }, [connect, disconnect])

  return { connect, disconnect }
}
