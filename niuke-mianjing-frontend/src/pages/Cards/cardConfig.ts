import type { CardTheme } from '@/api/types'

export type ThemeConfig = {
  pageBg: string
  accent: string
  accentSoft: string
  heading: string
  text: string
  muted: string
  tableHead: string
}

export type CardSizePresetKey = 'xhs_3_4' | 'xhs_square' | 'wechat_article' | 'wechat_cover' | 'md2card'

export type CardSizePreset = {
  label: string
  width: number
  height: number
  exportWidth: number
  exportHeight: number
  description: string
}

export const CARD_VERTICAL_CHROME = 96

export const cardSizePresets: Record<CardSizePresetKey, CardSizePreset> = {
  xhs_3_4: {
    label: '小红书 3:4',
    width: 540,
    height: 720,
    exportWidth: 1080,
    exportHeight: 1440,
    description: '图文笔记常用竖版',
  },
  xhs_square: {
    label: '小红书 1:1',
    width: 540,
    height: 540,
    exportWidth: 1080,
    exportHeight: 1080,
    description: '方图笔记/封面',
  },
  wechat_article: {
    label: '微信正文图',
    width: 450,
    height: 600,
    exportWidth: 900,
    exportHeight: 1200,
    description: '公众号正文/贴图',
  },
  wechat_cover: {
    label: '公众号封面',
    width: 450,
    height: 192,
    exportWidth: 900,
    exportHeight: 384,
    description: '首图封面横图',
  },
  md2card: {
    label: 'MD2Card 竖卡',
    width: 440,
    height: 586,
    exportWidth: 880,
    exportHeight: 1172,
    description: '接近原预览尺寸',
  },
}

export const cardSizeOptions = Object.entries(cardSizePresets).map(([value, preset]) => ({
  label: `${preset.label} · ${preset.exportWidth}×${preset.exportHeight}`,
  value: value as CardSizePresetKey,
}))

export const themeOptions: Array<{ label: string; value: CardTheme }> = [
  { label: '小红书清新', value: 'xiaohongshu' },
  { label: '字节蓝', value: 'bytedance' },
  { label: '阿里橙', value: 'alibaba' },
  { label: '极简黑白', value: 'minimal' },
  { label: '商务简报', value: 'business' },
]

export const themes: Record<CardTheme, ThemeConfig> = {
  xiaohongshu: {
    pageBg: '#ffffff',
    accent: '#ffb000',
    accentSoft: '#fff1bf',
    heading: '#262626',
    text: '#2f2f2f',
    muted: '#8c8c8c',
    tableHead: '#fff2bf',
  },
  bytedance: {
    pageBg: '#ffffff',
    accent: '#1677ff',
    accentSoft: '#eaf3ff',
    heading: '#102033',
    text: '#24364b',
    muted: '#64748b',
    tableHead: '#eaf3ff',
  },
  alibaba: {
    pageBg: '#ffffff',
    accent: '#ff7a00',
    accentSoft: '#fff0dc',
    heading: '#332112',
    text: '#3d3329',
    muted: '#8a6b4a',
    tableHead: '#ffe5c2',
  },
  minimal: {
    pageBg: '#ffffff',
    accent: '#111827',
    accentSoft: '#f3f4f6',
    heading: '#111827',
    text: '#1f2937',
    muted: '#6b7280',
    tableHead: '#f3f4f6',
  },
  business: {
    pageBg: '#ffffff',
    accent: '#4f46e5',
    accentSoft: '#eef2ff',
    heading: '#172033',
    text: '#334155',
    muted: '#64748b',
    tableHead: '#eef2ff',
  },
}

export const defaultMarkdown = '# 面经卡片\n\n选择一条面经，或在这里粘贴 Markdown 内容。'
