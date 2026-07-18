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

export type CoverPreviewData = {
  title: string
  src: string
  hint: string
}

export const computeCoverPreview = (
  customCover: CustomCover | null,
  generatedCover: CustomCover | null,
  article: { cover_base64?: string | null; cover_mime?: string | null } | null,
): CoverPreviewData | null => {
  if (customCover) {
    return {
      title: '自定义封面',
      src: `data:${customCover.mime};base64,${customCover.base64}`,
      hint: customCover.name,
    }
  }
  if (generatedCover) {
    return {
      title: 'AI 封面',
      src: `data:${generatedCover.mime};base64,${generatedCover.base64}`,
      hint: generatedCover.name,
    }
  }
  if (article?.cover_base64) {
    return {
      title: 'AI 封面',
      src: `data:${article.cover_mime || 'image/png'};base64,${article.cover_base64}`,
      hint: '已保存到数据库',
    }
  }
  return null
}
