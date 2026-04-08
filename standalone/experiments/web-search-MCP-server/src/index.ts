#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';
import * as cheerio from 'cheerio';

interface SearchResult {
  title: string;
  url: string;
  description: string;
}

const isValidSearchArgs = (args: any): args is { query: string; limit?: number } =>
  typeof args === 'object' &&
  args !== null &&
  typeof args.query === 'string' &&
  (args.limit === undefined || typeof args.limit === 'number');

class WebSearchServer {
  private server: Server;

  constructor() {
    this.server = new Server(
      {
        name: 'web-search',
        version: '0.1.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupToolHandlers();
    
    this.server.onerror = (error) => console.error('[MCP Error]', error);
    process.on('SIGINT', async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  private setupToolHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'search',
          description: 'Search the web using Google (no API key required)',
          inputSchema: {
            type: 'object',
            properties: {
              query: {
                type: 'string',
                description: 'Search query',
              },
              limit: {
                type: 'number',
                description: 'Maximum number of results to return (default: 5)',
                minimum: 1,
                maximum: 10,
              },
            },
            required: ['query'],
          },
        },
      ],
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      if (request.params.name !== 'search') {
        throw new McpError(
          ErrorCode.MethodNotFound,
          `Unknown tool: ${request.params.name}`
        );
      }

      if (!isValidSearchArgs(request.params.arguments)) {
        throw new McpError(
          ErrorCode.InvalidParams,
          'Invalid search arguments'
        );
      }

      const query = request.params.arguments.query;
      const limit = Math.min(request.params.arguments.limit || 5, 10);

      try {
        const results = await this.performSearch(query, limit);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(results, null, 2),
            },
          ],
        };
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        return {
          content: [
            {
              type: 'text',
              text: `Search error: ${message}`,
            },
          ],
          isError: true,
        };
      }
    });
  }

  private async performSearch(query: string, limit: number): Promise<SearchResult[]> {
  console.error(`Searching for: "${query}" with limit: ${limit}`);
  
  // 複数のユーザーエージェントをローテーション
  const userAgents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
  ];
  
  // ランダムに選択されたユーザーエージェント
  const userAgent = userAgents[Math.floor(Math.random() * userAgents.length)];
  
  try {
    const searchUrl = new URL('https://www.google.com/search');
    searchUrl.searchParams.set('q', query);
    searchUrl.searchParams.set('num', String(limit));
    searchUrl.searchParams.set('hl', 'en');

    const response = await fetch(searchUrl.toString(), {
      headers: {
        'User-Agent': userAgent,
        Accept: 'text/html,application/xhtml+xml,application/xml',
        'Accept-Language': 'en-US,en;q=0.9',
        Referer: 'https://www.google.com/',
      },
    });

    console.error(`Search response status: ${response.status}`);

    if (!response.ok) {
      console.error(`Response status: ${response.status}`);
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const html = await response.text();
    const $ = cheerio.load(html);
    const results: SearchResult[] = [];
    
    // 複数のセレクタパターンを試す (Googleは頻繁に構造を変更する)
    const selectors = [
      { container: 'div.g', title: 'h3', link: 'a', snippet: '.VwiC3b' },
      { container: 'div.tF2Cxc', title: 'h3', link: 'a', snippet: '.VwiC3b' },
      { container: 'div[data-sokoban-container]', title: 'h3', link: 'a', snippet: '.VwiC3b' },
      { container: 'div.yuRUbf', title: 'h3', link: 'a', snippet: '.IsZvec' },
      { container: 'div.g', title: 'h3.LC20lb', link: 'a', snippet: 'div.VwiC3b' }
    ];
    
    // 各セレクタパターンを試す
    for (const selector of selectors) {
      console.error(`Trying selector pattern: ${JSON.stringify(selector)}`);
      
      let found = false;
      $(selector.container).each((i, element) => {
        if (i >= limit) return false;
        
        const titleElement = $(element).find(selector.title);
        const linkElement = $(element).find(selector.link);
        const snippetElement = $(element).find(selector.snippet);
        
        if (titleElement.length && linkElement.length) {
          found = true;
          const url = linkElement.attr('href');
          if (url && url.startsWith('http')) {
            results.push({
              title: titleElement.text().trim(),
              url: url,
              description: snippetElement.text()?.trim() || '',
            });
          }
        }
      });
      
      // 十分な結果が見つかったら他のセレクタは試さない
      if (found) {
        console.error(`Found ${results.length} results using pattern: ${JSON.stringify(selector)}`);
        break;
      }
    }
    
    // 結果が少なすぎる場合はフォールバックとして汎用的なセレクタを使用
    if (results.length < Math.min(limit, 3)) {
      console.error('Insufficient results, trying generic selector');
      
      // リンクと見出しを持つ要素を探す
      $('a[href^="http"]').each((i, element) => {
        if (results.length >= limit) return false;
        
        const $el = $(element);
        const h3 = $el.find('h3').first();
        
        if (h3.length > 0) {
          const url = $el.attr('href');
          if (url && !results.some(r => r.url === url)) { // 重複チェック
            let description = '';
            // リンク要素の親の次の要素からdescriptionを取得しようとする
            const parent = $el.parent();
            const nextEl = parent.next();
            if (nextEl.length) {
              description = nextEl.text().trim();
            }
            
            results.push({
              title: h3.text().trim(),
              url: url,
              description: description,
            });
          }
        }
      });
    }
    
    console.error(`Returning ${results.length} search results`);
    
    if (results.length === 0) {
      console.error('No results found, HTML structure might have changed');
      console.error('HTML Preview: ' + html.substring(0, 1000));
    }
    
    return results;
  } catch (error) {
    console.error('Search failed:', error);
    throw error;
  }
}

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Web Search MCP server running on stdio');
  }
}

const server = new WebSearchServer();
server.run().catch(console.error);
