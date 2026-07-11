import React, { useMemo } from 'react'
import { Empty, Skeleton, Tag } from 'antd'
import './style.css'

interface Props {
  data: Array<{ post: string; count: number }> | undefined
  loading?: boolean
}

const TOP_N = 10
const CHART_HEIGHT = 320

const PostStatsChart: React.FC<Props> = ({ data, loading }) => {
  const { rows, total, topTags } = useMemo(() => {
    const sorted = data ? [...data].sort((a, b) => b.count - a.count) : []
    const total = sorted.reduce((sum, item) => sum + item.count, 0)

    const topThree = sorted.slice(0, 3)
    const rest = sorted.slice(TOP_N)
    const restTotal = rest.reduce((sum, item) => sum + item.count, 0)

    const visible = sorted.slice(0, TOP_N).map((item, index) => ({
      ...item,
      rank: index + 1,
      percent: total > 0 ? (item.count / total) * 100 : 0,
      tier: index < 3 ? 'top' : 'normal',
    }))

    if (rest.length > 0) {
      visible.push({
        post: `其他 ${rest.length} 项`,
        count: restTotal,
        rank: visible.length + 1,
        percent: total > 0 ? (restTotal / total) * 100 : 0,
        tier: 'rest',
      })
    }

    return {
      rows: visible,
      total,
      topTags: topThree,
    }
  }, [data])

  if (loading) return <Skeleton.Button active block style={{ height: CHART_HEIGHT }} />
  if (!rows.length) return <Empty description="暂无方向统计" />

  const maxCount = rows[0].count || 1

  return (
    <div className="post-stats-chart">
      {topTags.length > 0 && (
        <div className="post-stats-chart__summary">
          <span className="post-stats-chart__total">
            共 <strong>{total}</strong> 篇 · <strong>{data?.length ?? 0}</strong> 个方向
          </span>
          <div className="post-stats-chart__tags">
            {topTags.map((item, index) => (
              <Tag key={item.post} className={`post-stats-chart__tag post-stats-chart__tag--${index}`}>
                {item.post} {item.count}
              </Tag>
            ))}
          </div>
        </div>
      )}

      <div
        className="post-stats-chart__body"
        style={{ maxHeight: CHART_HEIGHT, overflowY: rows.length > 8 ? 'auto' : 'hidden' }}
      >
        {rows.map((row) => {
          const widthPercent = Math.max(2, (row.count / maxCount) * 100)
          return (
            <div key={`${row.post}-${row.rank}`} className={`post-stats-chart__row post-stats-chart__row--${row.tier}`}>
              <span className="post-stats-chart__label" title={row.post}>
                {row.post}
              </span>
              <div className="post-stats-chart__track">
                <div
                  className="post-stats-chart__bar"
                  style={{ width: `${widthPercent}%` }}
                />
              </div>
              <span className="post-stats-chart__value">
                <strong>{row.count}</strong>
                <em>{row.percent.toFixed(1)}%</em>
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default PostStatsChart
