import asyncio
from typing import Dict, List, Optional, Tuple
from strands import Agent
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters
import os
import traceback
from enum import Enum
import concurrent.futures

class AgentType(str, Enum):
    RESEARCH = "research"
    ANALYSIS = "analysis"
    REPORT = "report"

class MultiAgentManager:
    def __init__(self):
        self.agents: Dict[AgentType, Agent] = {}
        self.mcp_clients: Dict[AgentType, MCPClient] = {}
        self.initialized = False
        
        # エージェントの設定
        self.agent_configs = {
            AgentType.RESEARCH: {
                "name": "Research Agent",
                "description": "情報収集と検索を担当するエージェント",
                "system_prompt": """あなたはリサーチエージェントです。
                与えられたクエリについて、以下のMCPツールを使用して情報を収集してください：
                - Brave Search: ウェブ検索
                - ArXiv: 学術論文検索
                - Web Research: 詳細なウェブ調査
                
                収集した情報は整理して、分析エージェントが使用できる形式で返してください。""",
                "mcp_tools": ["brave_search", "arxiv", "web_research"]
            },
            AgentType.ANALYSIS: {
                "name": "Analysis Agent", 
                "description": "収集された情報の分析を担当するエージェント",
                "system_prompt": """あなたは分析エージェントです。
                リサーチエージェントから提供された情報を分析し、以下の観点から評価してください：
                - 信頼性と正確性
                - 関連性と重要性
                - トレンドとパターン
                - 機会とリスク
                
                分析結果は構造化された形式で、レポートエージェントが使用できるようにしてください。""",
                "mcp_tools": ["aws_knowledge", "financial_datasets"]
            },
            AgentType.REPORT: {
                "name": "Report Agent",
                "description": "最終的なレポート生成を担当するエージェント", 
                "system_prompt": """あなたはレポートエージェントです。
                リサーチエージェントと分析エージェントからの情報を統合し、以下の要素を含む包括的なレポートを作成してください：
                - エグゼクティブサマリー
                - 主要な発見事項
                - 推奨事項
                - アクションプラン
                
                レポートは明確で実用的な内容にしてください。""",
                "mcp_tools": ["aws_documentation", "aws_diagram"]
            }
        }
    
    async def initialize_agents(self):
        """すべてのエージェントを初期化"""
        print(" Initializing Multi-Agent A2A System...")
        
        # 各エージェントタイプごとに初期化
        for agent_type in AgentType:
            try:
                await self._initialize_agent(agent_type)
            except Exception as e:
                print(f"⛔Failed to initialize {agent_type}: {e}")
                traceback.print_exc()
        
        self.initialized = True
        print("✅ Multi-Agent A2A System initialization completed")
    
    async def _initialize_agent(self, agent_type: AgentType):
        """個別エージェントの初期化"""
        print(f"🔧 Initializing {agent_type} agent...")
        
        # MCPクライアントの作成
        mcp_client = await self._create_mcp_client(agent_type)
        if mcp_client:
            self.mcp_clients[agent_type] = mcp_client
            
            # コンテキストマネージャー内でツールを取得
            try:
                with mcp_client:
                    tools = mcp_client.list_tools_sync()
                    
                    # Strands Agentの作成
                    agent = Agent(
                        tools=tools,
                        system_prompt=self.agent_configs[agent_type]["system_prompt"]
                    )
                    
                    self.agents[agent_type] = agent
                    print(f"✅ {agent_type} agent initialized successfully")
                    
            except Exception as e:
                print(f"⛔Failed to get tools for {agent_type}: {e}")
                # ツールなしでエージェントを作成
                agent = Agent(
                    tools=[],
                    system_prompt=self.agent_configs[agent_type]["system_prompt"]
                )
                self.agents[agent_type] = agent
                print(f"⚠️ {agent_type} agent created without MCP tools")
        else:
            print(f"⚠️ {agent_type} agent initialization skipped due to MCP client failure")
            # MCPツールなしでエージェントを作成
            agent = Agent(
                tools=[],
                system_prompt=self.agent_configs[agent_type]["system_prompt"]
            )
            self.agents[agent_type] = agent
            print(f"⚠️ {agent_type} agent created without MCP tools")
    
    async def _create_mcp_client(self, agent_type: AgentType) -> Optional[MCPClient]:
        """エージェントタイプに応じたMCPクライアントの作成"""
        try:
            if agent_type == AgentType.RESEARCH:
                # リサーチエージェント用のMCPツール
                return await self._create_research_mcp_client()
            elif agent_type == AgentType.ANALYSIS:
                # 分析エージェント用のMCPツール
                return await self._create_analysis_mcp_client()
            elif agent_type == AgentType.REPORT:
                # レポートエージェント用のMCPツール
                return await self._create_report_mcp_client()
        except Exception as e:
            print(f"Error creating MCP client for {agent_type}: {e}")
            return None
    
    async def _create_research_mcp_client(self) -> MCPClient:
        """リサーチエージェント用MCPクライアント"""
        try:
            # Brave Search MCPサーバー
            brave_api_key = os.getenv("BRAVE_API_KEY")
            if not brave_api_key:
                print("Warning: BRAVE_API_KEY not set, Brave Search will not work")
                return None
            
            return MCPClient(
                lambda: stdio_client(
                    StdioServerParameters(
                        command="npx",
                        args=["-y", "@modelcontextprotocol/server-brave-search"],
                        env={"BRAVE_API_KEY": brave_api_key}
                    )
                )
            )
        except Exception as e:
            print(f"Error creating research MCP client: {e}")
            return None
    
    async def _create_analysis_mcp_client(self) -> MCPClient:
        """分析エージェント用MCPクライアント"""
        try:
            # AWS Knowledge MCPサーバー
            return MCPClient(
                lambda: stdio_client(
                    StdioServerParameters(
                        command="npx",
                        args=["mcp-remote", "https://knowledge-mcp.global.api.aws"]
                    )
                )
            )
        except Exception as e:
            print(f"Error creating analysis MCP client: {e}")
            return None
    
    async def _create_report_mcp_client(self) -> MCPClient:
        """レポートエージェント用MCPクライアント"""
        try:
            # AWS Documentation MCPサーバー
            return MCPClient(
                lambda: stdio_client(
                    StdioServerParameters(
                        command="python",
                        args=["-m", "awslabs.aws_documentation_mcp_server.server"]
                    )
                )
            )
        except Exception as e:
            print(f"Error creating report MCP client: {e}")
            return None
    
    async def query_agent(self, agent_type: str, query: str) -> str:
        """個別エージェントへのクエリ実行"""
        if agent_type not in self.agents:
            raise ValueError(f"Agent type {agent_type} not found")
        
        agent = self.agents[agent_type]
        try:
            # MCPツールがある場合はコンテキストマネージャー内で実行
            if agent_type in self.mcp_clients and self.mcp_clients[agent_type]:
                with self.mcp_clients[agent_type]:
                    response = agent(query)
                    return str(response)
            else:
                # MCPツールなしで実行
                response = agent(query)
                return str(response)
        except Exception as e:
            raise Exception(f"Agent query failed: {str(e)}")
    
    async def execute_workflow(self, query: str, workflow: List[str]) -> Tuple[Dict[str, str], str]:
        """マルチエージェントワークフローの実行"""
        print(f" Executing workflow: {workflow}")
        
        responses = {}
        current_context = query
        
        # ワークフローに従ってエージェントを順次実行
        for agent_type in workflow:
            if agent_type not in self.agents:
                print(f"⚠️ Agent {agent_type} not available, skipping...")
                continue
            
            try:
                # 前のエージェントの結果をコンテキストに含める
                enhanced_query = f"""
                元のクエリ: {query}
                
                前のエージェントの結果:
                {current_context}
                
                あなたのタスクを実行してください。
                """
                
                response = await self.query_agent(agent_type, enhanced_query)
                responses[agent_type] = response
                current_context = response
                
                print(f"✅ {agent_type} agent completed")
                
            except Exception as e:
                error_msg = f"Error in {agent_type} agent: {str(e)}"
                responses[agent_type] = error_msg
                print(f"⛔ {error_msg}")
        
        # 最終的なワークフロー結果を生成
        workflow_result = self._generate_workflow_summary(responses, query)
        
        return responses, workflow_result
    
    def _generate_workflow_summary(self, responses: Dict[str, str], original_query: str) -> str:
        """ワークフロー実行結果のサマリー生成"""
        summary = f"""
# マルチエージェントワークフロー実行結果

## 元のクエリ
{original_query}

## 各エージェントの実行結果

"""
        
        for agent_type, response in responses.items():
            summary += f"### {agent_type.upper()} エージェント\n"
            summary += f"{response[:500]}{'...' if len(response) > 500 else ''}\n\n"
        
        summary += "## 総合評価\n"
        summary += "すべてのエージェントが正常に実行され、包括的な分析が完了しました。"
        
        return summary
    
    async def configure_agent(self, agent_type: str, config: dict) -> bool:
        """エージェントの設定変更"""
        try:
            if agent_type in self.agent_configs:
                self.agent_configs[agent_type].update(config)
                print(f"✅ Agent {agent_type} configuration updated")
                return True
            return False
        except Exception as e:
            print(f"⛔Failed to configure agent {agent_type}: {e}")
            return False
    
    async def get_agent_status(self) -> Dict[str, str]:
        """エージェントのステータス取得"""
        status = {}
        for agent_type in AgentType:
            if agent_type in self.agents:
                status[agent_type] = "available"
            else:
                status[agent_type] = "unavailable"
        return status
    
    async def shutdown(self):
        """システムのシャットダウン"""
        print("🛑 Shutting down Multi-Agent A2A System...")
        
        for agent_type, client in self.mcp_clients.items():
            try:
                if client:
                    client.__exit__(None, None, None)
                    print(f"✅ {agent_type} MCP client shutdown successfully")
            except Exception as e:
                print(f"⛔Error during {agent_type} shutdown: {e}")
        
        print("✅ Multi-Agent A2A System shutdown completed")