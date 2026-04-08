import { useEffect, useMemo, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import './App.css'

const API_BASE_URL = 'http://localhost:3000'

type Role = 'user' | 'assistant' | 'tool'

interface Message {
  role: Role
  content: string
  timestamp: string
  meta?: { toolName?: string }
}

interface ApiResponse {
  message?: string
  status?: string
  timestamp?: string
}

interface McpClientInfo {
  id: string
  name: string
  type: 'stdio' | 'http' | 'sse'
  createdAt: string
  isActive: boolean
}

interface McpInitRequest {
  name: string
  type: 'stdio' | 'http' | 'sse'
  config: {
    command?: string
    args?: string[]
    url?: string
  }
}

interface FeatureSummary {
  category: string
  tsSupport: '✅' | '⚠️' | '❌'
  notes: string
}

interface HookEventLog {
  type: string
  timestamp: string
  data?: any
}

const classNames = (...tokens: Array<string | false | null | undefined>) =>
  tokens.filter(Boolean).join(' ')

const formatTime = (value?: string | null) => {
  if (!value) return ''
  const d = new Date(value)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

const HOOKS_DESCRIPTION = `# Hooks

Hooks は、エージェントのライフサイクル全体で発生するイベントを購読することで、エージェントの機能を拡張するための「合成可能な拡張メカニズム」です。  
この Hook システムにより、組み込みコンポーネントとユーザーコードの両方が、強く型付けされたイベントコールバックを通して、エージェントの挙動に反応したり、それを変更したりできるようになります。

## Overview

Hooks システムは、イベントごとに複数の購読者をサポートする、合成可能で型安全な仕組みです。

Hook Event は、ライフサイクル中の特定のイベント種別であり、そのイベントに対してコールバックを関連付けることができます。  
Hook Callback は、その Hook Event が発火したときに呼び出されるコールバック関数です。

Hooks によって、次のようなユースケースが可能になります:

- エージェント実行やツール利用状況のモニタリング
- ツール実行の挙動の変更
- 検証処理やエラーハンドリングの追加

## Basic Usage

Hook コールバックは特定のイベント種別に対して登録され、エージェント実行中にそのイベントが発生したとき、強く型付けされたイベントオブジェクトを受け取ります。  
各イベントは、そのライフサイクル段階に応じた関連データを保持しています。例えば:

- \`BeforeInvocationEvent\` には、エージェントやリクエストの詳細が含まれます
- \`BeforeToolCallEvent\` には、ツール情報やパラメータが含まれます

### Registering Individual Hook Callbacks

個別のイベントに対して、\`agent.hooks\` を使ってコールバックを後から登録できます:

\`\`\`typescript
const agent = new Agent()

// 個別のコールバックを登録
const myCallback = (event: BeforeInvocationEvent) => {
  console.log('Custom callback triggered')
}

agent.hooks.addCallback(BeforeInvocationEvent, myCallback)
\`\`\`

### Creating a Hook Provider

\`HookProvider\` プロトコルを使うと、1つのオブジェクトから複数イベント分のコールバックを登録できます:

\`\`\`typescript
class LoggingHook implements HookProvider {
  registerCallbacks(registry: HookRegistry): void {
    registry.addCallback(BeforeInvocationEvent, (ev) => this.logStart(ev))
    registry.addCallback(AfterInvocationEvent, (ev) => this.logEnd(ev))
  }

  private logStart(event: BeforeInvocationEvent): void {
    console.log('Request started')
  }

  private logEnd(event: AfterInvocationEvent): void {
    console.log('Request completed')
  }
}

// hooks パラメータ経由で渡す
const agent = new Agent({ hooks: [new LoggingHook()] })

// あとから追加することもできる
agent.hooks.addHook(new LoggingHook())
\`\`\`

## Hook Event Lifecycle

以下の図は、ツールが呼び出される典型的なエージェント実行において、各 Hook イベントがいつ発火するかを示しています:

- Request Start Events → \`BeforeInvocationEvent\` → \`MessageAddedEvent\`
- Model Events → \`BeforeModelCallEvent\` → \`MessageAddedEvent\` → \`AfterModelCallEvent\`
- Tool Events → \`BeforeToolCallEvent\` → \`MessageAddedEvent\` → \`AfterToolCallEvent\`
- Request End Events → \`AfterInvocationEvent\`

## Available Events

Hooks システムは、エージェント実行のさまざまな段階に対してイベントを提供します:

| Event | Description |
|-------|-------------|
| AgentInitializedEvent | エージェントが構築され、コンストラクタの最後で初期化処理を完了したときに発火します。 |
| BeforeInvocationEvent | 新しいエージェント呼び出しリクエストの開始時に発火します。 |
| AfterInvocationEvent | エージェントリクエストの終了時に、成功・失敗に関わらず発火します。コールバックは逆順で呼び出されます。 |
| MessageAddedEvent | メッセージがエージェントの会話履歴に追加されたときに発火します。 |
| BeforeModelCallEvent | モデル推論の呼び出し前に発火します。 |
| AfterModelCallEvent | モデル呼び出しが完了した後に発火します。コールバックは逆順で呼び出されます。 |
| BeforeToolCallEvent | ツールが実行される前に発火します。 |
| AfterToolCallEvent | ツール実行が完了した後に発火します。コールバックは逆順で呼び出されます。 |
| BeforeToolsEvent (TypeScript only) | 複数ツールをバッチ実行する前に発火します。 |
| AfterToolsEvent (TypeScript only) | 複数ツールをバッチ実行した後に発火します。コールバックは逆順で呼び出されます。 |

## Hook Behaviors

### Event Properties

ほとんどのイベントプロパティは、意図しない変更を防ぐために読み取り専用です。  
ただし、一部のプロパティはエージェントの挙動に影響を与えるために変更できるようになっています。

### Callback Ordering

一部のイベントは Before/After のペアとして提供されます。  
After イベントのコールバックは、常に対応する Before イベントのコールバックが実行された順序の「逆順」で呼び出されます。これにより、クリーンアップ処理などの整合性が保たれます。

## Advanced Usage

### Accessing Invocation State in Hooks

ツール実行に関わる Hook イベントでは、\`invocation state\` にアクセスできます。  
\`invocation state\` には、エージェント呼び出しを通じて渡される設定やコンテキストデータが含まれます。これは特に次のような用途に便利です:

- カスタムオブジェクト: データベースクライアント、コネクションプール、その他の Python オブジェクトなどへのアクセス
- リクエストコンテキスト: セッションID、ユーザー情報、設定、リクエスト固有データへのアクセス
- マルチエージェント共有状態: マルチエージェントパターンで、すべてのエージェント間で共有される状態へのアクセス（詳細は「Shared State Across Multi-Agent Patterns」参照）
- カスタムパラメータ: Hooks 側で必要とする追加データの受け渡し

注: この機能は、現時点では TypeScript SDK では利用できません。

### Tool Interception

ツール実行前に、ツールを変更または差し替えることができます。

注: ツールの変更機能は、現時点では TypeScript SDK では利用できません。

### Result Modification

ツール実行後に、ツールの結果を変更できます。

注: ツール結果の変更機能は、現時点では TypeScript SDK では利用できません。

## Best Practices

### Composability

Hooks は合成可能で再利用しやすい形で設計してください。

注: ツールの変更機能は、現時点では TypeScript SDK では利用できません。

### Event Property Modifications

イベントプロパティを変更する場合、その変更内容をログに記録しておくと、デバッグや監査に役立ちます。

注: ツールの変更機能は、現時点では TypeScript SDK では利用できません。

## Cookbook

このセクションでは、よくあるユースケースに対する実践的な Hook 実装例を紹介します。

### Fixed Tool Arguments

セキュリティポリシーの強制、挙動の一貫性維持、システムレベルの要件でエージェントの判断を上書きする場合に有用です。  
この Hook は、エージェント側がどのようなパラメータを指定しても、特定のツールが常に事前に決めたパラメータ値を使うように保証します。

注: ツールの変更機能は、現時点では TypeScript SDK では利用できません。

例えば、電卓ツール (\`calculator\` ツール) が常に小数点以下1桁の精度 (\`precision = 1\`) を使うように強制する場合:

注: ツールの変更機能は、現時点では TypeScript SDK では利用できません。

### Limit Tool Counts

暴走的なツール呼び出しの防止、レート制限の実装、使用回数のクォータ制御などに有用です。  
この Hook は、リクエストごとのツール呼び出し回数を追跡し、制限を超えた場合にはツールをエラーメッセージで置き換えます。

注: この機能は、現時点では TypeScript SDK では利用できません。

例えば、\`sleep\` ツールの呼び出しを 1 回のエージェント呼び出しにつき 3 回までに制限する場合:

注: この機能は、現時点では TypeScript SDK では利用できません。`

function App() {
  const [responses, setResponses] = useState<Record<string, ApiResponse | null>>({})
  const [loading, setLoading] = useState<Record<string, boolean>>({})
  const [errors, setErrors] = useState<Record<string, string | null>>({})

  const [messages, setMessages] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const [mcpClients, setMcpClients] = useState<McpClientInfo[]>([])
  const [activeMcpId, setActiveMcpId] = useState<string | null>(null)
  const [showMcpInit, setShowMcpInit] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [showFeatureSummary, setShowFeatureSummary] = useState(false)
  const [mcpInitForm, setMcpInitForm] = useState<McpInitRequest>({
    name: '',
    type: 'stdio',
    config: { command: '', args: [] }
  })
  const [agentState, setAgentState] = useState<Record<string, any>>({})
  const [agentStateLoading, setAgentStateLoading] = useState(false)
  const [newStateKey, setNewStateKey] = useState('')
  const [newStateValue, setNewStateValue] = useState('')
  const [editingStateKey, setEditingStateKey] = useState<string | null>(null)
  const [editingStateValue, setEditingStateValue] = useState('')
  const [conversationManagerType, setConversationManagerType] = useState<'null' | 'slidingWindow'>('slidingWindow')
  const [conversationManagerWindowSize, setConversationManagerWindowSize] = useState<number>(40)
  const [conversationManagerShouldTruncate, setConversationManagerShouldTruncate] = useState<boolean>(true)
  const [conversationManagerLoading, setConversationManagerLoading] = useState(false)
  const [hooksEvents, setHooksEvents] = useState<HookEventLog[]>([])
  const [showHooksLog, setShowHooksLog] = useState(false)
  const [hooksEventFilter, setHooksEventFilter] = useState<string>('all')
  const [currentHooksEvent, setCurrentHooksEvent] = useState<string | null>(null)
  const [showHooksDescription, setShowHooksDescription] = useState(false)
  const [notebooks, setNotebooks] = useState<Record<string, string>>({})
  const [notebooksLoading, setNotebooksLoading] = useState(false)
  const [selectedNotebook, setSelectedNotebook] = useState<string | null>(null)
  const [newNotebookName, setNewNotebookName] = useState('')
  const [newNotebookContent, setNewNotebookContent] = useState('')
  const [showSidebar, setShowSidebar] = useState(false)

  const generateUniqueNotebookName = (baseName: string, existingNotebooks: Record<string, string>): string => {
    let index = 1
    let candidate = `${baseName}-${index}`
    while (existingNotebooks[candidate] !== undefined) {
      index += 1
      candidate = `${baseName}-${index}`
    }
    return candidate
  }

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent])

  useEffect(() => {
    loadMcpClients()
    loadActiveMcp()
    loadAgentState()
    loadConversationManager()
    loadNotebooks()
  }, [])

  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setShowSidebar(false)
        setShowSettings(false)
        setShowFeatureSummary(false)
        setShowHooksLog(false)
      }
    }
    window.addEventListener('keydown', handleEsc)
    return () => window.removeEventListener('keydown', handleEsc)
  }, [])

  useEffect(() => {
    document.body.style.overflow = showSidebar ? 'hidden' : ''
    return () => {
      document.body.style.overflow = ''
    }
  }, [showSidebar])

  const loadMcpClients = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/mcp/list`)
      if (response.ok) {
        const data = await response.json()
        const clients = data.clients || []
        setMcpClients(clients)
        const activeId = data.activeId || null
        if (activeId && clients.some((client: McpClientInfo) => client.id === activeId)) {
          setActiveMcpId(activeId)
        } else {
          setActiveMcpId(null)
        }
      }
    } catch (error) {
      console.error('Failed to load MCP clients:', error)
      setActiveMcpId(null)
    }
  }

  const loadActiveMcp = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/mcp/active`)
      if (response.ok) {
        const data = await response.json()
        const activeId = data.id || null
        if (activeId && mcpClients.some(client => client.id === activeId)) {
          setActiveMcpId(activeId)
        } else {
          setActiveMcpId(null)
        }
      } else {
        setActiveMcpId(null)
      }
    } catch (error) {
      console.error('Failed to load active MCP:', error)
      setActiveMcpId(null)
    }
  }

  const initMcpClient = async () => {
    if (!mcpInitForm.name.trim()) {
      alert('MCP名を入力してください')
      return
    }

    if (mcpInitForm.type === 'stdio') {
      if (!mcpInitForm.config.command || !mcpInitForm.config.args || mcpInitForm.config.args.length === 0) {
        alert('コマンドと引数を入力してください')
        return
      }
    } else if (!mcpInitForm.config.url) {
      alert('URLを入力してください')
      return
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/mcp/init`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(mcpInitForm),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to initialize MCP client')
      }

      await loadMcpClients()
      setShowMcpInit(false)
      setMcpInitForm({ name: '', type: 'stdio', config: { command: '', args: [] } })
    } catch (error) {
      console.error('Failed to initialize MCP client:', error)
      alert(error instanceof Error ? error.message : 'MCPクライアントの初期化に失敗しました')
    }
  }

  const switchMcpClient = async (mcpId: string | null) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/mcp/switch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ mcpId }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to switch MCP client')
      }

      setActiveMcpId(mcpId)
      await loadMcpClients()
    } catch (error) {
      console.error('Failed to switch MCP client:', error)
      await loadMcpClients()
      if (error instanceof Error && error.message.includes('not found')) {
        setActiveMcpId(null)
      }
      alert(error instanceof Error ? error.message : 'MCPクライアントの切り替えに失敗しました')
    }
  }

  const fetchApi = async (endpoint: string, name: string) => {
    setLoading(prev => ({ ...prev, [name]: true }))
    setErrors(prev => ({ ...prev, [name]: null }))

    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data: ApiResponse = await response.json()
      setResponses(prev => ({ ...prev, [name]: data }))
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      setErrors(prev => ({ ...prev, [name]: errorMessage }))
      setResponses(prev => ({ ...prev, [name]: null }))
    } finally {
      setLoading(prev => ({ ...prev, [name]: false }))
    }
  }

  const resetConversation = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/agent/reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      setMessages([])
      setStreamingContent('')
    } catch (error) {
      console.error('Failed to reset conversation:', error)
    }
  }

  const sendMessage = async () => {
    if (!inputMessage.trim() || isStreaming) return

    const now = new Date().toISOString()
    const userMessage: Message = {
      role: 'user',
      content: inputMessage.trim(),
      timestamp: now,
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsStreaming(true)
    setStreamingContent('')

    try {
      const response = await fetch(`${API_BASE_URL}/api/agent/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userMessage.content }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('Response body is not readable')
      }

      let buffer = ''
      let accumulatedContent = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const event = JSON.parse(line.slice(6))

              if (event.type === 'error') {
                throw new Error(event.error || 'Streaming error')
              }

              const hookEventTypes = [
                'beforeInvocationEvent',
                'afterInvocationEvent',
                'beforeModelCallEvent',
                'afterModelCallEvent',
                'beforeToolCallEvent',
                'afterToolCallEvent',
                'beforeToolsEvent',
                'afterToolsEvent',
                'messageAddedEvent',
                'agentInitializedEvent'
              ]

              if (hookEventTypes.includes(event.type)) {
                const hookEvent: HookEventLog = {
                  type: event.type,
                  timestamp: new Date().toISOString(),
                  data: event
                }
                setHooksEvents(prev => [...prev, hookEvent])
                setCurrentHooksEvent(event.type)
                setTimeout(() => setCurrentHooksEvent(null), 2000)
              }

              if (event.type === 'modelContentBlockDeltaEvent') {
                const textDelta = event.delta?.textDelta || event.textDelta || event.delta?.text || ''
                if (textDelta) {
                  accumulatedContent += textDelta
                  setStreamingContent(accumulatedContent)
                }
              } else if (event.type === 'afterInvocationEvent') {
                if (event.stopData?.message?.content) {
                  const content = Array.isArray(event.stopData.message.content)
                    ? event.stopData.message.content.map((c: any) => c.text || '').join('')
                    : event.stopData.message.content
                  if (content && !accumulatedContent) {
                    accumulatedContent = content
                    setStreamingContent(accumulatedContent)
                  }
                }
              } else if (event.type === 'toolResultEvent' && event.result) {
                const toolMessage: Message = {
                  role: 'tool',
                  content: typeof event.result === 'string' ? event.result : JSON.stringify(event.result, null, 2),
                  timestamp: new Date().toISOString(),
                  meta: { toolName: event.toolName }
                }
                setMessages(prev => [...prev, toolMessage])
              }
            } catch (parseError) {
              console.error('Failed to parse SSE data:', parseError)
            }
          }
        }
      }

      if (buffer && buffer.startsWith('data: ')) {
        try {
          const event = JSON.parse(buffer.slice(6))
          if (event.type === 'modelContentBlockDeltaEvent') {
            const textDelta = event.delta?.textDelta || event.textDelta || event.delta?.text || ''
            if (textDelta) {
              accumulatedContent += textDelta
              setStreamingContent(accumulatedContent)
            }
          }
        } catch (parseError) {
          console.error('Failed to parse remaining buffer:', parseError)
        }
      }

      if (accumulatedContent) {
        const assistantMessage: Message = {
          role: 'assistant',
          content: accumulatedContent,
          timestamp: new Date().toISOString(),
        }
        setMessages(prev => [...prev, assistantMessage])
        await loadNotebooks()
        await loadAgentState()
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      const errorMsg: Message = {
        role: 'assistant',
        content: `エラー: ${errorMessage}`,
        timestamp: new Date().toISOString(),
      }
      setMessages(prev => [...prev, errorMsg])
    } finally {
      setIsStreaming(false)
      setStreamingContent('')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
    } catch (err) {
      console.error('Failed to copy text:', err)
    }
  }

  const loadAgentState = async () => {
    setAgentStateLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/agent/state`)
      if (response.ok) {
        const data = await response.json()
        setAgentState(data.state || {})
      }
    } catch (error) {
      console.error('Failed to load agent state:', error)
    } finally {
      setAgentStateLoading(false)
    }
  }

  const loadConversationManager = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/agent/conversation-manager`)
      if (response.ok) {
        const data = await response.json()
        const config = data.config || {}
        setConversationManagerType(config.type || 'slidingWindow')
        setConversationManagerWindowSize(config.windowSize || 40)
        setConversationManagerShouldTruncate(config.shouldTruncateResults !== undefined ? config.shouldTruncateResults : true)
      }
    } catch (error) {
      console.error('Failed to load conversation manager:', error)
    }
  }

  const handleSetConversationManager = async () => {
    setConversationManagerLoading(true)
    try {
      const config: any = { type: conversationManagerType }
      if (conversationManagerType === 'slidingWindow') {
        config.windowSize = conversationManagerWindowSize
        config.shouldTruncateResults = conversationManagerShouldTruncate
      }

      const response = await fetch(`${API_BASE_URL}/api/agent/conversation-manager`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to set conversation manager')
      }

      await response.json()
      alert(`Conversation Managerを${conversationManagerType}に設定しました`)
    } catch (error) {
      console.error('Failed to set conversation manager:', error)
      alert(error instanceof Error ? error.message : 'Conversation Managerの設定に失敗しました')
    } finally {
      setConversationManagerLoading(false)
    }
  }

  const handleSetAgentState = async () => {
    if (!newStateKey.trim()) {
      alert('キーを入力してください')
      return
    }

    let parsedValue: any
    try {
      parsedValue = JSON.parse(newStateValue || 'null')
    } catch {
      parsedValue = newStateValue
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/agent/state`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key: newStateKey.trim(), value: parsedValue }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to set agent state')
      }

      setNewStateKey('')
      setNewStateValue('')
      await loadAgentState()
      await loadNotebooks()
    } catch (error) {
      console.error('Failed to set agent state:', error)
      alert(error instanceof Error ? error.message : 'Agent Stateの設定に失敗しました')
    }
  }

  const handleUpdateAgentState = async (key: string) => {
    let parsedValue: any
    try {
      parsedValue = JSON.parse(editingStateValue || 'null')
    } catch {
      parsedValue = editingStateValue
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/agent/state`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key, value: parsedValue }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to update agent state')
      }

      setEditingStateKey(null)
      setEditingStateValue('')
      await loadAgentState()
      await loadNotebooks()
    } catch (error) {
      console.error('Failed to update agent state:', error)
      alert(error instanceof Error ? error.message : 'Agent Stateの更新に失敗しました')
    }
  }

  const handleDeleteAgentState = async (key: string) => {
    if (!confirm(`キー "${key}" を削除しますか？`)) return

    try {
      const response = await fetch(`${API_BASE_URL}/api/agent/state/${encodeURIComponent(key)}`, {
        method: 'DELETE',
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to delete agent state')
      }

      await loadAgentState()
      await loadNotebooks()
    } catch (error) {
      console.error('Failed to delete agent state:', error)
      alert(error instanceof Error ? error.message : 'Agent Stateの削除に失敗しました')
    }
  }

  const handleResetAgentState = async () => {
    if (!confirm('Agent Stateをすべてリセットしますか？')) return

    try {
      const response = await fetch(`${API_BASE_URL}/api/agent/state/reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to reset agent state')
      }

      await loadAgentState()
      await loadNotebooks()
    } catch (error) {
      console.error('Failed to reset agent state:', error)
      alert(error instanceof Error ? error.message : 'Agent Stateのリセットに失敗しました')
    }
  }

  const normalizeNotebooks = (raw: any): Record<string, string> => {
    if (!raw) return {}
    if (typeof raw === 'string') {
      try {
        const parsed = JSON.parse(raw)
        if (parsed && typeof parsed === 'object') {
          return parsed as Record<string, string>
        }
      } catch {
        return { default: raw }
      }
    }
    if (typeof raw === 'object') {
      if (raw instanceof Map) {
        return Object.fromEntries(raw.entries()) as Record<string, string>
      }
      const anyObj = raw as any
      if (typeof anyObj.entries === 'function') {
        return Object.fromEntries(anyObj.entries()) as Record<string, string>
      }
      return { ...(raw as Record<string, string>) }
    }
    return { default: String(raw) }
  }

  const loadNotebooks = async () => {
    setNotebooksLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/agent/state`)
      if (response.ok) {
        const data = await response.json()
        const notebooksData = normalizeNotebooks(data.state?.notebooks)
        setNotebooks(notebooksData)
        const names = Object.keys(notebooksData)
        setSelectedNotebook((prev) => {
          if (prev && names.includes(prev)) return prev
          return names.length > 0 ? names[0] : null
        })
      }
    } catch (error) {
      console.error('Failed to load notebooks:', error)
    } finally {
      setNotebooksLoading(false)
    }
  }

  const handleCreateNotebook = async () => {
    if (!newNotebookName.trim()) {
      alert('ノートブック名を入力してください')
      return
    }

    try {
      const baseName = newNotebookName.trim()
      const newContent = newNotebookContent || ''

      const currentNotebooks = notebooks
      const hasSameName = currentNotebooks[baseName] !== undefined
      const isContentDifferent = hasSameName && currentNotebooks[baseName] !== newContent
      const targetName = isContentDifferent ? generateUniqueNotebookName(baseName, currentNotebooks) : baseName

      const updatedNotebooks = {
        ...currentNotebooks,
        [targetName]: newContent
      }

      const response = await fetch(`${API_BASE_URL}/api/agent/state`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key: 'notebooks', value: updatedNotebooks }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to create notebook')
      }

      setNewNotebookName('')
      setNewNotebookContent('')
      await loadNotebooks()
      setSelectedNotebook(targetName)
    } catch (error) {
      console.error('Failed to create notebook:', error)
      alert(error instanceof Error ? error.message : 'ノートブックの作成に失敗しました')
    }
  }

  const handleDeleteNotebook = async (notebookName: string) => {
    if (!confirm(`ノートブック "${notebookName}" を削除しますか？`)) return

    try {
      const currentNotebooks = { ...notebooks }
      delete currentNotebooks[notebookName]

      const response = await fetch(`${API_BASE_URL}/api/agent/state`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key: 'notebooks', value: currentNotebooks }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to delete notebook')
      }

      if (selectedNotebook === notebookName) {
        const remainingNames = Object.keys(currentNotebooks)
        setSelectedNotebook(remainingNames.length > 0 ? remainingNames[0] : null)
      }
      await loadNotebooks()
    } catch (error) {
      console.error('Failed to delete notebook:', error)
      alert(error instanceof Error ? error.message : 'ノートブックの削除に失敗しました')
    }
  }

  const featureSummary: FeatureSummary[] = [
    { category: 'エージェント作成・実行', tsSupport: '✅', notes: 'Agent, invoke()' },
    { category: 'カスタムツール（tool）', tsSupport: '✅', notes: '関数 / クラス / async / streaming' },
    { category: 'Vended Tools', tsSupport: '✅', notes: 'bash など一部' },
    { category: 'モデルプロバイダ', tsSupport: '⚠️', notes: 'Bedrock / OpenAI / Custom のみ' },
    { category: 'ストリーミング（Async Iterator）', tsSupport: '✅', notes: 'agent.stream()' },
    { category: 'Callback Handlers（Streaming）', tsSupport: '❌', notes: '公式に「Not supported」' },
    { category: 'Hooks', tsSupport: '✅', notes: 'TS専用イベントあり' },
    { category: 'Agent State', tsSupport: '✅', notes: 'agent.state, context.agent.state' },
    { category: 'Request State', tsSupport: '❌', notes: 'Python のみ' },
    { category: 'Conversation Manager', tsSupport: '✅', notes: 'Null / SlidingWindow、要約型は Python のみ' },
    { category: 'MCP Tools', tsSupport: '✅', notes: 'stdio / HTTP / SSE' },
    { category: 'Structured Output', tsSupport: '❌', notes: 'Python のみ' },
    { category: 'Tool Executors', tsSupport: '❌', notes: 'Python のみ' },
    { category: 'Community Tools (strands-agents-tools)', tsSupport: '❌', notes: 'Python のみ' },
  ]

  const MessageContent = ({ content, role }: { content: string; role: Role }) => {
    if (role === 'user') {
      return <div className="markdown">{content}</div>
    }

    return (
      <div className="markdown">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            code({ node, inline, className, children, ...props }: any) {
              const match = /language-(\w+)/.exec(className || '')
              const codeString = String(children).replace(/\n$/, '')
              return !inline && match ? (
                <SyntaxHighlighter
                  style={vscDarkPlus}
                  language={match[1]}
                  PreTag="div"
                  {...props}
                >
                  {codeString}
                </SyntaxHighlighter>
              ) : (
                <code className={className} {...props}>
                  {children}
                </code>
              )
            },
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    )
  }

  const Avatar = ({ role }: { role: Role }) => {
    const icon =
      role === 'user'
        ? (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 12C14.7614 12 17 9.76142 17 7C17 4.23858 14.7614 2 12 2C9.23858 2 7 4.23858 7 7C7 9.76142 9.23858 12 12 12Z" fill="currentColor"/>
            <path d="M12 14C7.58172 14 4 16.2386 4 19V22H20V19C20 16.2386 16.4183 14 12 14Z" fill="currentColor"/>
          </svg>
        )
        : role === 'tool'
          ? (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M14.59 2.59L11.17 6H5C3.9 6 3 6.9 3 8V20C3 21.1 3.9 22 5 22H19C20.1 22 21 21.1 21 20V4C21 2.9 20.1 2 19 2H15C14.74 2 14.48 2.11 14.29 2.29L14.59 2.59ZM12 7.41L14.59 5H19V20H5V8H11C11.26 8 11.52 7.89 11.71 7.71L12 7.41ZM12 12C10.9 12 10 12.9 10 14C10 15.1 10.9 16 12 16C13.1 16 14 15.1 14 14C14 12.9 13.1 12 12 12Z" fill="currentColor"/>
            </svg>
          )
          : (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM13 17H11V15H13V17ZM13 13H11V7H13V13Z" fill="currentColor"/>
            </svg>
          )

    return <div className="msg__avatar">{icon}</div>
  }

  const activeMcpClient = mcpClients.find(client => client.id === activeMcpId)

  const roleLabels: Record<Role, string> = {
    user: 'あなた',
    assistant: 'エージェント',
    tool: 'Tool'
  }

  const streamingBadge = useMemo(() => {
    if (!currentHooksEvent) return null
    return (
      <span className="badge">
        {currentHooksEvent.replace('Event', '')}
      </span>
    )
  }, [currentHooksEvent])

  return (
    <div className="app">
      <header className="topbar">
        <button
          className="sidebar-toggle"
          onClick={() => setShowSidebar(true)}
          aria-label="サイドバーを開く"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M4 6H20V8H4V6ZM4 11H20V13H4V11ZM4 16H20V18H4V16Z" fill="currentColor"/>
          </svg>
        </button>

        <div className="topbar__title">Strands Agent TypeScript SDK</div>

        <div className="topbar__status">
          <span className={classNames('pill', activeMcpClient && 'pill--accent')}>
            MCP: {activeMcpClient ? `${activeMcpClient.name} (${activeMcpClient.type})` : 'なし'}
          </span>
          {isStreaming && <span className="pill pill--accent">生成中...</span>}
        </div>
      </header>

      <aside className={classNames('sidebar', showSidebar && 'is-open')}>
        <div className="sidebar__header">
          <div className="sidebar__title">メニュー</div>
          <button className="iconBtn" aria-label="サイドバーを閉じる" onClick={() => setShowSidebar(false)}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M18.3 5.71L12 12M5.7 18.29L12 12M12 12L18.3 18.29M12 12L5.7 5.71" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </button>
        </div>
        <div className="sidebar__content">
          <div className="panel">
            <h3>MCP設定</h3>
            <div className="field">
              <label className="label">MCP</label>
              <select
                value={activeMcpId || ''}
                onChange={(e) => switchMcpClient(e.target.value || null)}
                disabled={isStreaming}
                className="select"
              >
                <option value="">なし</option>
                {mcpClients.map(client => (
                  <option key={client.id} value={client.id}>
                    {client.name} ({client.type})
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <button className="btn" onClick={() => setShowMcpInit(!showMcpInit)} disabled={isStreaming}>
                {showMcpInit ? 'キャンセル' : 'MCP初期化'}
              </button>
            </div>
            {showMcpInit && (
              <div className="panel">
                <div className="field">
                  <label className="label">名前</label>
                  <input
                    className="input"
                    type="text"
                    value={mcpInitForm.name}
                    onChange={(e) => setMcpInitForm({ ...mcpInitForm, name: e.target.value })}
                    placeholder="MCPクライアント名"
                  />
                </div>
                <div className="field">
                  <label className="label">タイプ</label>
                  <select
                    className="select"
                    value={mcpInitForm.type}
                    onChange={(e) => setMcpInitForm({
                      ...mcpInitForm,
                      type: e.target.value as McpInitRequest['type'],
                      config: e.target.value === 'stdio' ? { command: '', args: [] } : { url: '' }
                    })}
                  >
                    <option value="stdio">Stdio</option>
                    <option value="http">HTTP</option>
                    <option value="sse">SSE</option>
                  </select>
                </div>
                {mcpInitForm.type === 'stdio' ? (
                  <>
                    <div className="field">
                      <label className="label">コマンド</label>
                      <input
                        className="input"
                        type="text"
                        value={mcpInitForm.config.command || ''}
                        onChange={(e) => setMcpInitForm({
                          ...mcpInitForm,
                          config: { ...mcpInitForm.config, command: e.target.value }
                        })}
                        placeholder="例: uvx"
                      />
                    </div>
                    <div className="field">
                      <label className="label">引数 (カンマ区切り)</label>
                      <input
                        className="input"
                        type="text"
                        value={mcpInitForm.config.args?.join(', ') || ''}
                        onChange={(e) => setMcpInitForm({
                          ...mcpInitForm,
                          config: { ...mcpInitForm.config, args: e.target.value.split(',').map(s => s.trim()).filter(Boolean) }
                        })}
                        placeholder="例: awslabs.aws-documentation-mcp-server@latest"
                      />
                    </div>
                  </>
                ) : (
                  <div className="field">
                    <label className="label">URL</label>
                    <input
                      className="input"
                      type="text"
                      value={mcpInitForm.config.url || ''}
                      onChange={(e) => setMcpInitForm({
                        ...mcpInitForm,
                        config: { ...mcpInitForm.config, url: e.target.value }
                      })}
                      placeholder="例: http://localhost:8000/mcp"
                    />
                  </div>
                )}
                <button className="btn primary" onClick={initMcpClient}>初期化</button>
              </div>
            )}
          </div>

          <div className="panel">
            <h3>操作</h3>
            <div className="field">
              <button className="btn" onClick={resetConversation} disabled={isStreaming}>会話をリセット</button>
            </div>
            <div className="field">
              <button className="btn" onClick={() => setShowFeatureSummary(true)}>機能サマリ</button>
            </div>
            <div className="field">
              <button className="btn" onClick={() => setShowHooksLog(true)}>Hooksログ {hooksEvents.length > 0 && `(${hooksEvents.length})`}</button>
            </div>
          </div>

          <div className="panel">
            <h3>設定</h3>
            <div className="field">
              <button className="btn" onClick={() => setShowSettings(true)}>設定を開く</button>
            </div>
          </div>
        </div>
      </aside>
      {showSidebar && <div className="overlay" onClick={() => setShowSidebar(false)} />}

      <main className="main">
        <section className="chat">
          <div className="chat__inner">
            {messages.length === 0 && !streamingContent && (
              <div className="empty">メッセージを入力して会話を開始してください</div>
            )}

            {messages.map((message, index) => (
              <div key={`${message.timestamp}-${index}`} className={classNames('msg', `msg--${message.role}`)}>
                <Avatar role={message.role} />
                <div className="msg__body">
                  <div className="msg__meta">
                    <span className="msg__role">{roleLabels[message.role]}</span>
                    {message.meta?.toolName && <span className="chip">{message.meta.toolName}</span>}
                    <span className="msg__time">{formatTime(message.timestamp)}</span>
                    <div className="msg__actions">
                      <button className="iconBtn" title="コピー" onClick={() => copyToClipboard(message.content)}>⧉</button>
                    </div>
                  </div>
                  <div className="bubble">
                    <MessageContent content={message.content} role={message.role} />
                  </div>
                </div>
              </div>
            ))}

            {streamingContent && (
              <div className="msg msg--assistant">
                <Avatar role="assistant" />
                <div className="msg__body">
                  <div className="msg__meta">
                    <span className="msg__role">Assistant</span>
                    {streamingBadge}
                  </div>
                  <div className="bubble">
                    <MessageContent content={streamingContent} role="assistant" />
                    <span className="chip">Streaming...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </section>

        <footer className="composer">
          <div className="composer__inner">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="メッセージを入力してください（Enterで送信、Shift+Enterで改行）"
              className="textarea"
              disabled={isStreaming}
            />
            <div className="composer__actions">
              <button
                className="btn primary"
                onClick={sendMessage}
                disabled={isStreaming || !inputMessage.trim()}
              >
                {isStreaming ? '送信中...' : '送信'}
              </button>
            </div>
          </div>
        </footer>
      </main>

      {showSettings && (
        <div className="modal" onClick={() => setShowSettings(false)}>
          <div className="modal__card" onClick={(e) => e.stopPropagation()}>
            <div className="modal__head">
              <div className="sidebar__title">設定</div>
              <button className="iconBtn" onClick={() => setShowSettings(false)} aria-label="閉じる">✕</button>
            </div>
            <div className="modal__body">
              <div className="panel">
                <h3>Health Check</h3>
                <div className="field">
                  <button
                    className="btn primary"
                    onClick={() => fetchApi('/api/health', 'health')}
                    disabled={loading.health}
                  >
                    {loading.health ? '確認中...' : 'Health Checkを実行'}
                  </button>
                </div>
                {responses.health && (
                  <div className="panel">
                    <pre className="log-item__body">{JSON.stringify(responses.health, null, 2)}</pre>
                  </div>
                )}
                {errors.health && <div className="chip warn">エラー: {errors.health}</div>}
              </div>

              <div className="panel">
                <h3>Agent State</h3>
                <div className="field">
                  <button className="btn" onClick={loadAgentState} disabled={agentStateLoading}>
                    {agentStateLoading ? '読み込み中...' : '再読み込み'}
                  </button>
                  <button className="btn" onClick={handleResetAgentState}>リセット</button>
                </div>

                <div className="panel">
                  <div className="field">
                    <label className="label">キー</label>
                    <input
                      className="input"
                      type="text"
                      value={newStateKey}
                      onChange={(e) => setNewStateKey(e.target.value)}
                      placeholder="例: user_preferences"
                    />
                  </div>
                  <div className="field">
                    <label className="label">値 (JSON または文字列)</label>
                    <textarea
                      className="textarea"
                      value={newStateValue}
                      onChange={(e) => setNewStateValue(e.target.value)}
                      rows={3}
                    />
                  </div>
                  <button className="btn primary" onClick={handleSetAgentState}>追加</button>
                </div>

                <div className="panel">
                  {Object.keys(agentState).length === 0 ? (
                    <div className="empty">Agent Stateは空です</div>
                  ) : (
                    Object.entries(agentState).map(([key, value]) => (
                      <div key={key} className="panel" style={{ marginBottom: 10 }}>
                        {editingStateKey === key ? (
                          <>
                            <div className="label">{key}</div>
                            <textarea
                              className="textarea"
                              value={editingStateValue}
                              onChange={(e) => setEditingStateValue(e.target.value)}
                              rows={2}
                            />
                            <div className="field">
                              <button className="btn primary" onClick={() => handleUpdateAgentState(key)}>保存</button>
                              <button className="btn" onClick={() => { setEditingStateKey(null); setEditingStateValue('') }}>キャンセル</button>
                            </div>
                          </>
                        ) : (
                          <>
                            <div className="log-item__head">
                              <div className="label">{key}</div>
                              <div className="msg__actions" style={{ opacity: 1 }}>
                                <button
                                  className="iconBtn"
                                  onClick={() => {
                                    setEditingStateKey(key)
                                    setEditingStateValue(typeof value === 'string' ? value : JSON.stringify(value, null, 2))
                                  }}
                                >
                                  ✎
                                </button>
                                <button className="iconBtn" onClick={() => handleDeleteAgentState(key)}>🗑</button>
                              </div>
                            </div>
                            <pre className="log-item__body">{typeof value === 'string' ? value : JSON.stringify(value, null, 2)}</pre>
                          </>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>

              <div className="panel">
                <h3>Notebooks</h3>
                <div className="field">
                  <button className="btn" onClick={loadNotebooks} disabled={notebooksLoading}>
                    {notebooksLoading ? '読み込み中...' : '再読み込み'}
                  </button>
                </div>
                <div className="panel">
                  <div className="field">
                    <label className="label">ノートブック名</label>
                    <input
                      className="input"
                      type="text"
                      value={newNotebookName}
                      onChange={(e) => setNewNotebookName(e.target.value)}
                      placeholder="例: meeting-notes"
                    />
                  </div>
                  <div className="field">
                    <label className="label">初期内容</label>
                    <textarea
                      className="textarea"
                      value={newNotebookContent}
                      onChange={(e) => setNewNotebookContent(e.target.value)}
                      rows={3}
                    />
                  </div>
                  <button className="btn primary" onClick={handleCreateNotebook}>作成</button>
                </div>

                {Object.keys(notebooks).length === 0 ? (
                  <div className="empty">ノートブックがありません</div>
                ) : (
                  <div className="panel">
                    <div className="field">
                      <label className="label">ノートブックを選択</label>
                      <select
                        className="select"
                        value={selectedNotebook || ''}
                        onChange={(e) => setSelectedNotebook(e.target.value)}
                      >
                        {Object.keys(notebooks).map((name) => (
                          <option key={name} value={name}>{name}</option>
                        ))}
                      </select>
                    </div>
                    {selectedNotebook && (
                      <div className="panel">
                        <div className="log-item__head">
                          <div className="label">{selectedNotebook}</div>
                          <button className="iconBtn" onClick={() => handleDeleteNotebook(selectedNotebook)}>🗑</button>
                        </div>
                        <div className="markdown">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                              code({ node, inline, className, children, ...props }: any) {
                                const match = /language-(\w+)/.exec(className || '')
                                return !inline && match ? (
                                  <SyntaxHighlighter
                                    style={vscDarkPlus}
                                    language={match[1]}
                                    PreTag="div"
                                    {...props}
                                  >
                                    {String(children).replace(/\n$/, '')}
                                  </SyntaxHighlighter>
                                ) : (
                                  <code className={className} {...props}>
                                    {children}
                                  </code>
                                )
                              },
                            }}
                          >
                            {notebooks[selectedNotebook] || '*空のノートブック*'}
                          </ReactMarkdown>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div className="panel">
                <h3>Conversation Manager</h3>
                <div className="field">
                  <label className="label">タイプ</label>
                  <select
                    className="select"
                    value={conversationManagerType}
                    onChange={(e) => setConversationManagerType(e.target.value as 'null' | 'slidingWindow')}
                  >
                    <option value="null">Null</option>
                    <option value="slidingWindow">SlidingWindow</option>
                  </select>
                </div>
                {conversationManagerType === 'slidingWindow' && (
                  <>
                    <div className="field">
                      <label className="label">Window Size</label>
                      <input
                        className="input"
                        type="number"
                        value={conversationManagerWindowSize}
                        onChange={(e) => setConversationManagerWindowSize(parseInt(e.target.value) || 40)}
                        min={1}
                      />
                    </div>
                    <div className="field">
                      <label className="label">
                        <input
                          type="checkbox"
                          checked={conversationManagerShouldTruncate}
                          onChange={(e) => setConversationManagerShouldTruncate(e.target.checked)}
                        /> Should Truncate Results
                      </label>
                    </div>
                  </>
                )}
                <button
                  className="btn primary"
                  onClick={handleSetConversationManager}
                  disabled={conversationManagerLoading}
                >
                  {conversationManagerLoading ? '設定中...' : '設定'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {showFeatureSummary && (
        <div className="modal" onClick={() => setShowFeatureSummary(false)}>
          <div className="modal__card" onClick={(e) => e.stopPropagation()}>
            <div className="modal__head">
              <div className="sidebar__title">機能サマリ（TypeScript SDK）</div>
              <button className="iconBtn" onClick={() => setShowFeatureSummary(false)} aria-label="閉じる">✕</button>
            </div>
            <div className="modal__body">
              <table className="table">
                <thead>
                  <tr>
                    <th>機能カテゴリ</th>
                    <th>TS サポート</th>
                    <th>備考</th>
                  </tr>
                </thead>
                <tbody>
                  {featureSummary.map((feature, index) => (
                    <tr key={index}>
                      <td>{feature.category}</td>
                      <td>
                        <span className={classNames('chip', feature.tsSupport === '✅' && 'success', feature.tsSupport === '⚠️' && 'limited', feature.tsSupport === '❌' && 'unsupported')}>
                          {feature.tsSupport}
                        </span>
                      </td>
                      <td>{feature.notes}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {showHooksLog && (
        <div className="modal" onClick={() => setShowHooksLog(false)}>
          <div className="modal__card" onClick={(e) => e.stopPropagation()}>
            <div className="modal__head">
              <div className="sidebar__title">Hooks イベントログ</div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button className="btn" onClick={() => setShowHooksDescription(!showHooksDescription)}>
                  {showHooksDescription ? '説明を非表示' : '説明を表示'}
                </button>
                <button className="iconBtn" onClick={() => setShowHooksLog(false)} aria-label="閉じる">✕</button>
              </div>
            </div>
            <div className="modal__body">
              {showHooksDescription && (
                <div className="panel">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      code({ node, inline, className, children, ...props }: any) {
                        const match = /language-(\w+)/.exec(className || '')
                        const codeString = String(children).replace(/\n$/, '')
                        return !inline && match ? (
                          <SyntaxHighlighter
                            style={vscDarkPlus}
                            language={match[1]}
                            PreTag="div"
                            {...props}
                          >
                            {codeString}
                          </SyntaxHighlighter>
                        ) : (
                          <code className={className} {...props}>
                            {children}
                          </code>
                        )
                      },
                    }}
                  >
                    {HOOKS_DESCRIPTION}
                  </ReactMarkdown>
                </div>
              )}

              <div className="panel">
                <div className="field">
                  <label className="label">フィルタ</label>
                  <select
                    className="select"
                    value={hooksEventFilter}
                    onChange={(e) => setHooksEventFilter(e.target.value)}
                  >
                    <option value="all">すべて</option>
                    <option value="beforeInvocationEvent">Before Invocation</option>
                    <option value="afterInvocationEvent">After Invocation</option>
                    <option value="beforeModelCallEvent">Before Model Call</option>
                    <option value="afterModelCallEvent">After Model Call</option>
                    <option value="beforeToolCallEvent">Before Tool Call</option>
                    <option value="afterToolCallEvent">After Tool Call</option>
                    <option value="beforeToolsEvent">Before Tools</option>
                    <option value="afterToolsEvent">After Tools</option>
                    <option value="messageAddedEvent">Message Added</option>
                    <option value="agentInitializedEvent">Agent Initialized</option>
                  </select>
                </div>
                <div className="field">
                  <button className="btn" onClick={() => setHooksEvents([])}>クリア</button>
                </div>
              </div>

              <div className="log-list">
                {hooksEvents
                  .filter(event => hooksEventFilter === 'all' || event.type === hooksEventFilter)
                  .length === 0 ? (
                  <div className="empty">イベントがありません</div>
                ) : (
                  hooksEvents
                    .filter(event => hooksEventFilter === 'all' || event.type === hooksEventFilter)
                    .map((event, index) => (
                      <div key={`${event.timestamp}-${index}`} className="log-item">
                        <div className="log-item__head">
                          <span>{event.type.replace('Event', '')}</span>
                          <span>{formatTime(event.timestamp)}</span>
                        </div>
                        {event.data && (
                          <div className="log-item__body">
                            {JSON.stringify(event.data, null, 2)}
                          </div>
                        )}
                      </div>
                    ))
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App

