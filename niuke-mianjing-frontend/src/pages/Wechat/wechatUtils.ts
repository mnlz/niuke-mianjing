export type CustomCover = {
  base64: string
  mime: string
  name: string
}

export type StreamEvent = {
  type?: string
  title?: string
  delta?: string
  html?: string
  markdown?: string
  message?: string
  digest?: string
}

export const readImageAsCover = (file: File): Promise<CustomCover> =>
  new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const value = String(reader.result || '')
      const match = value.match(/^data:(image\/[^;]+);base64,(.+)$/)
      if (!match) {
        reject(new Error('封面图片读取失败'))
        return
      }
      resolve({ mime: match[1], base64: match[2], name: file.name })
    }
    reader.onerror = () => reject(new Error('封面图片读取失败'))
    reader.readAsDataURL(file)
  })

export const parseSseChunk = (buffer: string) => {
  const events: StreamEvent[] = []
  const parts = buffer.split('\n\n')
  const rest = parts.pop() || ''
  parts.forEach((part) => {
    const line = part
      .split('\n')
      .find((item) => item.startsWith('data:'))
      ?.slice(5)
      .trim()
    if (!line) return
    try {
      events.push(JSON.parse(line))
    } catch {
      // Ignore an incomplete or malformed stream event.
    }
  })
  return { events, rest }
}
