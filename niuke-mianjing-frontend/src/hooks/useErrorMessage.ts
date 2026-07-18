import { message } from 'antd'

/**
 * 从任意 unknown 错误中提取可读消息，统一 (e as Error).message || '...' 模式。
 */
export function getErrorMessage(e: unknown, fallback = '操作失败，请稍后重试'): string {
  if (e instanceof Error) return e.message || fallback
  if (typeof e === 'string') return e || fallback
  return fallback
}

/**
 * 返回一个 message.error 包装函数，自动调用 getErrorMessage 提取消息。
 *
 * @example
 * const errMsg = useErrorMessage()
 * try { ... } catch (e) { errMsg(e, '保存失败') }
 */
export function useErrorMessage() {
  return (e: unknown, fallback?: string) => {
    message.error(getErrorMessage(e, fallback))
  }
}
