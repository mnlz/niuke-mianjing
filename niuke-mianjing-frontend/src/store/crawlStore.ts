import { create } from 'zustand'
import type { CrawlProgress, WSMessage, WSMessageType } from '@/api/types'

interface CrawlStore {
  connected: boolean
  progresses: Record<string, CrawlProgress>
  lastMessages: WSMessage[]

  setConnected: (v: boolean) => void
  updateProgress: (post: string, progress: Partial<CrawlProgress>) => void
  removeProgress: (post: string) => void
  clearProgresses: () => void
  addMessage: (msg: WSMessage) => void
  handleMessage: (msg: WSMessage) => void
}

export const useCrawlStore = create<CrawlStore>((set, get) => ({
  connected: false,
  progresses: {},
  lastMessages: [],

  setConnected: (v) => set({ connected: v }),

  updateProgress: (post, progress) =>
    set((state) => ({
      progresses: {
        ...state.progresses,
        [post]: { ...state.progresses[post], ...progress } as CrawlProgress,
      },
    })),

  removeProgress: (post) =>
    set((state) => {
      const { [post]: _, ...rest } = state.progresses
      return { progresses: rest }
    }),

  clearProgresses: () => set({ progresses: {} }),

  addMessage: (msg) =>
    set((state) => ({
      lastMessages: [...state.lastMessages.slice(-49), msg],
    })),

  handleMessage: (msg: WSMessage) => {
    const { updateProgress, removeProgress, addMessage } = get()
    addMessage(msg)

    const data = msg.data as Record<string, unknown>

    switch (msg.type as WSMessageType) {
      case 'crawl_start':
        updateProgress(data?.post as string, {
          post: data?.post as string,
          currentPage: 0,
          totalPages: data?.max_pages as number || 0,
          newRecords: 0,
          updatedRecords: 0,
          status: 'running',
        })
        break

      case 'crawl_page_done':
        updateProgress(data?.post as string, {
          currentPage: data?.page as number,
          newRecords: data?.new_count as number,
          updatedRecords: data?.updated_count as number,
        })
        break

      case 'crawl_post_done':
        updateProgress(data?.post as string, {
          status: 'done',
          currentPage: get().progresses[data?.post as string]?.totalPages || 0,
          newRecords: data?.new_count as number,
          updatedRecords: data?.updated_count as number,
        })
        break

      case 'crawl_all_done':
        set((state) => {
          const updated = { ...state.progresses }
          Object.keys(updated).forEach((k) => {
            if (updated[k].status === 'running') {
              updated[k] = { ...updated[k], status: 'done' }
            }
          })
          return { progresses: updated }
        })
        break

      case 'crawl_error':
        if (data?.post) {
          updateProgress(data.post as string, {
            status: 'error',
            error: msg.message,
          })
        }
        break

      default:
        break
    }
  },
}))
