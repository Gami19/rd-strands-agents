# Strands Agents TypeScript SDK 

---

## 0. SDK の状態と前提

- **Experimental（実験的）段階**の SDK
  - Python SDK に比べて未実装機能が多い
  - 破壊的変更が入る可能性あり
- 対応ランタイム
  - Node.js 20+ 推奨
  - TypeScript / JavaScript から利用

---
## 機能サマリ（TypeScript 観点）

| 機能カテゴリ                    | TS サポート | 備考 |
|---------------------------------|------------|------|
| エージェント作成・実行          | ✅         | `Agent`, `invoke()` |
| カスタムツール（tool）          | ✅         | 関数 / クラス / async / streaming |
| Vended Tools                    | ✅         | `bash` など一部 |
| モデルプロバイダ                | ⚠️         | Bedrock / OpenAI / Custom のみ |
| ストリーミング（Async Iterator）| ✅         | `agent.stream()` |
| Callback Handlers（Streaming）  | ❌         | 公式に「Not supported」 |
| Hooks                           | ✅         | TS専用イベントあり |
| Agent State                     | ✅         | `agent.state`, `context.agent.state` |
| Request State                   | ❌         | Python のみ |
| Conversation Manager            | ✅         | Null / SlidingWindow、要約型は Python のみ |
| MCP Tools                       | ✅         | stdio / HTTP / SSE |
| Structured Output               | ❌         | Python のみ |
| Tool Executors                  | ❌         | Python のみ |
| Community Tools (`strands-agents-tools`) | ❌ | Python のみ |
| Guardrails / PII Redaction 等   | （未記載） | TS 向け記述なし（Python 側優先） |
| マルチエージェントパターン      | （未記載） | TS 向け記述なし |

## 対応モデル

| Provider         | Python | TypeScript |
|------------------|:------:|:----------:|
| Custom Providers | ✅     | ✅         |
| Amazon Bedrock   | ✅     | ✅         |
| OpenAI           | ✅     | ✅         |
| Amazon Nova      | ✅     | ❌         |
| Anthropic        | ✅     | ❌         |
| Gemini           | ✅     | ❌         |
| LiteLLM          | ✅     | ❌         |
| llama.cpp        | ✅     | ❌         |
| LlamaAPI         | ✅     | ❌         |
| MistralAI        | ✅     | ❌         |
| Ollama           | ✅     | ❌         |
| SageMaker        | ✅     | ❌         |
| Writer           | ✅     | ❌         |
| Cohere           | ✅     | ❌         |
| CLOVA Studio     | ✅     | ❌         |
| FireworksAI      | ✅     | ❌         |

**TypeScript で利用可能なのは:**

- Bedrock
- OpenAI
- Custom Providers
---

## 1. インストールとセットアップ

### 1.1 インストール

```bash
npm install @strands-agents/sdk
```

TypeScript 利用時:

```bash
npm install --save-dev typescript @types/node
```

ディレクトリ例:

```text
my-agent/
├── src/
│   └── agent.ts
├── package.json
└── README.md
```

---

## 2. 認証情報（Credentials）

### 2.1 デフォルトモデル

- デフォルトは **Amazon Bedrock + Claude 4 Sonnet**。

### 2.2 AWS 認証の設定

いずれかの方法で設定:

- 環境変数  
  `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`
- `aws configure` による設定
- IAM ロール（EC2 / ECS / Lambda など）
- Bedrock API キー: `AWS_BEARER_TOKEN_BEDROCK`

Bedrock コンソール側で **対象モデルへのアクセス許可を有効化** しておく必要があります。

---

## 3. クイックスタート

### 3.1 最小のエージェント

```ts
import { Agent } from '@strands-agents/sdk'

const agent = new Agent()

const result = await agent.invoke('Hello!')
console.log(result.lastMessage)
```

### 3.2 カスタムツール付きエージェント

```ts
import { Agent, tool } from '@strands-agents/sdk'
import z from 'zod'

const letterCounter = tool({
  name: 'letter_counter',
  description:
    'Count occurrences of a specific letter in a word. Performs case-insensitive matching.',
  inputSchema: z
    .object({
      word: z.string().describe('The input word to search in'),
      letter: z.string().describe('The specific letter to count'),
    })
    .refine((data) => data.letter.length === 1, {
      message: "The 'letter' parameter must be a single character",
    }),
  callback: (input) => {
    const { word, letter } = input
    const lowerWord = word.toLowerCase()
    const lowerLetter = letter.toLowerCase()

    let count = 0
    for (const c of lowerWord) if (c === lowerLetter) count++

    return `The letter '${letter}' appears ${count} time(s) in '${word}'`
  },
})

const agent = new Agent({
  tools: [letterCounter],
})

const msg = `Tell me how many letter R's are in the word "strawberry" 🍓`
const result = await agent.invoke(msg)
console.log(result.lastMessage)
```

実行例:

```bash
npx tsx src/agent.ts
```

---

## 4. プロンプト（Prompts）

### 4.1 システムプロンプト

```ts
const agent = new Agent({
  systemPrompt:
    'You are a financial advisor specialized in retirement planning. ' +
    'Use tools to gather information and provide personalized advice. ' +
    'Always explain your reasoning and cite sources when possible.',
})
```

### 4.2 ユーザープロンプト（テキスト）

```ts
const response = await agent.invoke('What is the time in Seattle?')
console.log(response.lastMessage)
```

### 4.3 マルチモーダル（テキスト + 画像）

```ts
import { readFileSync } from 'node:fs'
import { Agent, TextBlock, ImageBlock } from '@strands-agents/sdk'

const imageBytes = readFileSync('path/to/image.png')

const agent = new Agent()

const response = await agent.invoke([
  new TextBlock('What can you see in this image?'),
  new ImageBlock({
    format: 'png',
    source: { bytes: new Uint8Array(imageBytes) },
  }),
])
```

### 4.4 Direct Tool Calls

- **TypeScript: 未サポート**
- Python SDK には「ツールを直接呼び出す」APIがありますが、TS では利用できません。

---

## 5. 会話と状態管理（State & Conversation）

### 5.1 会話履歴（Conversation History）

```ts
const agent = new Agent()

await agent.invoke('Hello!')
console.log(agent.messages)
```

既存メッセージで初期化:

```ts
const agent = new Agent({
  messages: [
    { role: 'user', content: [{ text: 'Hello, my name is Strands!' }] },
    {
      role: 'assistant',
      content: [{ text: 'Hi there! How can I help you today?' }],
    },
  ],
})

await agent.invoke("What's my name?")
```

### 5.2 Conversation Manager

#### NullConversationManager

```ts
import { Agent, NullConversationManager } from '@strands-agents/sdk'

const agent = new Agent({
  conversationManager: new NullConversationManager(),
})
```

#### SlidingWindowConversationManager（デフォルト）

```ts
import {
  Agent,
  SlidingWindowConversationManager,
} from '@strands-agents/sdk'

const manager = new SlidingWindowConversationManager({
  windowSize: 40,
  shouldTruncateResults: true,
})

const agent = new Agent({ conversationManager: manager })
```

- 直近 N メッセージのみ保持
- コンテキストウィンドウ超過時に古いメッセージ / 大きなツール結果をトリミング

#### SummarizingConversationManager

- **TypeScript: 未サポート**（Python のみ）

### 5.3 Agent State（キー値ストア）

```ts
const agent = new Agent({
  state: { user_preferences: { theme: 'dark' }, session_count: 0 },
})

agent.state.set('last_action', 'login')
console.log(agent.state.get('user_preferences'))
agent.state.delete('last_action')
```

- JSON シリアライズ可能な値のみ格納可能。

### 5.4 ツールから State を読む

```ts
import { tool, ToolContext } from '@strands-agents/sdk'
import z from 'zod'

const apiCallTool = tool({
  name: 'api_call',
  description: 'Make an API call with user context',
  inputSchema: z.object({
    query: z.string().describe('The search query'),
  }),
  callback: async (input, context?: ToolContext) => {
    if (!context) throw new Error('Context is required')

    const userId = context.agent.state.get('userId') as string | undefined
    // userId をヘッダ用途などに利用
    // ...
    return { ok: true, userId, query: input.query }
  },
})
```

### 5.5 Request State

- **TypeScript: 未サポート**（Python のみ）

---

## 6. カスタムツール（tool()）

### 6.1 基本

```ts
import { tool } from '@strands-agents/sdk'
import z from 'zod'

const weatherTool = tool({
  name: 'weather_forecast',
  description: 'Get weather forecast for a city',
  inputSchema: z.object({
    city: z.string().describe('The name of the city'),
    days: z.number().default(3).describe('Number of days for the forecast'),
  }),
  callback: (input) => {
    return `Weather forecast for ${input.city} for the next ${input.days} days...`
  },
})
```

- `name` / `description` / `inputSchema` の **動的オーバーライドは TS では未サポート**（Python のみ）。

### 6.2 戻り値と ToolResult

- `string | number | boolean | null | object | array` など JSON シリアライズ可能な値は、自動で `ToolResultBlock` に変換。
- 例外は `status: "error"` な ToolResult に変換されます。

### 6.3 非同期 & ストリーミングツール

```ts
const asyncTool = tool({
  name: 'call_api',
  description: 'Call API asynchronously',
  inputSchema: z.object({}),
  callback: async () => {
    await new Promise((r) => setTimeout(r, 1000))
    return 'Done!'
  },
})

const streamingTool = tool({
  name: 'process_data',
  description: 'Process records',
  inputSchema: z.object({ records: z.number() }),
  callback: async function* (input: { records: number }) {
    for (let i = 0; i < input.records; i++) {
      if (i % 10 === 0) {
        yield `Processing ${i}/${input.records}`
      }
    }
    return `Completed ${input.records}`
  },
})
```

### 6.4 ToolContext

```ts
const getAgentInfoTool = tool({
  name: 'get_agent_info',
  description: 'Get information about the agent',
  inputSchema: z.object({}),
  callback: (input, context?: ToolContext) =>
    `Agent has ${context?.agent.messages.length} messages`,
})
```

- 引数名を変えるカスタムルール（Pythonの `tool_context` など）は TS では不要。  
  単に第2引数に `ToolContext` を受け取る。

---

## 7. モデルプロバイダ（Model Providers）

### 7.1 Bedrock / OpenAI 例

```ts
import { Agent } from '@strands-agents/sdk'
import { BedrockModel } from '@strands-agents/sdk/models/bedrock'
import { OpenAIModel } from '@strands-agents/sdk/models/openai'

// Bedrock
const bedrockModel = new BedrockModel({
  modelId: 'anthropic.claude-sonnet-4-20250514-v1:0',
  region: 'us-west-2',
  temperature: 0.3,
})

let agent = new Agent({ model: bedrockModel })
let response = await agent.invoke('What can you help me with?')

// OpenAI
const openaiModel = new OpenAIModel({
  apiKey: process.env.OPENAI_API_KEY,
  modelId: 'gpt-4o',
})

agent = new Agent({ model: openaiModel })
response = await agent.invoke('What can you help me with?')
```

---

## 8. カスタムモデルプロバイダ（Custom Model Providers）

- `Model` 抽象クラスを継承して、自作の LLM API クライアントを実装可能。
- `stream(messages, options)` / `getConfig()` / `updateConfig()` を実装する。

構造化出力（Structured Output）は:

- **TypeScript の Custom Provider では未サポート**（Python のみ）。

---

## 9. ストリーミング（Async Iterators）

### 9.1 agent.stream()

```ts
const agent = new Agent({ tools: [someTool], printer: false })

for await (const event of agent.stream('質問')) {
  if (
    event.type === 'modelContentBlockDeltaEvent' &&
    event.delta.type === 'textDelta'
  ) {
    process.stdout.write(event.delta.text)
  }
}
```

### 9.2 Express 連携例

```ts
import express from 'express'

const app = express()
app.use(express.json())

app.post('/stream', async (req, res) => {
  const { prompt } = req.body
  const agent = new Agent({ tools: [someTool], printer: false })

  for await (const event of agent.stream(prompt)) {
    res.write(`${JSON.stringify(event)}
`)
  }
  res.end()
})
```

### 9.3 Callback Handlers について

公式ドキュメントに明記:

> **Not supported in TypeScript**  
> TypeScript does not support callback handlers. For real-time event handling in TypeScript, use the async iterator pattern with `agent.stream()` or see Hooks for lifecycle event handling.

- **TS では callback handler 型のストリーミングは未サポート**。  
- 代わりに:
  - `agent.stream()`（Async Iterator）
  - Hooks（後述）

を利用します。

---

## 10. Hooks（フック）

TypeScript SDK は Hooks システムをサポートしています。

### 10.1 個別コールバック

```ts
import {
  Agent,
  BeforeInvocationEvent,
} from '@strands-agents/sdk'

const agent = new Agent()

agent.hooks.addCallback(BeforeInvocationEvent, (event) => {
  console.log('Custom callback triggered')
})
```

### 10.2 HookProvider

```ts
import {
  HookProvider,
  HookRegistry,
  BeforeInvocationEvent,
  AfterInvocationEvent,
} from '@strands-agents/sdk'

class LoggingHook implements HookProvider {
  registerCallbacks(registry: HookRegistry): void {
    registry.addCallback(BeforeInvocationEvent, () =>
      console.log('Request started'),
    )
    registry.addCallback(AfterInvocationEvent, () =>
      console.log('Request completed'),
    )
  }
}

const agent = new Agent({ hooks: [new LoggingHook()] })
agent.hooks.addHook(new LoggingHook())
```

### 10.3 利用可能なイベント

- `AgentInitializedEvent`
- `BeforeInvocationEvent` / `AfterInvocationEvent`
- `MessageAddedEvent`
- `BeforeModelCallEvent` / `AfterModelCallEvent`
- `BeforeToolCallEvent` / `AfterToolCallEvent`
- **`BeforeToolsEvent` / `AfterToolsEvent`（TypeScript only）**

### 10.4 TypeScript 限定イベント

- ツールをバッチ実行する前後に `BeforeToolsEvent` / `AfterToolsEvent` が発火。

### 10.5 Python のみの高度機能（TS 未サポート）

- Invocation State の注入・参照
- Hooks からのツール差し替え（Tool Interception）
- ツール結果の改変（Result Modification）

---

## 11. MCP Tools（Model Context Protocol）

TypeScript でも MCP ツールがサポートされています。

### 11.1 クイックスタート

```ts
import { Agent } from '@strands-agents/sdk'
import { McpClient } from '@strands-agents/sdk/tools/mcp' // 実際のパスは SDK に準拠
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js'

const mcpClient = new McpClient({
  transport: new StdioClientTransport({
    command: 'uvx',
    args: ['awslabs.aws-documentation-mcp-server@latest'],
  }),
})

const agent = new Agent({
  tools: [mcpClient],
})

await agent.invoke('What is AWS Lambda?')
```

### 11.2 複数トランスポート

- `StdioClientTransport`（ローカル CLI）
- `StreamableHTTPClientTransport`（HTTP ベースの MCP サーバ）
- `SSEClientTransport`（SSE サーバ）

### 11.3 複数 MCP サーバの利用

```ts
const agentMultiple = new Agent({
  tools: [localMcpClient, remoteMcpClient],
})
```

### 11.4 制限（TS）

- ツールフィルタリング・プレフィックス付与など、一部の高度機能は **Python のみ**。

---

## 12. Structured Output（構造化出力）

- **TypeScript: 未サポート**
- Pydantic ベースの Structured Output は Python SDK 限定機能。

TS で似たことをしたい場合:

- モデルに JSON 形式で出力させるようプロンプト設計
- `JSON.parse` + `zod` などでバリデーション

---