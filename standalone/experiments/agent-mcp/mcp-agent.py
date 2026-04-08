from contextlib import asynccontextmanager
from strands import Agent
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from typing import Dict, Optional
from enum import Enum
import os
import traceback
from dotenv import load_dotenv
import platform
import sys

# 環境変数のロード
load_dotenv()

# Lifespan contextマネージャを定義（非推奨警告を解決するため）
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 起動時の処理
    try:
        mcp_manager.initialize_servers()
    except Exception as e:
        print(f"⛔Failed during startup: {e}")
        traceback.print_exc()
    
    yield  # FastAPIアプリケーションの実行中
    
    # シャットダウン時の処理
    mcp_manager.shutdown()

app = FastAPI(title="Multi-MCP Agent API", version="1.0.0", lifespan=lifespan)

# MCPサーバータイプ
# WEB_SEARCH（pskill9）とWEB_RESEARCH（mzxrai）は異なるサーバーを指す
class MCPServerType(str, Enum):
    AWS_DOCUMENTATION = "aws_documentation"
    AWS_DIAGRAM = "aws_diagram"
    AWS_KNOWLEDGE = "aws_knowledge"
    BRAVE_SEARCH = "brave_search"
    PLAYWRIGHT = "playwright"
    ARXIV = "arxiv"
    WEB_SEARCH = "web_search"  
    WEB_RESEARCH = "web_research"
    SERENA = "serena"  
    FINANCIAL_DATASETS = "financial_datasets"
    WORLD_BANK = "world_bank"


# リクエストモデル
class QueryRequest(BaseModel):
    query: str

# レスポンスモデル
class QueryResponse(BaseModel):
    response: str
    status: str = "success" 

# playwrightオプションクラス
class PlaywrightOptions(BaseModel):
    # デフォルトはヘッドレスモードを無効
    headless: bool = False
    vision: bool = False

# Playwright専用リクエストモデル 
class PlaywrightQueryRequest(BaseModel):
    query: str
    options: Optional[PlaywrightOptions] = None

# ArXivオプションクラス
class ArXivOptions(BaseModel):
    storage_path: Optional[str] = None

# WebSearchオプションクラス
class WebSearchOptions(BaseModel):
    max_results: Optional[int] = 5

# Serena用オプションクラス
class SerenaOptions(BaseModel):
    context: Optional[str] = "desktop-app"
    mode: Optional[list] = []

# (Serena)プロジェクト有効化用のリクエストモデル
class ProjectActivateRequest(BaseModel):
    project_path: str


# MCP設定を管理するクラス
class MCPManager:
    def __init__(self):
        self.clients: Dict[MCPServerType, MCPClient] = {}
        self.agents: Dict[MCPServerType, Agent] = {}
        self.initialized = False
    
    # 共通の初期化メソッド
    def _initialize_client(self, server_type, extra_info=None):
        """
        クライアント起動と対応するエージェントを初期化する共通メソッド
        """
        try:
            if server_type in self.clients:
                info_text = f" {extra_info}" if extra_info else ""
                print(f"Initializing {server_type} MCP Agent{info_text}...🚀")
                
                def do_initialization():
                    self.clients[server_type].__enter__()
                    self.agents[server_type] = Agent(tools=self.clients[server_type].list_tools_sync())
                    return True
                
                # ThreadPoolExecutorを使用してタイムアウト付き実行
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(do_initialization)
                    try:
                        # 60秒でタイムアウト
                        result = future.result(timeout=60)
                        print(f"{server_type} initialized successfully👍")
                        return True
                        
                    except concurrent.futures.TimeoutError:
                        print(f"⛔ Timeout during {server_type} initialization after 60 seconds")
                        # クリーンアップ
                        try:
                            if server_type in self.clients:
                                self.clients[server_type].__exit__(None, None, None)
                                del self.clients[server_type]
                        except:
                            pass
                        return False
                        
            return False
            
        except Exception as e:
            print(f"⛔ Failed to initialize {server_type} MCP Agent: {str(e)}")
            traceback.print_exc()
            return False
    
    def initialize_servers(self):
        # AWS DocumentationのMCPサーバー
        if platform.system() == "Windows":
            self.clients[MCPServerType.AWS_DOCUMENTATION] = MCPClient(
                lambda: stdio_client(
                    StdioServerParameters(
                        command="python",
                        args=["-m", "awslabs.aws_documentation_mcp_server.server"]
                    )
                )
            )            
        else:
            self.clients[MCPServerType.AWS_DOCUMENTATION] = MCPClient(
                lambda: stdio_client(
                    StdioServerParameters(
                        command="uvx",
                        args=["awslabs.aws-documentation-mcp-server@latest"]
                    )
                )
            )            
            
        # AWS DiagramのMCPサーバー
        self.clients[MCPServerType.AWS_DIAGRAM] = MCPClient(
        lambda: stdio_client(
            StdioServerParameters(
                command="python",
                args=["-m", "awslabs.aws_diagram_mcp_server.server"],
                env={
                    "FASTMCP_LOG_LEVEL": "ERROR",
                    "PATH": os.environ.get("PATH", "")
                },
                autoApprove=[],
                disabled=False
                )
            )
        )

        # AWS KnowledgeのMCPサーバー
        self.clients[MCPServerType.AWS_KNOWLEDGE] = MCPClient(
            lambda: stdio_client(
                StdioServerParameters(
                    command="npx",
                    args=[
                        "mcp-remote",
                        "https://knowledge-mcp.global.api.aws"
                    ]
                )
            )
        )

        # Brave Searchのサーバー - Node.jsを使用
        brave_api_key = os.getenv("BRAVE_API_KEY")
        if not brave_api_key:
            print("Warning: BRAVE_API_KEY is not set. Brave Search MCP will not work.")
        
        self.clients[MCPServerType.BRAVE_SEARCH] = MCPClient(
            lambda: stdio_client(
                StdioServerParameters(
                    command="npx",
                    args=[
                        "-y",
                        "@modelcontextprotocol/server-brave-search"
                    ],
                    env={
                        "BRAVE_API_KEY": brave_api_key,
                        "PATH": os.environ.get("PATH", "")
                    }
                )
            )
        )
        
        # 環境変数として設定されていればそちらを優先
        storage_path = os.getenv("ARXIV_STORAGE_PATH")

        if not storage_path:
            print("ARXIV_STORAGE_PATH が設定されていません。デフォルトのストレージパス（デスクトップ上）を使用します。")
            # デフォルトのストレージパスを設定
            if platform.system() == "Windows":
                from pathlib import Path
                storage_path = os.path.join(Path.home(), "Desktop", "arxiv-papers")
            else:
                storage_path = os.path.join(os.path.expanduser("~"), "Desktop", "arxiv-papers")
        # フォルダが存在しない場合は作成
        if not os.path.exists(storage_path):
            print(f"ダウンロード先のファルダが存在しないため、デスクトップ上に作成します")
            try:
                os.makedirs(storage_path)
                print(f"Created ArXiv storage directory at: {storage_path}")
            except Exception as e:
                print(f"⛔Failed to create directory {storage_path}: {e}")
                # 作成に失敗した場合はデフォルトパスにフォールバック
                if platform.system() == "Windows":
                    storage_path = os.path.join(os.environ["USERPROFILE"], ".arxiv-mcp-server", "papers")
                else:
                    storage_path = os.path.expanduser("~/.arxiv-mcp-server/papers")
                print(f"Falling back to default ArXiv storage path: {storage_path}")
                # フォールバックディレクトリも作成
                if not os.path.exists(storage_path):
                    os.makedirs(storage_path)

        # ArXiv MCPサーバーを追加
        self.clients[MCPServerType.ARXIV] = MCPClient(
            lambda: stdio_client(
                StdioServerParameters(
                    command="uv",
                    args=[
                        "tool",
                        "run",
                        "arxiv-mcp-server",
                        "--storage-path", storage_path
                    ]
                )
            )
        )
        
        # Web Search MCPサーバーを追加（パスを直接指定）
        web_search_path = os.getenv("WEB_SEARCH_MCP_PATH")

        # 環境変数が設定されていれば使用、なければnpxを使用
        if web_search_path and os.path.exists(web_search_path):
            print(f"Using Web Search MCP at path: {web_search_path}")
            self.clients[MCPServerType.WEB_SEARCH] = MCPClient(
                lambda: stdio_client(
                    StdioServerParameters(
                        command="node",
                        args=[web_search_path]
                    )
                )
            )
        
        # Web Research MCPサーバーを追加（Windows対応を強化）
        if platform.system() == "Windows":
            # Windows環境向けの設定
            env_vars = {
                "PATH": os.environ.get("PATH", ""),
                "DEBUG": "*"  # 詳細なログを有効化
            }
            
            print("Initializing Web Research MCP Server for Windows environment...")
            self.clients[MCPServerType.WEB_RESEARCH] = MCPClient(
                lambda: stdio_client(
                    StdioServerParameters(
                        command="npx",
                        args=[
                            "-y", 
                            "@mzxrai/mcp-webresearch@latest"
                        ],
                        env=env_vars
                    )
                )
            )
        else:
            # macOS/Linux向けの設定
            self.clients[MCPServerType.WEB_RESEARCH] = MCPClient(
                lambda: stdio_client(
                    StdioServerParameters(
                        command="npx",
                        args=[
                            "-y", 
                            "@mzxrai/mcp-webresearch@latest"
                        ]
                    )
                )
            )
            
        # serenaフォルダを使用
        serena_path = os.getenv("SERENA_MCP_SERVER_PATH")
        if serena_path and os.path.exists(serena_path):
            print(f"Using local Serena installation at: {serena_path}")
            self.clients[MCPServerType.SERENA] = MCPClient(
                lambda: stdio_client(
                    StdioServerParameters(
                        command="uv",
                        args=["run", "--directory", serena_path, "serena", "start-mcp-server", "--context", "desktop-app"],
                    )
                )
            )
        else:
            print("SERENA_MCP_SERVER_PATH not set or local Serena installation not found, skipping Serena initialization")

        # World Bank MCPサーバーを追加
        world_bank_path = os.getenv("WORLD_BANK_MCP_SERVER_PATH")
        if world_bank_path and os.path.exists(world_bank_path):
            print(f"Using local World Bank MCP Server at: {world_bank_path}")
            self.clients[MCPServerType.WORLD_BANK] = MCPClient(
                lambda: stdio_client(
                    StdioServerParameters(
                        command="uv",
                        args=[ 
                            "--directory", 
                            world_bank_path,
                            "run", 
                            "world_bank_mcp_server"
                        ]
                    )
                )
            )
        else:
            print("WORLD_BANK_MCP_SERVER_PATH not set or path not found, skipping World Bank initialization")
        
        # Financial Datasets MCPサーバーを追加
        financial_datasets_path = os.getenv("FINANCIAL_DATASETS_MCP_SERVER_PATH")
        if financial_datasets_path and os.path.exists(financial_datasets_path):
            print(f"Using local Financial Datasets MCP Server at: {financial_datasets_path}")
            self.clients[MCPServerType.FINANCIAL_DATASETS] = MCPClient(
                lambda: stdio_client(
                    StdioServerParameters(
                        command="uv",
                        args=[
                            "--directory", 
                            financial_datasets_path,
                            "run", 
                            "server.py"
                        ]
                    )
                )
            )
        else:
            print("FINANCIAL_DATASETS_MCP_SERVER_PATH not set or path not found, skipping Financial Datasets initialization")

        # サーバータイプリストを動的に作成
        # WORLD_BANK, FINANCIAL_DATASETS, SERENA は、除外
        server_types = [
            MCPServerType.AWS_DOCUMENTATION, 
            MCPServerType.BRAVE_SEARCH, 
            MCPServerType.ARXIV,
            MCPServerType.WEB_SEARCH, 
            MCPServerType.WEB_RESEARCH, 
            MCPServerType.AWS_DIAGRAM,
            MCPServerType.AWS_KNOWLEDGE
        ]
        
        # World Bankクライアントが作成されている場合のみリストに追加
        if MCPServerType.WORLD_BANK in self.clients:
            server_types.append(MCPServerType.WORLD_BANK)
        
        # Financial Datasetsクライアントが作成されている場合のみリストに追加
        if MCPServerType.FINANCIAL_DATASETS in self.clients:
            server_types.append(MCPServerType.FINANCIAL_DATASETS)

        # Serenaが初期化されている場合のみリストに追加
        if MCPServerType.SERENA in self.clients:
            server_types.append(MCPServerType.SERENA)
        
        for server_type in server_types:
            extra_info = None
            if server_type == MCPServerType.ARXIV:
                extra_info = f"with storage path: {storage_path}"
            elif server_type == MCPServerType.SERENA:
                extra_info = f"from {serena_path}"
            self._initialize_client(server_type, extra_info)
        
        # PlayWrightは初期設定でデフォルト(ヘッドレスなし)で初期化
        self.create_playwright_client(headless=False)
        
        self.initialized = True
    
    # Playwrightクライアントを作成するメソッド
    def create_playwright_client(self, headless=False, vision=False):
        # 既存のクライアントをシャットダウン
        if MCPServerType.PLAYWRIGHT in self.clients:
            try:
                self.clients[MCPServerType.PLAYWRIGHT].__exit__(None, None, None)
            except Exception as e:
                print(f"Error shutting down existing Playwright client: {e}")
        
        # 引数リストを作成
        args = ["-y", "@playwright/mcp@latest"]
        if headless:
            args.append("--headless")
        if vision:
            args.append("--vision")
        
        # 新しいクライアントを作成
        self.clients[MCPServerType.PLAYWRIGHT] = MCPClient(
            lambda: stdio_client(
                StdioServerParameters(
                    command="npx",
                    args=args
                )
            )
        )

        # 共通の初期化処理を使用
        return self._initialize_client(
            MCPServerType.PLAYWRIGHT, 
            f"(headless={headless}, vision={vision})"
        )

    # Serenaクライアントを設定するメソッド
    def configure_serena_client(self, context="desktop-app", modes=None, project_path=None):
        # 既存のクライアントをシャットダウン
        if MCPServerType.SERENA in self.clients:
            try:
                self.clients[MCPServerType.SERENA].__exit__(None, None, None)
            except Exception as e:
                print(f"Error shutting down existing Serena client: {e}")
        
        # 親ディレクトリにあるSerenaを使用
        serena_path = os.getenv("SERENA_MCP_SERVER_PATH")
        
        if not serena_path:
            print("SERENA_MCP_SERVER_PATH not set, cannot configure Serena client")
            return
        
        # 引数リストを作成
        args = []
        if os.path.exists(serena_path):
            command = "uv"
            args = ["run", "--directory", serena_path, "serena", "start-mcp-server"]
        else:
            print(f"Serena path does not exist: {serena_path}")
            return
        
        # コンテキストを追加
        args.extend(["--context", context])
        
        # モードを追加 (もし指定されていれば)
        if modes:
            for mode in modes:
                args.extend(["--mode", mode])
        
        # プロジェクトパスを追加 (リクエストで指定)
        if project_path:
            args.extend(["--project", project_path])
        
        # 新しいクライアントを作成
        self.clients[MCPServerType.SERENA] = MCPClient(
            lambda: stdio_client(
                StdioServerParameters(
                    command=command,
                    args=args
                )
            )
        )

        # 共通の初期化処理を使用
        extra_info = f"with context={context}"
        if modes:
            extra_info += f", modes={modes}"
        if project_path:
            extra_info += f", project={project_path}"
            
        return self._initialize_client(MCPServerType.SERENA, extra_info)

    # ArXivクライアントを再設定するメソッド
    def configure_arxiv_client(self, storage_path=None):
        # 既存のクライアントをシャットダウン
        if MCPServerType.ARXIV in self.clients:
            try:
                self.clients[MCPServerType.ARXIV].__exit__(None, None, None)
            except Exception as e:
                print(f"Error shutting down existing ArXiv client: {e}")
        
        # ストレージパスが指定されていない場合はデフォルト値を使用
        if not storage_path:
            if platform.system() == "Windows":
                from pathlib import Path
                storage_path = os.path.join(Path.home(), "Desktop", "arxiv-papers")
            else:
                storage_path = os.path.join(os.path.expanduser("~"), "Desktop", "arxiv-papers")
            
            # フォルダが存在しない場合は作成
            if not os.path.exists(storage_path):
                try:
                    os.makedirs(storage_path)
                except Exception:
                    # 作成に失敗した場合はデフォルトパスにフォールバック
                    if platform.system() == "Windows":
                        storage_path = os.path.join(os.environ["USERPROFILE"], ".arxiv-mcp-server", "papers")
                    else:
                        storage_path = os.path.expanduser("~/.arxiv-mcp-server/papers")
                    
                    # フォールバックディレクトリも必要に応じて作成
                    if not os.path.exists(storage_path):
                        os.makedirs(storage_path)
        
        # 新しいクライアントを作成
        self.clients[MCPServerType.ARXIV] = MCPClient(
            lambda: stdio_client(
                StdioServerParameters(
                    command="uv",
                    args=[
                        "tool",
                        "run",
                        "arxiv-mcp-server",
                        "--storage-path", storage_path
                    ]
                )
            )
        )

        # 共通の初期化処理を使用
        return self._initialize_client(MCPServerType.ARXIV, f"with storage path: {storage_path}")

    # Web Research設定を変更するメソッド
    def configure_web_research_client(self, debug_mode=False):
        # 既存のクライアントをシャットダウン
        if MCPServerType.WEB_RESEARCH in self.clients:
            try:
                self.clients[MCPServerType.WEB_RESEARCH].__exit__(None, None, None)
            except Exception as e:
                print(f"Error shutting down existing Web Research client: {e}")
        
        # 環境変数の設定
        env_vars = {
            "PATH": os.environ.get("PATH", ""),
            "DEBUG": "*",  # すべてのデバッグログを有効化
            "NODE_DEBUG": "http,net,request"  # Nodeのネットワーク関連ログを有効化
        }
        
        # デバッグモードが有効な場合
        if debug_mode:
            env_vars.update({
                "DEBUG": "*",
                "NODE_DEBUG": "module"
            })
            
        # Windows環境の場合は追加設定
        if platform.system() == "Windows":
            env_vars["NODE_TLS_REJECT_UNAUTHORIZED"] = "0"
            
        # 新しいクライアントを作成
        self.clients[MCPServerType.WEB_RESEARCH] = MCPClient(
            lambda: stdio_client(
                StdioServerParameters(
                    command="npx",
                    args=[
                        "-y",
                        "@mzxrai/mcp-webresearch@latest"
                    ],
                    env=env_vars
                )
            )
        )

        # 共通の初期化処理を使用
        success = self._initialize_client(MCPServerType.WEB_RESEARCH, 
                                        f"with debug_mode={debug_mode}")
        
        # 初期化後にツール情報を出力
        if success:
            tools = self.clients[MCPServerType.WEB_RESEARCH].list_tools_sync()
            print(f"Web Research MCP Server initialized with tools: {[t.name for t in tools]}")
        
        return success

    # Web Search設定を変更するメソッド
    def configure_web_search_client(self, max_results=5):
        # 既存のクライアントをシャットダウン
        if MCPServerType.WEB_SEARCH in self.clients:
            try:
                self.clients[MCPServerType.WEB_SEARCH].__exit__(None, None, None)
            except Exception as e:
                print(f"Error shutting down existing Web Search client: {e}")
        
        # パスが環境変数で指定されているか確認
        web_search_path = os.getenv("WEB_SEARCH_MCP_PATH")
        
        if web_search_path and os.path.exists(web_search_path):
            # 環境変数から設定されたパスを使用
            self.clients[MCPServerType.WEB_SEARCH] = MCPClient(
                lambda: stdio_client(
                    StdioServerParameters(
                        command="node",
                        args=[web_search_path]
                    )
                )
            )
        else:
            # npxを使用
            self.clients[MCPServerType.WEB_SEARCH] = MCPClient(
                lambda: stdio_client(
                    StdioServerParameters(
                        command="npx",
                        args=[
                            "-y",
                            "@mzxrai/mcp-webresearch@0.1.0"
                        ]
                    )
                )
            )

        # 共通の初期化処理を使用
        return self._initialize_client(MCPServerType.WEB_SEARCH, f"with max_results: {max_results}")

    def shutdown(self):
        for server_type, client in self.clients.items():
            try:
                client.__exit__(None, None, None)
                print(f"MCP Agent for {server_type} shutdown successfully👍")
            except Exception as e:
                print(f"Error during {server_type} shutdown: {e}")
    
    def get_agent(self, server_type: MCPServerType) -> Optional[Agent]:
        return self.agents.get(server_type)

# MCPマネージャー
mcp_manager = MCPManager()

@app.get("/")
async def root():
    return {"message": "Multi-MCP Agent API is running"}

@app.get("/health")
async def health_check():
    available_servers = [name for name, agent in mcp_manager.agents.items() if agent is not None]
    
    # 詳細なステータス情報を追加
    server_status = {}
    for server_type in MCPServerType:
        if server_type in mcp_manager.agents:
            server_status[server_type] = "available" if mcp_manager.agents[server_type] else "unavailable"
        else:
            server_status[server_type] = "not initialized"
    
    return {
        "status": "healthy", 
        "initialized": mcp_manager.initialized,
        "available_servers": available_servers,
        "server_status": server_status
    }

# AWS Documentationクエリエンドポイント
@app.post("/aws_documentation/query", response_model=QueryResponse)
async def aws_query(request: QueryRequest):
    agent = mcp_manager.get_agent(MCPServerType.AWS_DOCUMENTATION)
    if agent is None:
        raise HTTPException(
            status_code=404, 
            detail="AWS Documentation MCP Agent not available. Please check server logs for initialization errors."
        )
    
    try:
        response = agent(request.query)
        return QueryResponse(
            response=str(response)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"⛔Query failed: {str(e)}")

# AWS Diagramクエリエンドポイント
@app.post("/aws-diagram/query", response_model=QueryResponse)
async def aws_diagram_query(request: QueryRequest):
    agent = mcp_manager.get_agent(MCPServerType.AWS_DIAGRAM)
    if agent is None:
        raise HTTPException(
            status_code=404, 
            detail="AWS Diagram MCP Agent not available. Please check server logs for initialization errors."
        )
    
    try:
        response = agent(request.query)
        return QueryResponse(
            response=str(response)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"⛔Query failed: {str(e)}")

# AWS Knowledgeクエリエンドポイント
@app.post("/aws-knowledge/query", response_model=QueryResponse)
async def aws_knowledge_query(request: QueryRequest):
    agent = mcp_manager.get_agent(MCPServerType.AWS_KNOWLEDGE)
    if agent is None:
        raise HTTPException(
            status_code=404, 
            detail="AWS Knowledge MCP Agent not available. Please check server logs for initialization errors."
        )
    
    try:
        response = agent(request.query)
        return QueryResponse(
            response=str(response)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"⛔Query failed: {str(e)}")

# Brave Searchクエリエンドポイント
@app.post("/brave/query", response_model=QueryResponse)
async def brave_search_query(request: QueryRequest):
    agent = mcp_manager.get_agent(MCPServerType.BRAVE_SEARCH)
    if agent is None:
        raise HTTPException(
            status_code=404, 
            detail="Brave Search MCP Agent not available. Please check server logs for initialization errors."
        )
    
    try:
        response = agent(request.query)
        return QueryResponse(
            response=str(response)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"⛔Query failed: {str(e)}")
    
@app.post("/playwright/query", response_model=QueryResponse)
async def playwright_query(request: PlaywrightQueryRequest):
    print(f"Received Playwright query: {request}")
    # オプションが指定された場合は新しいクライアントを作成
    if request.options:
        success = mcp_manager.create_playwright_client(
            headless=request.options.headless,
            vision=request.options.vision
        )
        if not success:
            raise HTTPException(
                status_code=500, 
                detail="⛔Failed to initialize Playwright with the specified options"
            )

    agent = mcp_manager.get_agent(MCPServerType.PLAYWRIGHT)
    if agent is None:
        raise HTTPException(
            status_code=404, 
            detail="Playwright MCP Agent not available. Please check server logs for initialization errors."
        )
    
    try:
        response = agent(request.query)
        return QueryResponse(
            response=str(response)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"⛔Query failed: {str(e)}")

# ArXivクエリエンドポイント
@app.post("/arxiv/query", response_model=QueryResponse)
async def arxiv_query(request: QueryRequest):
    agent = mcp_manager.get_agent(MCPServerType.ARXIV)
    if agent is None:
        raise HTTPException(
            status_code=404, 
            detail="ArXiv MCP Agent not available. Please check server logs for initialization errors."
        )
    
    try:
        response = agent(request.query)
        return QueryResponse(
            response=str(response)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"⛔Query failed: {str(e)}")

# Web Search クエリエンドポイント
@app.post("/web-search/query", response_model=QueryResponse)
async def web_search_query(request: QueryRequest):
    agent = mcp_manager.get_agent(MCPServerType.WEB_SEARCH)
    if agent is None:
        raise HTTPException(
            status_code=404, 
            detail="Web Search MCP Agent not available. Please check server logs for initialization errors."
        )
    
    try:
        response = agent(request.query)
        return QueryResponse(
            response=str(response)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"⛔Query failed: {str(e)}")

# Web Researchクエリエンドポイント
@app.post("/web-research/query", response_model=QueryResponse)
async def web_research_query(request: QueryRequest):
    agent = mcp_manager.get_agent(MCPServerType.WEB_RESEARCH)
    if agent is None:
        raise HTTPException(
            status_code=404, 
            detail="Web Research MCP Agent not available. Please check server logs for initialization errors."
        )
    
    try:
        response = agent(request.query)
        return QueryResponse(
            response=str(response)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"⛔Query failed: {str(e)}")

# Serenaのプロジェクト有効化専用エンドポイント
@app.post("/serena/activate-project", response_model=dict)
async def serena_activate_project(request: ProjectActivateRequest):
    project_path = request.project_path
    
    if not project_path:
        raise HTTPException(
            status_code=400,
            detail="Project path is required"
        )
    
    agent = mcp_manager.get_agent(MCPServerType.SERENA)
    if agent is None:
        raise HTTPException(
            status_code=404, 
            detail="Serena MCP Agent not available. Please check server logs for initialization errors."
        )
    
    try:
        # プロジェクト有効化のためのクエリを実行
        response = agent(f"Activate the project {project_path}")
        return {
            "status": "success",
            "message": f"Project {project_path} activation request sent to Serena",
            "response": str(response)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Project activation failed: {str(e)}"
        )

# Serenaクエリエンドポイント
@app.post("/serena/query", response_model=QueryResponse)
async def serena_query(request: QueryRequest):
    agent = mcp_manager.get_agent(MCPServerType.SERENA)
    if agent is None:
        raise HTTPException(
            status_code=404, 
            detail="Serena MCP Agent not available. Please check server logs for initialization errors."
        )
    
    try:
        response = agent(request.query)
        return QueryResponse(
            response=str(response)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"⛔Query failed: {str(e)}")

# World Bankクエリエンドポイント
@app.post("/world_bank/query", response_model=QueryResponse)
async def world_bank_query(request: QueryRequest):
    agent = mcp_manager.get_agent(MCPServerType.WORLD_BANK)
    if agent is None:
        raise HTTPException(
            status_code=404, 
            detail="World Bank MCP Agent not available. Please check server logs for initialization errors."
        )
    
    try:
        response = agent(request.query)
        return QueryResponse(
            response=str(response)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"⛔Query failed: {str(e)}")

# Financial Datasetsクエリエンドポイント
@app.post("/financial_datasets/query", response_model=QueryResponse)
async def financial_datasets_query(request: QueryRequest):
    agent = mcp_manager.get_agent(MCPServerType.FINANCIAL_DATASETS)
    if agent is None:
        raise HTTPException(
            status_code=404, 
            detail="Financial Datasets MCP Agent not available. Please check server logs for initialization errors."
        )
    
    try:
        response = agent(request.query)
        return QueryResponse(
            response=str(response)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"⛔Query failed: {str(e)}")

# 設定変更（playwright）エンドポイント
@app.post("/playwright/configure", response_model=dict)
async def configure_playwright(options: PlaywrightOptions):
    success = mcp_manager.create_playwright_client(
        headless=options.headless,
        vision=options.vision
    )
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail="⛔Failed to configure Playwright with the specified options"
        )
    
    return {
        "status": "success",
        "message": f"Playwright configured with headless={options.headless}, vision={options.vision}"
    }

# 設定変更（ArXiv）エンドポイント
@app.post("/arxiv/configure", response_model=dict)
async def configure_arxiv(options: ArXivOptions):
    success = mcp_manager.configure_arxiv_client(
        storage_path=options.storage_path
    )
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail="⛔Failed to configure ArXiv MCP Server with the specified options"
        )
    
    return {
        "status": "success",
        "message": f"ArXiv MCP Server configured with storage_path={options.storage_path or 'default'}"
    }

# 設定変更（Web Search）エンドポイント
@app.post("/web-search/configure", response_model=dict)
async def configure_web_search(options: WebSearchOptions):
    success = mcp_manager.configure_web_search_client(
        max_results=options.max_results
    )
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail="⛔Failed to configure Web Search MCP Server with the specified options"
        )
    
    return {
        "status": "success",
        "message": f"Web Search MCP Server configured with max_results={options.max_results}"
    }

if __name__ == "__main__":
    # ポート競合を避けるために別のポートを使用
    port = 8001
    print(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)