# services/arxiv_mcp_service.py
import os
import platform
import traceback
import asyncio
import sys
from typing import Dict, Any, Optional
from strands import Agent
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters
from config import Config

class ArxivMCPService:
    def __init__(self):
        self.client: Optional[MCPClient] = None
        self.agent: Optional[Agent] = None
        self.is_connected = False
        self.connection_error = None
        self.storage_path = self._get_storage_path()
        self.max_papers = Config.ARXIV_MAX_PAPERS
        self._lock = asyncio.Lock()
        
    def _get_storage_path(self) -> str:
        storage_path = os.getenv("ARXIV_STORAGE_PATH")
        if not storage_path:
            print("⛔ARXIV_STORAGE_PATH が設定されていません。")
            if platform.system() == "Windows":
                from pathlib import Path
                storage_path = os.path.join(Path.home(), "Desktop", "arxiv-papers")
            else:
                storage_path = os.path.join(os.path.expanduser("~"), "Desktop", "arxiv-papers")
        
        if not os.path.exists(storage_path):
            try:
                os.makedirs(storage_path, exist_ok=True)
                print(f"📁 ストレージフォルダを作成しました: {storage_path}")
            except Exception as e:
                print(f"⛔フォルダ作成に失敗しました: {storage_path} - {e}")
        
        return storage_path
    
    def _ensure_event_loop_policy(self):
        """Windows環境でのイベントループポリシー設定"""
        if platform.system() == "Windows":
            try:
                # 現在のポリシーを確認
                policy = asyncio.get_event_loop_policy()
                if not isinstance(policy, asyncio.WindowsProactorEventLoopPolicy):
                    print("Windows ProactorEventLoopPolicy を設定中...")
                    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            except Exception as e:
                print(f"イベントループポリシー設定エラー: {e}")
    
    async def initialize(self) -> bool:
        """arXiv MCP サーバーの非同期初期化"""
        print(f"arXiv MCP サーバー初期化開始 - ストレージパス: {self.storage_path}")
        
        # Windows環境でのイベントループポリシー確認
        self._ensure_event_loop_policy()
        
        if not os.path.exists(self.storage_path):
            try:
                os.makedirs(self.storage_path, exist_ok=True)
                print(f"📁 ストレージフォルダを作成しました: {self.storage_path}")
            except Exception as e:
                self.connection_error = f"ストレージパス作成失敗: {self.storage_path} - {e}"
                print(f"⛔ {self.connection_error}")
                return False
        
        try:
            print(f"Initializing arxiv MCP Agent with storage path: {self.storage_path}...🚀")
            
            # Windows環境での特別な処理
            if platform.system() == "Windows":
                # uvコマンドの存在確認
                import subprocess
                try:
                    result = subprocess.run(["uv", "--version"], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode != 0:
                        raise FileNotFoundError("uv command not found")
                    print(f"UV version: {result.stdout.strip()}")
                except (FileNotFoundError, subprocess.TimeoutExpired) as e:
                    self.connection_error = f"uvコマンドが見つかりません: {e}"
                    print(f"⛔ {self.connection_error}")
                    return False
                
                # arxiv-mcp-serverの存在確認
                try:
                    result = subprocess.run(["uv", "tool", "list"], 
                                          capture_output=True, text=True, timeout=10)
                    if "arxiv-mcp-server" not in result.stdout:
                        self.connection_error = "arxiv-mcp-server がインストールされていません"
                        print(f"⛔ {self.connection_error}")
                        print("以下のコマンドでインストールしてください:")
                        print("uv tool install arxiv-mcp-server")
                        return False
                    print("arxiv-mcp-server の存在を確認しました")
                except subprocess.TimeoutExpired:
                    print("⚠️ uv tool list がタイムアウトしました")
            
            # MCPクライアント作成（同期処理）
            def create_client():
                return MCPClient(
                    lambda: stdio_client(
                        StdioServerParameters(
                            command="uv",
                            args=[
                                "tool",
                                "run",
                                "arxiv-mcp-server",
                                "--storage-path", self.storage_path
                            ]
                        )
                    )
                )
            
            self.client = create_client()
            
            # 新しい方法：async contextを使用
            try:
                await self._start_client_async()
                self.is_connected = True
                self.connection_error = None
                print(f"arxiv initialized successfully👍")
                return True
                
            except Exception as e:
                print(f"非同期クライアント起動に失敗: {e}")
                # フォールバック：同期処理を試行
                return await self._try_sync_fallback()
                
        except Exception as e:
            self.connection_error = str(e)
            print(f"⛔ Failed to initialize arxiv MCP Agent: {str(e)}")
            traceback.print_exc()
            self.is_connected = False
            return False
    
    async def _start_client_async(self):
        """非同期でクライアントを起動"""
        # クライアントをコンテキストマネージャーとして使用
        self.client.__enter__()
        
        # ツール一覧取得
        tools = self.client.list_tools_sync()
        self.agent = Agent(tools=tools)
        print(f"利用可能なツール: {[tool.name for tool in tools]}")
    
    async def _try_sync_fallback(self) -> bool:
        """同期処理のフォールバック"""
        try:
            print("同期処理フォールバックを試行中...")
            
            # 同期処理でクライアント起動
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.client.__enter__)
            
            # ツール取得
            tools = await loop.run_in_executor(None, self.client.list_tools_sync)
            self.agent = Agent(tools=tools)
            
            self.is_connected = True
            self.connection_error = None
            print(f"arxiv initialized successfully (fallback)👍")
            print(f"利用可能なツール: {[tool.name for tool in tools]}")
            return True
            
        except Exception as e:
            self.connection_error = f"フォールバック処理も失敗: {str(e)}"
            print(f"⛔ {self.connection_error}")
            return False

    async def search_and_analyze_papers(self, query: str, refined_query: Optional[str] = None) -> Dict[str, Any]:
        """論文検索・ダウンロード・分析の非同期処理"""
        async with self._lock:
            if not self.is_connected or not self.agent:
                return {
                    "error": f"arXiv MCP サーバーに接続されていません: {self.connection_error}",
                    "status": "failed"
                }
            
            try:
                search_query = refined_query if refined_query else query
                
                arxiv_prompt = f"""
以下の質問について、arXivから関連する論文を検索し、最大{self.max_papers}論文まで取得・分析してください。

質問: {query}
検索クエリ: {search_query}

実行手順:
1. search_papers ツールを使用して関連論文を検索してください
2. 見つかった論文の中から最も関連性の高い{self.max_papers}論文を選択してください  
3. 各論文について download_paper でダウンロードしてください
4. 各論文について read_paper で内容を読み込んでください
5. 質問に対する答えとして、論文の内容を統合して分析してください

注意点:
- 論文が見つからない場合は、その旨を報告してください
- ダウンロードや読み込みに失敗した論文があっても、取得できた論文で分析を続けてください
- 各論文のタイトル、著者、要旨、主要な発見事項を含めてください
"""
                
                # エージェント実行
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(None, self.agent, arxiv_prompt)
                
                response_text = str(response) if response else "応答を取得できませんでした"
                
                return {
                    "query": query,
                    "search_query": search_query,
                    "response": response_text,
                    "storage_path": self.storage_path,
                    "max_papers": self.max_papers,
                    "status": "success"
                }
                
            except Exception as e:
                error_msg = f"arXiv論文分析中にエラーが発生しました: {str(e)}"
                print(error_msg)
                traceback.print_exc()
                return {
                    "error": error_msg,
                    "status": "failed"
                }
    
    async def cleanup(self):
        """非同期リソースクリーンアップ"""
        if self.client:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.client.__exit__, None, None, None)
                print("MCP Agent for arxiv shutdown successfully👍")
            except Exception as e:
                print(f"Error during arxiv shutdown: {e}")
        
        self.client = None
        self.agent = None
        self.is_connected = False

# シングルトンインスタンス
arxiv_mcp_service = ArxivMCPService()