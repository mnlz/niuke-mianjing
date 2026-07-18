import { useCallback, useState } from 'react'
import { message } from 'antd'
import { logApi } from '@/api'
import type { NiukeRecord } from '@/api/types'
import { getErrorMessage } from './useErrorMessage'

interface UseRecordsOptions {
  /** 单页最大条数，默认 100（列表场景）；分页场景传 pageSize */
  pageSize?: number
  /** 是否启用分页，默认 false（不分页场景使用） */
  paged?: boolean
  /** 加载失败时的提示文案 */
  errorMessage?: string
  roleGroup?: string
  roleFamily?: string
}

interface UseRecordsResult {
  records: NiukeRecord[]
  loading: boolean
  pagination: { current: number; pageSize: number; total: number }
  reload: (page?: number, pageSize?: number) => Promise<void>
  setRecords: React.Dispatch<React.SetStateAction<NiukeRecord[]>>
}

/**
 * 统一封装 logApi.records 调用，覆盖列表式（Wechat/Cards）和分页式（Data/PublicInterviews）两种模式。
 * 本 Hook 不监听 postFilter/companyFilter 变化，由调用方在 useEffect 中触发 reload。
 *
 * @example 列表场景
 * const { records, loading, reload } = useRecords(postFilter, companyFilter, { pageSize: 100 })
 * useEffect(() => { reload() }, [postFilter, companyFilter])
 *
 * @example 分页场景
 * const { records, loading, pagination, reload } = useRecords(postFilter, companyFilter, { paged: true, pageSize: 20 })
 */
export function useRecords(
  postFilter: string,
  companyFilter: string,
  options: UseRecordsOptions = {},
): UseRecordsResult {
  const { pageSize: defaultPageSize = 100, paged = false, errorMessage, roleGroup, roleFamily } = options

  const [records, setRecords] = useState<NiukeRecord[]>([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({ current: 1, pageSize: defaultPageSize, total: 0 })

  const reload = useCallback(
    async (page = 1, pageSize?: number) => {
      const size = pageSize ?? pagination.pageSize
      try {
        setLoading(true)
        const offset = (page - 1) * size
        const data = await logApi.records({
          post: postFilter || undefined,
          company: companyFilter || undefined,
          role_group: roleGroup || undefined,
          role_family: roleFamily || undefined,
          limit: size,
          offset,
        })
        setRecords(data?.data || [])
        if (paged) {
          setPagination((prev) => ({
            ...prev,
            current: page,
            pageSize: size,
            total: data?.total || 0,
          }))
        }
      } catch (e: unknown) {
        if (errorMessage) {
          message.error(getErrorMessage(e, errorMessage))
        } else {
          message.warning('面经列表加载失败')
        }
      } finally {
        setLoading(false)
      }
    },
    [postFilter, companyFilter, roleGroup, roleFamily, paged, errorMessage, pagination.pageSize],
  )

  return { records, loading, pagination, reload, setRecords }
}
