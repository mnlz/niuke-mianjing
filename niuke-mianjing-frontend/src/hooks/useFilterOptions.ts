import { useEffect, useMemo, useState } from 'react'
import { message } from 'antd'
import { logApi } from '@/api'
import type { FilterOptions } from '@/api/types'

const EMPTY: FilterOptions = { posts: [], companies: [] }

/**
 * 加载岗位方向和公司筛选项，并提供两套 Select options（带"全部"占位）。
 * 失败时仅 warning 一次，组件仍可继续渲染空筛选项。
 *
 * @example
 * const { postOptions, companyOptions } = useFilterOptions()
 */
export function useFilterOptions() {
  const [filterOptions, setFilterOptions] = useState<FilterOptions>(EMPTY)

  useEffect(() => {
    logApi
      .filters()
      .then((data) => setFilterOptions(data || EMPTY))
      .catch(() => message.warning('筛选项加载失败，可继续查看已有数据'))
  }, [])

  const postOptions = useMemo(
    () => [{ label: '全部方向', value: '' }, ...filterOptions.posts.map((p) => ({ label: p, value: p }))],
    [filterOptions.posts],
  )

  const companyOptions = useMemo(
    () => [{ label: '全部公司', value: '' }, ...filterOptions.companies.map((c) => ({ label: c, value: c }))],
    [filterOptions.companies],
  )

  return { filterOptions, postOptions, companyOptions }
}
