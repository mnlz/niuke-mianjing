const pad = (value: number) => String(value).padStart(2, '0')

export const formatDisplayTime = (value?: string | null) => {
  if (!value) return '时间未知'

  const normalized = value.includes('T') ? value : value.replace(' ', 'T')
  const date = new Date(normalized)

  if (!Number.isNaN(date.getTime())) {
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
  }

  return value.replace('T', ' ').replace(/\.\d+$/, '').slice(0, 16)
}
