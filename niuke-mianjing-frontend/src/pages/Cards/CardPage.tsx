import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

import { CARD_VERTICAL_CHROME, type CardSizePreset, type ThemeConfig } from './cardConfig'

type CardPageProps = {
  content: string
  page: number
  total: number
  theme: ThemeConfig
  preset: CardSizePreset
  innerRef: (node: HTMLDivElement | null) => void
}

const CardPage: React.FC<CardPageProps> = ({ content, page, total, theme, preset, innerRef }) => (
  <div
    ref={innerRef}
    className="md2-card-page"
    style={{
      width: preset.width,
      height: preset.height,
      background: theme.pageBg,
      color: theme.text,
      padding: '28px 32px',
      boxShadow: '0 18px 46px rgba(15, 23, 42, 0.10)',
      overflow: 'hidden',
      position: 'relative',
    }}
  >
    <div className="md2-card-topbar" style={{ color: theme.accent }}>
      <span>‹ 备忘录</span>
      <span>分享 · · ·</span>
    </div>
    <div
      className="md2-card-content"
      style={
        {
          '--accent': theme.accent,
          '--accent-soft': theme.accentSoft,
          '--table-head': theme.tableHead,
          '--heading': theme.heading,
          '--text': theme.text,
          '--muted': theme.muted,
          height: Math.max(120, preset.height - CARD_VERTICAL_CHROME),
        } as React.CSSProperties
      }
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
    {total > 1 && (
      <div className="md2-page-no" style={{ color: theme.muted }}>
        {page + 1}/{total}
      </div>
    )}
  </div>
)

export default CardPage
