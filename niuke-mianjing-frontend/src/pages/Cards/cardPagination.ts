import { CARD_VERTICAL_CHROME, defaultMarkdown, type CardSizePreset } from './cardConfig'

const normalizeMarkdown = (value: string) =>
  value
    .replace(/\r\n/g, '\n')
    .replace(/^(\d+[.)、])(?=\S)/gm, '$1 ')
    .trim()

const splitBlocks = (value: string) => {
  const lines = normalizeMarkdown(value).split('\n')
  const blocks: string[] = []
  let i = 0

  const pushParagraphChunks = (paragraph: string[]) => {
    for (let start = 0; start < paragraph.length; start += 4) {
      blocks.push(paragraph.slice(start, start + 4).join('\n'))
    }
  }

  while (i < lines.length) {
    const line = lines[i]
    if (!line.trim()) {
      i += 1
      continue
    }
    if (/^\|/.test(line.trim())) {
      const table: string[] = []
      while (i < lines.length && /^\|/.test(lines[i].trim())) {
        table.push(lines[i])
        i += 1
      }
      blocks.push(table.join('\n'))
      continue
    }
    if (/^#{1,6}\s+/.test(line.trim()) || /^\d+[.)、]\s+/.test(line.trim())) {
      blocks.push(line)
      i += 1
      continue
    }

    const paragraph: string[] = []
    while (
      i < lines.length &&
      lines[i].trim() &&
      !/^\|/.test(lines[i].trim()) &&
      !/^#{1,6}\s+/.test(lines[i].trim()) &&
      !/^\d+[.)、]\s+/.test(lines[i].trim())
    ) {
      paragraph.push(lines[i])
      i += 1
    }
    pushParagraphChunks(paragraph)
  }
  return blocks
}

const estimateBlockHeight = (block: string, cardWidth: number) => {
  const text = block.replace(/[#>*_`|[\]()]/g, '').trim()
  const charsPerLine = Math.max(18, Math.floor((cardWidth - 64) / 15))
  if (/^#\s+/.test(block)) return 56
  if (/^##\s+/.test(block)) return 42
  if (/^#{3,6}\s+/.test(block)) return 34
  if (/^\|/.test(block.trim())) {
    const rows = block.split('\n').filter((line) => /^\|/.test(line.trim()))
    return Math.max(80, rows.length * 36 + 12)
  }
  if (/^\d+[.)、]\s+/.test(block.trim())) return Math.max(28, Math.ceil(text.length / charsPerLine) * 24)
  const lineCount = Math.max(1, block.split('\n').length)
  return Math.max(34, Math.ceil(text.length / charsPerLine) * 26 + lineCount * 6 + 8)
}

const isHeadingBlock = (block: string) => /^#{1,6}\s+/.test(block.trim())

export const paginateMarkdown = (value: string, preset: CardSizePreset) => {
  const blocks = splitBlocks(value)
  const pages: string[] = []
  let current: string[] = []
  let height = 0
  const contentLimit = Math.max(160, preset.height - CARD_VERTICAL_CHROME)

  const pushCurrentPage = () => {
    if (!current.length) return
    if (current.length > 1 && isHeadingBlock(current[current.length - 1])) {
      const heading = current.pop() as string
      pages.push(current.join('\n\n'))
      current = [heading]
      height = estimateBlockHeight(heading, preset.width)
      return
    }
    pages.push(current.join('\n\n'))
    current = []
    height = 0
  }

  blocks.forEach((block) => {
    const blockHeight = estimateBlockHeight(block, preset.width)
    if (current.length && height + blockHeight > contentLimit) pushCurrentPage()
    current.push(block)
    height += blockHeight
  })

  if (current.length) pages.push(current.join('\n\n'))
  return pages.length ? pages : [defaultMarkdown]
}
