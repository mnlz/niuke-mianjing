export const downloadText = (filename: string, content: string, type: string) => {
  const blob = new Blob([content], { type })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  document.body.removeChild(anchor)
  URL.revokeObjectURL(url)
}

export const safeName = (value: string) => value.replace(/[\\/:*?"<>|]/g, '_').slice(0, 48)

export const parseDataUrlImage = (dataUrl: string) => {
  const match = dataUrl.match(/^data:(image\/[a-zA-Z0-9.+-]+);base64,(.+)$/)
  if (!match) throw new Error('卡片图片生成失败，请重试')
  return { mime: match[1], base64: match[2] }
}
