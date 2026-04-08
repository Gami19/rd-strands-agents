# main.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import asyncio
import uuid
from datetime import datetime
import logging

from strands import Agent
from strands.multiagent import Swarm, GraphBuilder
from strands.models import BedrockModel
from strands.multiagent.a2a import A2AServer
from strands_tools.a2a_client import A2AClientToolProvider
import boto3

from agents.router import RouterAgent
from agents.faq import FAQAgent
from agents.expert import ExpertAgent
from agents.general import GeneralAgent
from agents.workflow_coordinator import WorkflowCoordinator
from config import Config

# ログ設定
logging.getLogger("strands.multiagent").setLevel(logging.DEBUG)
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

# FastAPIアプリケーションの作成
app = FastAPI(title="Advanced Multi-Agent System API with A2A", version="2.0.0")

# リクエストモデル
class QueryRequest(BaseModel):
    query: str
    use_a2a: Optional[bool] = True
    workflow_type: Optional[str] = "swarm"  # "swarm", "graph", "workflow"

class SwarmRequest(BaseModel):
    query: str
    max_handoffs: Optional[int] = Config.MAX_HANDOFFS
    max_iterations: Optional[int] = Config.MAX_ITERATIONS
    execution_timeout: Optional[float] = Config.EXECUTION_TIMEOUT
    node_timeout: Optional[float] = Config.NODE_TIMEOUT

class GraphRequest(BaseModel):
    query: str
    workflow_type: str = "sequential"  # "sequential", "parallel", "branching"

class A2ARequest(BaseModel):
    query: str
    target_agent: Optional[str] = None
    use_discovery: bool = True

# レスポンスモデル
class QueryResponse(BaseModel):
    response: str
    agent: str
    routing_info: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}
    a2a_info: Optional[Dict[str, Any]] = None

class SwarmResponse(BaseModel):
    request_id: str
    status: str
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class GraphResponse(BaseModel):
    request_id: str
    status: str
    execution_order: List[str]
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class A2AResponse(BaseModel):
    response: str
    agent_url: str
    agent_card: Dict[str, Any]
    metadata: Dict[str, Any]

# 進行中のリクエストを保存
active_requests = {}

# エージェントのインスタンス
router_agent = RouterAgent()
faq_agent = FAQAgent()
expert_agent = ExpertAgent()
general_agent = GeneralAgent()
workflow_coordinator = WorkflowCoordinator()

# A2Aサーバーのインスタンス
a2a_servers = {}

# Bedrock関連の関数
def create_bedrock_client():
    return boto3.client(
        service_name='bedrock-runtime',
        region_name=Config.AWS_REGION,
        aws_access_key_id=Config.AWS_ACCESS_KEY,
        aws_secret_access_key=Config.AWS_SECRET_KEY,
    )

def create_bedrock_model(client, model_id: str = None):
    if not model_id:
        model_id = Config.FAQ_MODEL
    
    return BedrockModel(
        model_id=model_id,
        client=client,
        temperature=0.1,
        max_tokens=4096,
        streaming=True,
    )

def setup_a2a_servers():
    """A2Aサーバーをセットアップ"""
    global a2a_servers
    
    # 各エージェントをA2Aサーバーとして公開
    a2a_servers["router"] = A2AServer(
        agent=router_agent,
        http_url=f"http://localhost:{Config.A2A_ROUTER_PORT}"
    )
    
    a2a_servers["faq"] = A2AServer(
        agent=faq_agent,
        http_url=f"http://localhost:{Config.A2A_FAQ_PORT}"
    )
    
    a2a_servers["expert"] = A2AServer(
        agent=expert_agent,
        http_url=f"http://localhost:{Config.A2A_EXPERT_PORT}"
    )
    
    a2a_servers["general"] = A2AServer(
        agent=general_agent,
        http_url=f"http://localhost:{Config.A2A_GENERAL_PORT}"
    )
    
    # ワークフローコーディネーターもA2Aサーバーとして公開
    a2a_servers["workflow"] = A2AServer(
        agent=workflow_coordinator,
        http_url=f"http://localhost:{Config.A2A_WORKFLOW_PORT}"
    )

@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の初期化"""
    setup_a2a_servers()
    logging.info("A2A servers initialized")

@app.get("/")
async def root():
    return {
        "message": "Advanced Multi-Agent System API with A2A", 
        "version": "2.0.0",
        "endpoints": [
            "/chat", "/swarm", "/swarm/{request_id}", 
            "/graph", "/a2a", "/a2a/discover", "/workflow"
        ],
        "a2a_servers": list(a2a_servers.keys())
    }

@app.post("/chat", response_model=QueryResponse)
async def chat(request: QueryRequest):
    """改良されたルーティング＋エージェント実行（A2A対応）"""
    try:
        if request.use_a2a and request.workflow_type == "workflow":
            # ワークフローコーディネーターを使用
            result = await workflow_coordinator.coordinate_workflow(request.query)
            return QueryResponse(
                response=result.get("response", "応答を取得できませんでした"),
                agent="WorkflowCoordinator",
                routing_info={"workflow_type": "coordinated"},
                metadata=result.get("metadata", {}),
                a2a_info={"a2a_enabled": True}
            )
        
        # Step 1: ルーティング
        routing_result = router_agent.route_query(request.query)
        agent_type = routing_result["agent_type"]
        
        # Step 2: 適切なエージェントで処理
        if agent_type == "FAQ":
            result = await faq_agent.process_with_search(request.query)
        elif agent_type == "EXPERT":
            result = await expert_agent.process_with_search(request.query)
        else:  # GENERAL
            result = general_agent.process_general(request.query)
        
        return QueryResponse(
            response=result.get("response", "応答を取得できませんでした"),
            agent=result.get("agent", "Unknown"),
            routing_info=routing_result,
            metadata={
                "has_search_results": result.get("has_search_results", False),
                "analysis_depth": result.get("analysis_depth", ""),
                "type": result.get("type", ""),
                "search_count": result.get("search_count", 0)
            },
            a2a_info={"a2a_enabled": request.use_a2a}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"処理エラー: {str(e)}")

@app.post("/a2a", response_model=A2AResponse)
async def a2a_chat(request: A2ARequest):
    """A2Aクライアントを使用したエージェント間通信"""
    try:
        if request.use_discovery:
            # A2Aクライアントツールプロバイダーを使用
            provider = A2AClientToolProvider(
                known_agent_urls=[
                    f"http://localhost:{Config.A2A_FAQ_PORT}",
                    f"http://localhost:{Config.A2A_EXPERT_PORT}",
                    f"http://localhost:{Config.A2A_GENERAL_PORT}"
                ]
            )
            
            # オーケストレーターエージェントを作成
            orchestrator = Agent(
                tools=provider.tools,
                system_prompt="""あなたはオーケストレーターエージェントです。
                利用可能なA2Aエージェントを発見し、適切なエージェントにタスクを委譲してください。
                各エージェントの専門性を考慮して最適な選択を行ってください。"""
            )
            
            response = orchestrator(request.query)
            
            return A2AResponse(
                response=str(response),
                agent_url="discovered",
                agent_card={"discovery": "enabled"},
                metadata={"method": "discovery"}
            )
        else:
            # 特定のエージェントに直接通信
            target_url = f"http://localhost:{Config.A2A_FAQ_PORT}"
            if request.target_agent == "expert":
                target_url = f"http://localhost:{Config.A2A_EXPERT_PORT}"
            elif request.target_agent == "general":
                target_url = f"http://localhost:{Config.A2A_GENERAL_PORT}"
            
            # A2Aクライアントを使用して通信
            import httpx
            from a2a.client import A2ACardResolver, A2AClient
            from a2a.types import MessageSendParams, SendMessageRequest
            
            async with httpx.AsyncClient() as client:
                resolver = A2ACardResolver(httpx_client=client, base_url=target_url)
                agent_card = await resolver.get_agent_card()
                
                a2a_client = A2AClient(httpx_client=client, agent_card=agent_card)
                
                payload = {
                    "message": {
                        "role": "user",
                        "parts": [{"kind": "text", "text": request.query}],
                        "messageId": str(uuid.uuid4()),
                    }
                }
                
                from a2a.types import SendMessageRequest
                request_obj = SendMessageRequest(
                    id=str(uuid.uuid4()), 
                    params=MessageSendParams(**payload)
                )
                
                response = await a2a_client.send_message(request_obj)
                
                return A2AResponse(
                    response=str(response),
                    agent_url=target_url,
                    agent_card=agent_card.model_dump(),
                    metadata={"method": "direct"}
                )
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"A2A通信エラー: {str(e)}")

@app.get("/a2a/discover")
async def discover_a2a_agents():
    """利用可能なA2Aエージェントを発見"""
    try:
        discovered_agents = []
        
        for name, server in a2a_servers.items():
            try:
                import httpx
                async with httpx.AsyncClient() as client:
                    from a2a.client import A2ACardResolver
                    resolver = A2ACardResolver(
                        httpx_client=client, 
                        base_url=server.http_url
                    )
                    agent_card = await resolver.get_agent_card()
                    discovered_agents.append({
                        "name": name,
                        "url": server.http_url,
                        "card": agent_card.model_dump()
                    })
            except Exception as e:
                logging.warning(f"Failed to discover {name}: {e}")
        
        return {
            "discovered_agents": discovered_agents,
            "total_count": len(discovered_agents)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"エージェント発見エラー: {str(e)}")

@app.post("/graph", response_model=GraphResponse)
async def create_graph_workflow(request: GraphRequest):
    """Graphパターンでのワークフロー実行"""
    try:
        request_id = str(uuid.uuid4())
        
        # Bedrockクライアントとモデルの作成
        bedrock_client = create_bedrock_client()
        
        # グラフ用のエージェント作成
        research_agent = Agent(
            name="researcher",
            system_prompt="あなたは研究専門家です。与えられたトピックについて詳細な調査を行ってください。",
            model=create_bedrock_model(bedrock_client, Config.EXPERT_MODEL)
        )
        
        analysis_agent = Agent(
            name="analyst",
            system_prompt="あなたは分析専門家です。研究データを分析し、洞察を抽出してください。",
            model=create_bedrock_model(bedrock_client, Config.EXPERT_MODEL)
        )
        
        report_agent = Agent(
            name="reporter",
            system_prompt="あなたはレポート作成専門家です。分析結果を基に分かりやすいレポートを作成してください。",
            model=create_bedrock_model(bedrock_client, Config.GENERAL_MODEL)
        )
        
        # グラフの構築
        builder = GraphBuilder()
        
        if request.workflow_type == "sequential":
            # シーケンシャルパイプライン
            builder.add_node(research_agent, "research")
            builder.add_node(analysis_agent, "analysis")
            builder.add_node(report_agent, "report")
            
            builder.add_edge("research", "analysis")
            builder.add_edge("analysis", "report")
            
        elif request.workflow_type == "parallel":
            # 並列処理
            builder.add_node(research_agent, "research")
            builder.add_node(analysis_agent, "analysis")
            builder.add_node(report_agent, "report")
            
            # 並列実行（依存関係なし）
            builder.set_entry_point("research")
            builder.set_entry_point("analysis")
            builder.set_entry_point("report")
            
        elif request.workflow_type == "branching":
            # 分岐ロジック
            classifier_agent = Agent(
                name="classifier",
                system_prompt="あなたは分類専門家です。質問の性質を分析し、適切な処理経路を決定してください。",
                model=create_bedrock_model(bedrock_client, Config.ROUTER_MODEL)
            )
            
            builder.add_node(classifier_agent, "classifier")
            builder.add_node(research_agent, "research")
            builder.add_node(analysis_agent, "analysis")
            builder.add_node(report_agent, "report")
            
            # 条件付きエッジ
            def is_research_needed(state):
                classifier_result = state.results.get("classifier")
                if not classifier_result:
                    return False
                result_text = str(classifier_result.result)
                return "research" in result_text.lower()
            
            def is_analysis_needed(state):
                classifier_result = state.results.get("classifier")
                if not classifier_result:
                    return False
                result_text = str(classifier_result.result)
                return "analysis" in result_text.lower()
            
            builder.add_edge("classifier", "research", condition=is_research_needed)
            builder.add_edge("classifier", "analysis", condition=is_analysis_needed)
            builder.add_edge("research", "report")
            builder.add_edge("analysis", "report")
        
        # グラフの構築と実行
        graph = builder.build()
        result = graph(request.query)
        
        # 結果の処理
        formatted_results = {}
        for node_id, node_result in result.results.items():
            if node_result and node_result.result and node_result.result.message:
                content = node_result.result.message.get('content', [])
                if content and isinstance(content, list) and len(content) > 0:
                    formatted_results[node_id] = content[0].get('text', '')
                else:
                    formatted_results[node_id] = "内容が取得できませんでした"
        
        # リクエスト情報の保存
        active_requests[request_id] = {
            "status": "completed",
            "completed": True,
            "started_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "query": request.query,
            "workflow_type": request.workflow_type,
            "results": formatted_results,
            "execution_order": [node.node_id for node in result.execution_order]
        }
        
        return GraphResponse(
            request_id=request_id,
            status="completed",
            execution_order=[node.node_id for node in result.execution_order],
            results=formatted_results
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graphワークフローエラー: {str(e)}")

@app.post("/workflow")
async def create_workflow():
    """ワークフローツールを使用したワークフロー作成"""
    try:
        from strands_tools import workflow
        
        # ワークフローコーディネーターエージェントを作成
        coordinator = Agent(
            tools=[workflow],
            system_prompt="""あなたはワークフローコーディネーターです。
            ユーザーの要求に基づいて適切なワークフローを作成し、実行してください。"""
        )
        
        # サンプルワークフローの作成
        workflow_result = coordinator.tool.workflow(
            action="create",
            workflow_id="sample_workflow",
            tasks=[
                {
                    "task_id": "data_collection",
                    "description": "データ収集と前処理",
                    "system_prompt": "データ収集と前処理を専門とするエージェント",
                    "priority": 5
                },
                {
                    "task_id": "analysis",
                    "description": "データ分析と洞察抽出",
                    "dependencies": ["data_collection"],
                    "system_prompt": "データ分析を専門とするエージェント",
                    "priority": 3
                },
                {
                    "task_id": "reporting",
                    "description": "レポート作成と可視化",
                    "dependencies": ["analysis"],
                    "system_prompt": "レポート作成を専門とするエージェント",
                    "priority": 2
                }
            ]
        )
        
        return {
            "message": "ワークフローが作成されました",
            "workflow_id": "sample_workflow",
            "result": workflow_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ワークフロー作成エラー: {str(e)}")

# 既存のSwarm機能（改良版）
async def run_swarm(request_id: str, query: str, config: dict):
    try:
        # Bedrockクライアントとモデルの作成
        bedrock_client = create_bedrock_client()
        model = create_bedrock_model(bedrock_client)
        
        # スワーム用のエージェント作成（A2A対応）
        swarm_agents = [
            Agent(
                name="RouterSwarmAgent",
                system_prompt="あなたはルーティング分析を行うエージェントです。質問を分析し、どのような専門知識が必要かを判断してください。",
                model=model
            ),
            Agent(
                name="FAQSwarmAgent", 
                system_prompt="あなたはFAQ専門エージェントです。よくある質問に対して正確で分かりやすい回答を提供してください。",
                model=model
            ),
            Agent(
                name="ExpertSwarmAgent",
                system_prompt="あなたは専門家エージェントです。複雑で専門的な質問に対して詳細な分析と回答を提供してください。",
                model=model
            )
        ]
        
        # Swarmの設定と実行
        swarm = Swarm(
            swarm_agents,
            max_handoffs=config.get('max_handoffs', Config.MAX_HANDOFFS),
            max_iterations=config.get('max_iterations', Config.MAX_ITERATIONS),
            execution_timeout=config.get('execution_timeout', Config.EXECUTION_TIMEOUT),
            node_timeout=config.get('node_timeout', Config.NODE_TIMEOUT),
            repetitive_handoff_detection_window=3,
            repetitive_handoff_min_unique_agents=2
        )
        
        # スワームの実行
        result = swarm(query)
        
        # 結果の処理
        formatted_results = {}
        for agent_name, node_result in result.results.items():
            if node_result and node_result.result and node_result.result.message:
                content = node_result.result.message.get('content', [])
                if content and isinstance(content, list) and len(content) > 0:
                    formatted_results[agent_name] = content[0].get('text', '')
                else:
                    formatted_results[agent_name] = "内容が取得できませんでした"
        
        # ノード履歴の処理
        node_history = [node.node_id for node in result.node_history]
        
        # リクエスト情報の更新
        active_requests[request_id].update({
            "status": "completed",
            "completed": True,
            "updated_at": datetime.now().isoformat(),
            "results": formatted_results,
            "node_history": node_history
        })
        
    except Exception as e:
        # エラー情報の更新
        active_requests[request_id].update({
            "status": "failed",
            "completed": True,
            "updated_at": datetime.now().isoformat(),
            "error": str(e)
        })

@app.post("/swarm", response_model=SwarmResponse)
async def create_swarm_request(request: SwarmRequest, background_tasks: BackgroundTasks):
    """改良されたSwarmパターンでの実行（A2A対応）"""
    request_id = str(uuid.uuid4())
    
    active_requests[request_id] = {
        "status": "processing",
        "completed": False,
        "started_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "query": request.query,
        "config": {
            "max_handoffs": request.max_handoffs,
            "max_iterations": request.max_iterations,
            "execution_timeout": request.execution_timeout,
            "node_timeout": request.node_timeout
        }
    }
    
    background_tasks.add_task(
        run_swarm, 
        request_id, 
        request.query, 
        {
            "max_handoffs": request.max_handoffs,
            "max_iterations": request.max_iterations,
            "execution_timeout": request.execution_timeout,
            "node_timeout": request.node_timeout
        }
    )
    
    return {
        "request_id": request_id,
        "status": "processing",
        "results": None
    }

@app.get("/swarm/{request_id}", response_model=SwarmStatusResponse)
async def get_swarm_status(request_id: str):
    """Swarm実行状況の確認"""
    if request_id not in active_requests:
        raise HTTPException(status_code=404, detail="Request not found")
    
    request_info = active_requests[request_id]
    
    return {
        "request_id": request_id,
        "status": request_info["status"],
        "completed": request_info["completed"],
        "started_at": request_info["started_at"],
        "updated_at": request_info["updated_at"],
        "node_history": request_info.get("node_history"),
        "results": request_info.get("results"),
        "error": request_info.get("error")
    }



@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {
        "status": "healthy", 
        "framework": "strands-agents",
        "a2a_enabled": True,
        "patterns": ["swarm", "graph", "workflow"]
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)