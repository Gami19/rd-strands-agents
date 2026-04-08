import { Router, Request, Response } from 'express';
import { readFileSync } from 'fs';
import { resolve } from 'path';
import { agent, resetAgent, initMcpClient, switchMcpClient, getMcpClients, getActiveMcpClient, getAgentState, setAgentState, deleteAgentState, resetAgentState, getConversationManagerConfig, setConversationManagerConfig } from '../agent';

const router = Router();

router.get('/test', (req: Request, res: Response) => {
  res.json({ message: 'API test endpoint' });
});

router.post('/agent/invoke', async (req: Request, res: Response) => {
  const startTime = Date.now();
  try {
    const { message } = req.body;
    
    if (!message || typeof message !== 'string') {
      console.log('[API] /agent/invoke - Invalid request: message is missing or not a string');
      return res.status(400).json({ error: 'Message is required and must be a string' });
    }

    const messagePreview = message.length > 100 ? message.substring(0, 100) + '...' : message;
    console.log(`[API] /agent/invoke - Received message: "${messagePreview}"`);
    console.log(`[API] /agent/invoke - Starting agent invocation...`);

    const result = await agent.invoke(message);
    
    const duration = Date.now() - startTime;
    console.log(`[API] /agent/invoke - Agent invocation completed in ${duration}ms`);
    const responseText = typeof result.lastMessage === 'string' ? result.lastMessage : JSON.stringify(result.lastMessage);
    console.log(`[API] /agent/invoke - Response length: ${responseText.length} characters`);
    
    res.json({
      response: result.lastMessage,
      messages: agent.messages,
    });
  } catch (error) {
    const duration = Date.now() - startTime;
    console.error(`[API] /agent/invoke - Error after ${duration}ms:`, error);
    console.error('[API] /agent/invoke - Error details:', error instanceof Error ? error.message : 'Unknown error');
    res.status(500).json({ 
      error: 'Failed to invoke agent',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

function serializeEvent(event: any): any {
  const serialized: any = {
    type: event.type,
  };

  if (event.delta) {
    serialized.delta = {
      type: event.delta.type,
      text: event.delta.text,
      textDelta: event.delta.textDelta,
    };
  }

  if (event.start) {
    serialized.start = {
      type: event.start.type,
      name: event.start.name,
    };
  }

  if (event.stopData) {
    serialized.stopData = {
      message: event.stopData.message ? {
        role: event.stopData.message.role,
        content: event.stopData.message.content,
      } : undefined,
    };
  }

  if (event.textDelta !== undefined) {
    serialized.textDelta = event.textDelta;
  }

  if (event.lastMessage !== undefined) {
    serialized.lastMessage = event.lastMessage;
  }

  return serialized;
}

router.post('/agent/stream', async (req: Request, res: Response) => {
  const startTime = Date.now();
  let eventCount = 0;
  let accumulatedResponse = '';
  try {
    const { message } = req.body;
    
    if (!message || typeof message !== 'string') {
      console.log('[API] /agent/stream - Invalid request: message is missing or not a string');
      return res.status(400).json({ error: 'Message is required and must be a string' });
    }

    const messagePreview = message.length > 100 ? message.substring(0, 100) + '...' : message;
    console.log(`[API] /agent/stream - Received message: "${messagePreview}"`);
    console.log(`[API] /agent/stream - Starting streaming...`);
    console.log(`[API] /agent/stream - Streaming response:`);
    console.log('─'.repeat(80));

    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');

    for await (const event of agent.stream(message)) {
      try {
        eventCount++;
        
        if (event.type === 'beforeInvocationEvent') {
          console.log(`[API] /agent/stream - Event #${eventCount}: beforeInvocationEvent - Agent loop initialized`);
        } else if (event.type === 'beforeModelCallEvent') {
          console.log(`[API] /agent/stream - Event #${eventCount}: beforeModelCallEvent - Model call starting`);
        } else if (event.type === 'afterModelCallEvent') {
          console.log(`[API] /agent/stream - Event #${eventCount}: afterModelCallEvent - Model call completed`);
        } else if (event.type === 'beforeToolsEvent') {
          console.log(`[API] /agent/stream - Event #${eventCount}: beforeToolsEvent - Tools execution starting`);
        } else if (event.type === 'afterToolsEvent') {
          console.log(`[API] /agent/stream - Event #${eventCount}: afterToolsEvent - Tools execution completed`);
        } else if (event.type === 'afterInvocationEvent') {
          console.log(`[API] /agent/stream - Event #${eventCount}: afterInvocationEvent - Agent loop completed`);
        } else if (event.type === 'modelContentBlockDeltaEvent') {
          const eventAny = event as any;
          const textDelta = eventAny.delta?.textDelta || eventAny.textDelta || eventAny.delta?.text || '';
          if (textDelta && typeof textDelta === 'string') {
            accumulatedResponse += textDelta;
            process.stdout.write(textDelta);
          }
        }
        
        const serialized = serializeEvent(event);
        const data = JSON.stringify(serialized);
        res.write(`data: ${data}\n\n`);
      } catch (serializeError) {
        console.error(`[API] /agent/stream - Event serialization error at event #${eventCount}:`, serializeError);
      }
    }

    console.log('\n' + '─'.repeat(80));
    const duration = Date.now() - startTime;
    console.log(`[API] /agent/stream - Streaming completed in ${duration}ms - Total events: ${eventCount}`);
    console.log(`[API] /agent/stream - Total response length: ${accumulatedResponse.length} characters`);
    res.end();
  } catch (error) {
    const duration = Date.now() - startTime;
    console.error(`\n[API] /agent/stream - Error after ${duration}ms (${eventCount} events processed):`, error);
    console.error('[API] /agent/stream - Error details:', error instanceof Error ? error.message : 'Unknown error');
    const errorData = JSON.stringify({
      type: 'error',
      error: error instanceof Error ? error.message : 'Unknown error',
    });
    res.write(`data: ${errorData}\n\n`);
    res.end();
  }
});

router.post('/agent/reset', async (req: Request, res: Response) => {
  try {
    console.log('[API] /agent/reset - Resetting agent conversation history...');
    resetAgent();
    console.log('[API] /agent/reset - Agent conversation history cleared successfully');
    res.json({ success: true, message: 'Conversation history cleared' });
  } catch (error) {
    console.error('[API] /agent/reset - Error:', error);
    console.error('[API] /agent/reset - Error details:', error instanceof Error ? error.message : 'Unknown error');
    res.status(500).json({ 
      error: 'Failed to reset conversation',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

router.get('/mcp/list', async (req: Request, res: Response) => {
  try {
    console.log('[API] /mcp/list - Getting MCP clients list...');
    const clients = getMcpClients();
    const activeClient = getActiveMcpClient();
    
    const clientList = clients.map(client => ({
      id: client.id,
      name: client.name,
      type: client.type,
      createdAt: client.createdAt.toISOString(),
      isActive: activeClient?.id === client.id,
    }));
    
    console.log(`[API] /mcp/list - Found ${clients.length} MCP clients`);
    res.json({ clients: clientList, activeId: activeClient?.id || null });
  } catch (error) {
    console.error('[API] /mcp/list - Error:', error);
    res.status(500).json({ 
      error: 'Failed to get MCP clients',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

router.post('/mcp/init', async (req: Request, res: Response) => {
  try {
    const { name, type, config } = req.body;
    
    if (!name || typeof name !== 'string') {
      console.log('[API] /mcp/init - Invalid request: name is missing or not a string');
      return res.status(400).json({ error: 'Name is required and must be a string' });
    }
    
    if (!type || !['stdio', 'http', 'sse'].includes(type)) {
      console.log('[API] /mcp/init - Invalid request: type must be stdio, http, or sse');
      return res.status(400).json({ error: 'Type must be stdio, http, or sse' });
    }
    
    if (!config || typeof config !== 'object') {
      console.log('[API] /mcp/init - Invalid request: config is missing or not an object');
      return res.status(400).json({ error: 'Config is required and must be an object' });
    }
    
    console.log(`[API] /mcp/init - Initializing MCP client: ${name} (${type})`);
    const mcpId = await initMcpClient(name, type, config);
    console.log(`[API] /mcp/init - MCP client initialized successfully: ${mcpId}`);
    
    res.json({ success: true, mcpId, message: 'MCP client initialized successfully' });
  } catch (error) {
    console.error('[API] /mcp/init - Error:', error);
    console.error('[API] /mcp/init - Error details:', error instanceof Error ? error.message : 'Unknown error');
    res.status(500).json({ 
      error: 'Failed to initialize MCP client',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

router.post('/mcp/switch', async (req: Request, res: Response) => {
  try {
    const { mcpId } = req.body;
    
    if (mcpId !== null && (typeof mcpId !== 'string' || mcpId.trim() === '')) {
      console.log('[API] /mcp/switch - Invalid request: mcpId must be a string or null');
      return res.status(400).json({ error: 'mcpId must be a string or null' });
    }
    
    const targetId = mcpId === null ? null : mcpId.trim();
    console.log(`[API] /mcp/switch - Switching MCP client to: ${targetId || 'none'}`);
    
    const availableClients = getMcpClients();
    console.log(`[API] /mcp/switch - Available MCP clients: ${availableClients.length}`);
    availableClients.forEach(client => {
      console.log(`[API] /mcp/switch -   - ${client.name} (${client.id}) [${client.type}]`);
    });
    
    switchMcpClient(targetId);
    const activeClient = getActiveMcpClient();
    
    console.log(`[API] /mcp/switch - MCP client switched successfully`);
    res.json({ 
      success: true, 
      activeId: activeClient?.id || null,
      message: activeClient ? `Switched to ${activeClient.name}` : 'MCP client deactivated'
    });
  } catch (error) {
    console.error('[API] /mcp/switch - Error:', error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    console.error('[API] /mcp/switch - Error details:', errorMessage);
    
    const availableClients = getMcpClients();
    const availableClientsList = availableClients.map(c => ({
      id: c.id,
      name: c.name,
      type: c.type
    }));
    
    res.status(500).json({ 
      error: 'Failed to switch MCP client',
      details: errorMessage,
      availableClients: availableClientsList,
      hint: availableClients.length === 0 
        ? 'No MCP clients are available. Please initialize an MCP client first or check mcp-servers.json configuration.'
        : 'Please check if the MCP client ID is correct. Use GET /api/mcp/list to see available clients.'
    });
  }
});

router.get('/mcp/active', async (req: Request, res: Response) => {
  try {
    console.log('[API] /mcp/active - Getting active MCP client...');
    const activeClient = getActiveMcpClient();
    
    if (activeClient) {
      res.json({
        id: activeClient.id,
        name: activeClient.name,
        type: activeClient.type,
        createdAt: activeClient.createdAt.toISOString(),
      });
    } else {
      res.json({ id: null, name: null, type: null, createdAt: null });
    }
  } catch (error) {
    console.error('[API] /mcp/active - Error:', error);
    res.status(500).json({ 
      error: 'Failed to get active MCP client',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

router.get('/agent/state', async (req: Request, res: Response) => {
  try {
    console.log('[API] /agent/state - Getting agent state...');
    const state = getAgentState();
    console.log(`[API] /agent/state - Found ${Object.keys(state).length} state entries`);
    res.json({ state });
  } catch (error) {
    console.error('[API] /agent/state - Error:', error);
    res.status(500).json({ 
      error: 'Failed to get agent state',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

router.post('/agent/state', async (req: Request, res: Response) => {
  try {
    const { key, value } = req.body;
    
    if (!key || typeof key !== 'string') {
      console.log('[API] /agent/state - Invalid request: key is missing or not a string');
      return res.status(400).json({ error: 'Key is required and must be a string' });
    }
    
    if (value === undefined) {
      console.log('[API] /agent/state - Invalid request: value is missing');
      return res.status(400).json({ error: 'Value is required' });
    }
    
    console.log(`[API] /agent/state - Setting state: ${key}`);
    setAgentState(key, value);
    res.json({ success: true, message: `State set: ${key}` });
  } catch (error) {
    console.error('[API] /agent/state - Error:', error);
    res.status(500).json({ 
      error: 'Failed to set agent state',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

router.delete('/agent/state/:key', async (req: Request, res: Response) => {
  try {
    const { key } = req.params;
    
    if (!key) {
      console.log('[API] /agent/state/:key - Invalid request: key is missing');
      return res.status(400).json({ error: 'Key is required' });
    }
    
    console.log(`[API] /agent/state/:key - Deleting state: ${key}`);
    deleteAgentState(key);
    res.json({ success: true, message: `State deleted: ${key}` });
  } catch (error) {
    console.error('[API] /agent/state/:key - Error:', error);
    res.status(500).json({ 
      error: 'Failed to delete agent state',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

router.post('/agent/state/reset', async (req: Request, res: Response) => {
  try {
    console.log('[API] /agent/state/reset - Resetting agent state...');
    resetAgentState();
    console.log('[API] /agent/state/reset - Agent state reset completed');
    res.json({ success: true, message: 'Agent state reset completed' });
  } catch (error) {
    console.error('[API] /agent/state/reset - Error:', error);
    res.status(500).json({ 
      error: 'Failed to reset agent state',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

router.get('/agent/conversation-manager', async (req: Request, res: Response) => {
  try {
    console.log('[API] /agent/conversation-manager - Getting Conversation Manager config...');
    const config = getConversationManagerConfig();
    console.log(`[API] /agent/conversation-manager - Current config: ${config.type}`);
    res.json({ config });
  } catch (error) {
    console.error('[API] /agent/conversation-manager - Error:', error);
    res.status(500).json({ 
      error: 'Failed to get Conversation Manager config',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

router.post('/agent/conversation-manager', async (req: Request, res: Response) => {
  try {
    const { type, windowSize, shouldTruncateResults } = req.body;
    
    if (!type || !['null', 'slidingWindow'].includes(type)) {
      console.log('[API] /agent/conversation-manager - Invalid request: type must be null or slidingWindow');
      return res.status(400).json({ error: 'Type must be null or slidingWindow' });
    }
    
    const config: any = { type };
    
    if (type === 'slidingWindow') {
      if (windowSize !== undefined) {
        if (typeof windowSize !== 'number' || windowSize < 1) {
          return res.status(400).json({ error: 'windowSize must be a positive number' });
        }
        config.windowSize = windowSize;
      } else {
        config.windowSize = 40;
      }
      
      if (shouldTruncateResults !== undefined) {
        if (typeof shouldTruncateResults !== 'boolean') {
          return res.status(400).json({ error: 'shouldTruncateResults must be a boolean' });
        }
        config.shouldTruncateResults = shouldTruncateResults;
      } else {
        config.shouldTruncateResults = true;
      }
    }
    
    console.log(`[API] /agent/conversation-manager - Setting Conversation Manager: ${type}`);
    setConversationManagerConfig(config);
    console.log(`[API] /agent/conversation-manager - Conversation Manager updated successfully`);
    
    res.json({ success: true, config, message: `Conversation Manager set to ${type}` });
  } catch (error) {
    console.error('[API] /agent/conversation-manager - Error:', error);
    res.status(500).json({ 
      error: 'Failed to set Conversation Manager',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

export default router;