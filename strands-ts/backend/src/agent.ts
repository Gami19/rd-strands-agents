import { Agent, tool, McpClient, NullConversationManager, SlidingWindowConversationManager } from '@strands-agents/sdk';
import { httpRequest } from '@strands-agents/sdk/vended_tools/http_request';
import { SSEClientTransport } from '@modelcontextprotocol/sdk/client/sse.js';
import z from 'zod';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

let agent: Agent;

const letterCounter = tool({
  name: 'letter_counter',
  description: 'Count occurrences of a specific letter in a word. Performs case-insensitive matching.',
  inputSchema: z.object({
    word: z.string().describe('The input word to search in'),
    letter: z.string().length(1).describe('The specific letter to count'),
  }) as any,
  callback: (input: { word: string; letter: string }) => {
    const { word, letter } = input;
    const lowerWord = word.toLowerCase();
    const lowerLetter = letter.toLowerCase();
    let count = 0;
    for (const char of lowerWord) {
      if (char === lowerLetter) {
        count++;
      }
    }
    return `The letter '${letter}' appears ${count} time(s) in '${word}'`;
  },
});

interface NotebookState {
  [name: string]: string;
}

const notebookInputSchema = z
  .object({
    mode: z
      .enum(['create', 'list', 'read', 'write', 'clear'])
      .describe('The operation to perform: `create`, `list`, `read`, `write`, `clear`.'),
    name: z.string().optional().describe('Name of the notebook to operate on. Defaults to "default".'),
    newStr: z.string().optional().describe('New string for replacement or insertion operations.'),
    readRange: z
      .array(z.number())
      .optional()
      .describe('Optional parameter of `read` command. Line range to show [start, end]. Supports negative indices.'),
    oldStr: z.string().optional().describe('String to replace in write mode when doing text replacement.'),
    insertLine: z
      .union([z.string(), z.number()])
      .optional()
      .describe(
        'Line number (int) or search text (str) for insertion point in write mode. Supports negative indices.'
      ),
  })
  .refine(
    (data) => {
      if (data.mode === 'write') {
        const hasReplacement = data.oldStr !== undefined && data.newStr !== undefined;
        const hasInsertion = data.insertLine !== undefined && data.newStr !== undefined;
        return hasReplacement || hasInsertion;
      }
      return true;
    },
    {
      message:
        'Write operation requires either (oldStr + newStr) for replacement or (insertLine + newStr) for insertion',
    }
  );

const notebook = tool({
  name: 'notebook',
  description:
    'Manages text notebooks for note-taking and documentation. Supports create, list, read, write (replace or insert), and clear operations. Notebooks persist within the agent invocation.',
  inputSchema: notebookInputSchema as any,
  callback: (input: any, context: any) => {
    if (!context?.agent?.state) {
      throw new Error('Agent state is not initialized');
    }

    const notebooks: NotebookState = (context.agent.state.get('notebooks') as NotebookState | undefined) || {};
    if (Object.keys(notebooks).length === 0) {
      notebooks.default = '';
    }

    let result: string;
    const name = (input.name ?? 'default') as string;

    switch (input.mode) {
      case 'create':
        result = handleCreate(notebooks, name, input.newStr);
        break;
      case 'list':
        result = handleList(notebooks);
        break;
      case 'read':
        result = handleRead(notebooks, name, input.readRange);
        break;
      case 'write':
        result = handleWrite(notebooks, name, input.oldStr, input.newStr, input.insertLine);
        break;
      case 'clear':
        result = handleClear(notebooks, name);
        break;
      default:
        throw new Error(`Unknown mode: ${input.mode}`);
    }

    context.agent.state.set('notebooks', notebooks);
    return result;
  },
});

const handleCreate = (notebooks: Record<string, string>, name: string, newStr?: string): string => {
  notebooks[name] = newStr ?? '';
  return `Created notebook '${name}'${newStr ? ' with specified content' : ' (empty)'}`;
};

const handleList = (notebooks: Record<string, string>): string => {
  const notebookNames = Object.keys(notebooks);
  if (notebookNames.length === 0) {
    return 'No notebooks available';
  }

  const details = notebookNames
    .map((nbName) => {
      const lineCount = notebooks[nbName] ? notebooks[nbName].split('\n').length : 0;
      const status = lineCount === 0 ? 'Empty' : `${lineCount} lines`;
      return `- ${nbName}: ${status}`;
    })
    .join('\n');

  return `Available notebooks:\n${details}`;
};

const handleRead = (notebooks: Record<string, string>, name: string, readRange?: number[]): string => {
  if (!(name in notebooks)) {
    throw new Error(`Notebook '${name}' not found`);
  }

  const content = notebooks[name]!;
  if (!readRange) {
    return content || `Notebook '${name}' is empty`;
  }

  const lines = content.split('\n');
  let start = readRange[0];
  let end = readRange[1];

  if (start === undefined || end === undefined) {
    throw new Error('`readRange` must be a list of two integers: `[start, end]`');
  }

  if (start < 0) {
    start = lines.length + start + 1;
  }
  if (end < 0) {
    end = lines.length + end + 1;
  }

  const selectedLines: string[] = [];
  for (let lineNum = start; lineNum <= end; lineNum++) {
    if (lineNum >= 1 && lineNum <= lines.length) {
      selectedLines.push(`${lineNum}: ${lines[lineNum - 1]}`);
    }
  }

  return selectedLines.length > 0 ? selectedLines.join('\n') : 'No valid lines found in range';
};

const handleWrite = (
  notebooks: Record<string, string>,
  name: string,
  oldStr?: string,
  newStr?: string,
  insertLine?: string | number
): string => {
  if (!(name in notebooks)) {
    throw new Error(`Notebook '${name}' not found`);
  }

  if (oldStr !== undefined && newStr !== undefined) {
    if (!notebooks[name]!.includes(oldStr)) {
      throw new Error(`String '${oldStr}' not found in notebook '${name}'`);
    }
    notebooks[name] = notebooks[name]!.replace(oldStr, newStr);
    return `Replaced text in notebook '${name}'`;
  }

  if (insertLine !== undefined && newStr !== undefined) {
    const lines = notebooks[name]!.split('\n');
    let lineNum: number;

    if (typeof insertLine === 'string') {
      lineNum = lines.findIndex((line) => line.includes(insertLine));
      if (lineNum === -1) {
        throw new Error(`Text '${insertLine}' not found in notebook '${name}'`);
      }
    } else {
      lineNum = insertLine < 0 ? lines.length + insertLine : insertLine - 1;
    }

    if (lineNum < -1 || lineNum > lines.length) {
      throw new Error('Line number out of range');
    }

    lines.splice(lineNum + 1, 0, newStr);
    notebooks[name] = lines.join('\n');
    return `Inserted text at line ${lineNum + 2} in notebook '${name}'`;
  }

  throw new Error('Invalid write operation');
};

const handleClear = (notebooks: Record<string, string>, name: string): string => {
  if (!(name in notebooks)) {
    throw new Error(`Notebook '${name}' not found`);
  }
  notebooks[name] = '';
  return `Cleared notebook '${name}'`;
};

interface McpClientInfo {
  id: string;
  name: string;
  type: 'stdio' | 'http' | 'sse';
  client: McpClient;
  createdAt: Date;
}

const mcpClients: Map<string, McpClientInfo> = new Map();
let activeMcpId: string | null = null;

interface McpServerConfig {
  name: string;
  type: 'stdio' | 'http' | 'sse';
  config: {
    command?: string;
    args?: string[];
    url?: string;
  };
}

const loadMcpServersFromConfig = async (): Promise<void> => {
  const __filename = fileURLToPath(import.meta.url);
  const __dirname = dirname(__filename);
  const configPath = resolve(__dirname, '../mcp-servers.json');

  try {
    const fileContent = readFileSync(configPath, 'utf-8');
    const configs: McpServerConfig[] = JSON.parse(fileContent);

    if (!Array.isArray(configs)) {
      console.warn('[MCP] mcp-servers.json is not an array, skipping...');
      return;
    }

    console.log(`[MCP] Loading ${configs.length} MCP server(s) from config file...`);

    let successCount = 0;
    let failureCount = 0;

    for (const config of configs) {
      try {
        if (!config.name || !config.type || !config.config) {
          console.error(`[MCP] Invalid MCP server config: missing required fields`);
          console.error(`[MCP]   Config:`, JSON.stringify(config, null, 2));
          failureCount++;
          continue;
        }

        if (!['stdio', 'http', 'sse'].includes(config.type)) {
          console.error(`[MCP] Invalid MCP server type: ${config.type}`);
          console.error(`[MCP]   Valid types are: stdio, http, sse`);
          console.error(`[MCP]   Config:`, JSON.stringify(config, null, 2));
          failureCount++;
          continue;
        }

        if (config.type === 'stdio' && (!config.config.command || !config.config.args || !Array.isArray(config.config.args))) {
          console.error(`[MCP] Invalid stdio config: command and args (array) are required`);
          console.error(`[MCP]   Config:`, JSON.stringify(config, null, 2));
          failureCount++;
          continue;
        }

        if ((config.type === 'http' || config.type === 'sse') && !config.config.url) {
          console.error(`[MCP] Invalid ${config.type} config: url is required`);
          console.error(`[MCP]   Config:`, JSON.stringify(config, null, 2));
          failureCount++;
          continue;
        }

        const mcpId = await initMcpClient(config.name, config.type, config.config);
        console.log(`[MCP] Successfully loaded MCP server from config: ${config.name} (${mcpId})`);
        successCount++;
      } catch (error) {
        console.error(`[MCP] Failed to load MCP server from config: ${config.name}`);
        console.error(`[MCP]   Error:`, error instanceof Error ? error.message : error);
        console.error(`[MCP]   Config:`, JSON.stringify(config, null, 2));
        failureCount++;
      }
    }

    console.log(`[MCP] Finished loading MCP servers from config file: ${successCount} succeeded, ${failureCount} failed`);
  } catch (error: any) {
    if (error.code === 'ENOENT') {
      console.log('[MCP] mcp-servers.json not found, skipping config file loading');
    } else if (error instanceof SyntaxError) {
      console.error('[MCP] Failed to parse mcp-servers.json:', error.message);
    } else {
      console.error('[MCP] Failed to load mcp-servers.json:', error);
    }
  }
};

const baseTools = [letterCounter, notebook, httpRequest];

type ConversationManagerType = 'null' | 'slidingWindow';

interface ConversationManagerConfig {
  type: ConversationManagerType;
  windowSize?: number;
  shouldTruncateResults?: boolean;
}

let conversationManagerConfig: ConversationManagerConfig = {
  type: 'slidingWindow',
  windowSize: 40,
  shouldTruncateResults: true,
};

const createConversationManager = (config: ConversationManagerConfig) => {
  if (config.type === 'null') {
    return new NullConversationManager();
  } else {
    return new SlidingWindowConversationManager({
      windowSize: config.windowSize || 40,
      shouldTruncateResults: config.shouldTruncateResults !== undefined ? config.shouldTruncateResults : true,
    });
  }
};

const snapshotAgentState = (): Record<string, any> => {
  const result: Record<string, any> = {};
  try {
    if (!agent.state) {
      return result;
    }

    const stateAny = agent.state as any;
    if (typeof stateAny.entries === 'function') {
      for (const [key, value] of stateAny.entries()) {
        result[key] = value;
      }
    } else if (typeof stateAny.forEach === 'function') {
      stateAny.forEach((value: any, key: string) => {
        result[key] = value;
      });
    } else {
      Object.assign(result, stateAny);
    }
  } catch (error) {
    console.warn('[Agent] Failed to snapshot agent state:', error instanceof Error ? error.message : error);
  }
  return result;
};

agent = new Agent({
  tools: [...baseTools],
  printer: false,
  conversationManager: createConversationManager(conversationManagerConfig),
});

console.log('[Agent] Agent initialized with tools: letterCounter, notebook, http_request');
console.log('[Agent] Agent configuration: printer=false');
console.log(`[Agent] Conversation Manager: ${conversationManagerConfig.type}`);

const updateAgentTools = () => {
  const tools: any[] = [...baseTools];
  
  if (activeMcpId && mcpClients.has(activeMcpId)) {
    const mcpInfo = mcpClients.get(activeMcpId)!;
    tools.push(mcpInfo.client);
    console.log(`[Agent] Adding MCP client to tools: ${mcpInfo.name} (${mcpInfo.id})`);
  }
  
  const previousMessages = agent.messages;
  const previousState = snapshotAgentState();
  agent = new Agent({
    tools,
    printer: false,
    messages: previousMessages,
    state: previousState,
    conversationManager: createConversationManager(conversationManagerConfig),
  });
  console.log(`[Agent] Agent tools updated. Total tools: ${tools.length}`);
};

export const getConversationManagerConfig = (): ConversationManagerConfig => {
  return { ...conversationManagerConfig };
};

export const setConversationManagerConfig = (config: ConversationManagerConfig): void => {
  conversationManagerConfig = { ...config };
  const previousMessages = agent.messages;
  const previousState = snapshotAgentState();
  const tools: any[] = [...baseTools];
  
  if (activeMcpId && mcpClients.has(activeMcpId)) {
    const mcpInfo = mcpClients.get(activeMcpId)!;
    tools.push(mcpInfo.client);
  }
  
  agent = new Agent({
    tools,
    printer: false,
    messages: previousMessages,
    state: previousState,
    conversationManager: createConversationManager(conversationManagerConfig),
  });
  console.log(`[Agent] Conversation Manager updated: ${conversationManagerConfig.type}`);
  if (conversationManagerConfig.type === 'slidingWindow') {
    console.log(`[Agent]   windowSize: ${conversationManagerConfig.windowSize}, shouldTruncateResults: ${conversationManagerConfig.shouldTruncateResults}`);
  }
};

export const initMcpClient = async (
  name: string,
  type: 'stdio' | 'http' | 'sse',
  config: { command?: string; args?: string[]; url?: string }
): Promise<string> => {
  const id = `mcp_${Date.now()}_${Math.random().toString(36).substring(7)}`;
  let client: McpClient;

  try {
    if (type === 'stdio') {
      if (!config.command || !config.args) {
        throw new Error('Stdio transport requires command and args');
      }
      const { StdioClientTransport } = await import('@modelcontextprotocol/sdk/client/stdio.js');
      const transport = new StdioClientTransport({
        command: config.command,
        args: config.args,
      });
      
      client = new McpClient({
        transport,
      });
      
      console.log(`[MCP] Initialized stdio client: ${name} with command: ${config.command} ${config.args.join(' ')}`);
      console.log(`[MCP] Note: Connection will be established when first used`);
    } else if (type === 'http') {
      if (!config.url) {
        throw new Error('HTTP transport requires url');
      }
      const sdkModule = await import('@strands-agents/sdk');
      if ('StreamableHTTPClientTransport' in sdkModule) {
        const StreamableHTTPClientTransport = (sdkModule as any).StreamableHTTPClientTransport;
        client = new McpClient({
          transport: new StreamableHTTPClientTransport(new URL(config.url)) as any,
        });
        console.log(`[MCP] Initialized HTTP client: ${name} with URL: ${config.url}`);
        
        try {
          await client.connect();
          console.log(`[MCP] Connected to MCP server: ${name}`);
        } catch (connectError) {
          console.error(`[MCP] Failed to connect to MCP server: ${name}`, connectError);
          throw new Error(`Failed to connect to MCP server: ${connectError instanceof Error ? connectError.message : 'Unknown error'}`);
        }
      } else {
        throw new Error('HTTP transport is not available in the SDK. Please use SSE transport instead.');
      }
    } else if (type === 'sse') {
      if (!config.url) {
        throw new Error('SSE transport requires url');
      }
      client = new McpClient({
        transport: new SSEClientTransport(new URL(config.url)),
      });
      console.log(`[MCP] Initialized SSE client: ${name} with URL: ${config.url}`);
      
      try {
        await client.connect();
        console.log(`[MCP] Connected to MCP server: ${name}`);
      } catch (connectError) {
        console.error(`[MCP] Failed to connect to MCP server: ${name}`, connectError);
        throw new Error(`Failed to connect to MCP server: ${connectError instanceof Error ? connectError.message : 'Unknown error'}`);
      }
    } else {
      throw new Error(`Unsupported transport type: ${type}`);
    }

    const mcpInfo: McpClientInfo = {
      id,
      name,
      type,
      client,
      createdAt: new Date(),
    };

    mcpClients.set(id, mcpInfo);
    console.log(`[MCP] MCP client registered: ${name} (${id})`);
    
    return id;
  } catch (error) {
    console.error(`[MCP] Failed to initialize MCP client: ${name}`, error);
    throw error;
  }
};

export const switchMcpClient = (mcpId: string | null): void => {
  if (mcpId === null) {
    activeMcpId = null;
    console.log('[MCP] Deactivated MCP client');
  } else if (mcpClients.has(mcpId)) {
    activeMcpId = mcpId;
    const mcpInfo = mcpClients.get(mcpId)!;
    console.log(`[MCP] Switched to MCP client: ${mcpInfo.name} (${mcpId})`);
  } else {
    const availableClients = Array.from(mcpClients.values()).map(c => ({
      id: c.id,
      name: c.name,
      type: c.type
    }));
    console.error(`[MCP] MCP client not found: ${mcpId}`);
    console.error(`[MCP] Available MCP clients:`, availableClients);
    throw new Error(
      `MCP client not found: ${mcpId}. ` +
      `Available clients: ${availableClients.length > 0 
        ? availableClients.map(c => `${c.name} (${c.id})`).join(', ')
        : 'none'}`
    );
  }
  updateAgentTools();
};

export const getMcpClients = (): McpClientInfo[] => {
  return Array.from(mcpClients.values());
};

export const getActiveMcpClient = (): McpClientInfo | null => {
  if (activeMcpId && mcpClients.has(activeMcpId)) {
    return mcpClients.get(activeMcpId)!;
  }
  return null;
};

export const resetAgent = () => {
  console.log('[Agent] Resetting agent instance...');
  const previousState = snapshotAgentState();
  const tools: any[] = [...baseTools];
  
  if (activeMcpId && mcpClients.has(activeMcpId)) {
    const mcpInfo = mcpClients.get(activeMcpId)!;
    tools.push(mcpInfo.client);
  }
  
  agent = new Agent({
    tools,
    printer: false,
    state: previousState,
    conversationManager: createConversationManager(conversationManagerConfig),
  });
  console.log('[Agent] Agent instance reset completed');
};

export const getAgentState = (): Record<string, any> => {
  if (!agent.state) {
    return {};
  }
  const state: Record<string, any> = {};
  
  if (typeof (agent.state as any).entries === 'function') {
    for (const [key, value] of (agent.state as any).entries()) {
      state[key] = value;
    }
  } else if (typeof (agent.state as any).forEach === 'function') {
    (agent.state as any).forEach((value: any, key: string) => {
      state[key] = value;
    });
  } else {
    const entries = Object.entries(agent.state as any);
    for (const [key, value] of entries) {
      state[key] = value;
    }
  }
  
  return state;
};

export const setAgentState = (key: string, value: any): void => {
  if (!agent.state) {
    throw new Error('Agent state is not initialized');
  }
  try {
    JSON.stringify(value);
    agent.state.set(key, value);
    console.log(`[Agent] State set: ${key} = ${JSON.stringify(value)}`);
  } catch (error) {
    throw new Error(`Value is not JSON serializable: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
};

export const deleteAgentState = (key: string): void => {
  if (!agent.state) {
    throw new Error('Agent state is not initialized');
  }
  agent.state.delete(key);
  console.log(`[Agent] State deleted: ${key}`);
};

export const resetAgentState = (): void => {
  if (!agent.state) {
    return;
  }
  const keys = Array.from(agent.state.keys());
  for (const key of keys) {
    agent.state.delete(key);
  }
  console.log('[Agent] State reset completed');
};

loadMcpServersFromConfig().catch((error) => {
  console.error('[MCP] Error loading MCP servers from config:', error);
});

export { agent };

