import { computed, ref } from 'vue'
import { ListSessionItem, SessionStatus } from '../types/response'

// 筛选类型
export type FilterType = 'all' | 'pinned' | 'running' | 'shared'

// 分组类型
export interface SessionGroup {
  key: string
  label: string
  sessions: ListSessionItem[]
  collapsed: boolean
}

// 时间分组工具函数
function isToday(timestamp: number | null): boolean {
  if (!timestamp) return false
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const date = new Date(timestamp * 1000)
  date.setHours(0, 0, 0, 0)
  return date.getTime() === today.getTime()
}

function isYesterday(timestamp: number | null): boolean {
  if (!timestamp) return false
  const yesterday = new Date()
  yesterday.setHours(0, 0, 0, 0)
  yesterday.setDate(yesterday.getDate() - 1)
  const date = new Date(timestamp * 1000)
  date.setHours(0, 0, 0, 0)
  return date.getTime() === yesterday.getTime()
}

function isWithinDays(timestamp: number | null, days: number): boolean {
  if (!timestamp) return false
  const now = new Date()
  now.setHours(0, 0, 0, 0)
  const date = new Date(timestamp * 1000)
  date.setHours(0, 0, 0, 0)
  const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24))
  return diffDays > 0 && diffDays <= days
}

function isWithinMonths(timestamp: number | null, months: number): boolean {
  if (!timestamp) return false
  const now = new Date()
  const date = new Date(timestamp * 1000)
  const diffMonths = (now.getFullYear() - date.getFullYear()) * 12 + (now.getMonth() - date.getMonth())
  return diffMonths > 0 && diffMonths <= months
}

/**
 * 会话分组和筛选 composable
 */
export function useSessionGrouping(sessions: { value: ListSessionItem[] }) {
  // 当前筛选
  const activeFilter = ref<FilterType>('all')

  // 分组折叠状态
  const collapsedGroups = ref<Set<string>>(new Set())

  // 搜索关键词
  const searchQuery = ref('')

  // 筛选后的会话
  const filteredSessions = computed(() => {
    let result = sessions.value

    // 搜索过滤
    if (searchQuery.value.trim()) {
      const query = searchQuery.value.toLowerCase()
      result = result.filter(s =>
        (s.title?.toLowerCase().includes(query)) ||
        (s.latest_message?.toLowerCase().includes(query))
      )
    }

    // 类型筛选
    switch (activeFilter.value) {
      case 'pinned':
        result = result.filter(s => s.pinned)
        break
      case 'running':
        result = result.filter(s => s.status === SessionStatus.RUNNING || s.status === SessionStatus.PENDING)
        break
      case 'shared':
        result = result.filter(s => s.is_shared)
        break
      case 'all':
      default:
        break
    }

    return result
  })

  // 分组后的会话
  const groupedSessions = computed<SessionGroup[]>(() => {
    const sessionsToGroup = filteredSessions.value

    // 置顶组
    const pinned: ListSessionItem[] = []
    const today: ListSessionItem[] = []
    const yesterday: ListSessionItem[] = []
    const last7Days: ListSessionItem[] = []
    const last30Days: ListSessionItem[] = []
    const older: ListSessionItem[] = []

    sessionsToGroup.forEach(session => {
      if (session.pinned) {
        pinned.push(session)
      } else if (isToday(session.latest_message_at)) {
        today.push(session)
      } else if (isYesterday(session.latest_message_at)) {
        yesterday.push(session)
      } else if (isWithinDays(session.latest_message_at, 7)) {
        last7Days.push(session)
      } else if (isWithinDays(session.latest_message_at, 30)) {
        last30Days.push(session)
      } else {
        older.push(session)
      }
    })

    const groups: SessionGroup[] = []

    if (pinned.length > 0) {
      groups.push({
        key: 'pinned',
        label: 'Pinned',
        sessions: pinned,
        collapsed: collapsedGroups.value.has('pinned')
      })
    }

    if (today.length > 0) {
      groups.push({
        key: 'today',
        label: 'Today',
        sessions: today,
        collapsed: collapsedGroups.value.has('today')
      })
    }

    if (yesterday.length > 0) {
      groups.push({
        key: 'yesterday',
        label: 'Yesterday',
        sessions: yesterday,
        collapsed: collapsedGroups.value.has('yesterday')
      })
    }

    if (last7Days.length > 0) {
      groups.push({
        key: 'last7Days',
        label: 'Last 7 Days',
        sessions: last7Days,
        collapsed: collapsedGroups.value.has('last7Days')
      })
    }

    if (last30Days.length > 0) {
      groups.push({
        key: 'last30Days',
        label: 'Last 30 Days',
        sessions: last30Days,
        collapsed: collapsedGroups.value.has('last30Days')
      })
    }

    if (older.length > 0) {
      groups.push({
        key: 'older',
        label: 'Older',
        sessions: older,
        collapsed: collapsedGroups.value.has('older')
      })
    }

    return groups
  })

  // 切换分组折叠状态
  const toggleGroupCollapse = (groupKey: string) => {
    if (collapsedGroups.value.has(groupKey)) {
      collapsedGroups.value.delete(groupKey)
    } else {
      collapsedGroups.value.add(groupKey)
    }
    // 触发响应式更新
    collapsedGroups.value = new Set(collapsedGroups.value)
  }

  // 设置筛选类型
  const setFilter = (filter: FilterType) => {
    activeFilter.value = filter
  }

  // 设置搜索关键词
  const setSearchQuery = (query: string) => {
    searchQuery.value = query
  }

  // 统计数据
  const stats = computed(() => ({
    all: sessions.value.length,
    pinned: sessions.value.filter(s => s.pinned).length,
    running: sessions.value.filter(s => s.status === SessionStatus.RUNNING || s.status === SessionStatus.PENDING).length,
    shared: sessions.value.filter(s => s.is_shared).length,
  }))

  return {
    activeFilter,
    searchQuery,
    filteredSessions,
    groupedSessions,
    collapsedGroups,
    stats,
    toggleGroupCollapse,
    setFilter,
    setSearchQuery,
  }
}
