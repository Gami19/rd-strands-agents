from strands import Agent
from strands.tools.mcp import MCPClient
from typing import Dict, Any

class ResearchAgent:
    """リサーチエージェントの実装"""
    
    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client
        self.tools = mcp_client.list_tools_sync()
        
        self.agent = Agent(
            tools=self.tools,
            system_prompt="""あなたはリサーチエージェントです。
            与えられたクエリについて、以下のMCPツールを使用して情報を収集してください：
            
            1. Brave Search: 最新のウェブ情報の検索
            2. ArXiv: 学術論文と研究資料の検索
            3. Web Research: 詳細なウェブ調査と分析
            
            収集した情報は以下の形式で整理してください：
            - 主要な発見事項
            - 信頼できる情報源
            - 最新のトレンド
            - 関連する統計データ
            
            情報は分析エージェントが使用できるよう、構造化して提供してください。"""
        )
    
    def research(self, query: str) -> Dict[str, Any]:
        """リサーチクエリの実行"""
        try:
            response = self.agent(query)
            return {
                "status": "success",
                "query": query,
                "results": str(response),
                "sources": self._extract_sources(str(response))
            }
        except Exception as e:
            return {
                "status": "error",
                "query": query,
                "error": str(e)
            }
    
    def _extract_sources(self, response: str) -> list:
        """レスポンスから情報源を抽出"""
        # 簡易的な情報源抽出（実際の実装ではより高度な処理が必要）
        sources = []
        lines = response.split('\n')
        for line in lines:
            if 'http' in line or 'arxiv.org' in line or 'doi.org' in line:
                sources.append(line.strip())
        return sources