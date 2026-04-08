
import asyncio
import platform
import sys

# Windows環境での修正
if platform.system() == "Windows":
    # ProactorEventLoopPolicyを設定（subprocessをサポート）
    if sys.version_info >= (3, 8):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import uuid
from datetime import datetime
import traceback
from services.orchestrator import orchestrator
from services.arxiv_mcp_service import arxiv_mcp_service
from config import Config

@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    # 起動時処理
    print("=== 分散型マルチエージェントシステム初期化開始 ===")
    
    # 1. arXiv MCP サーバー初期化（Windows環境対応）
    try:
        print(" arXiv MCP サーバー初期化中...")
        arxiv_initialized = arxiv_mcp_service.initialize()
        
        if arxiv_initialized:
            print("✅ arXiv MCP サーバー: 利用可能")
            print(f"   ストレージパス: {arxiv_mcp_service.storage_path}")
            print(f"   最大論文数: {arxiv_mcp_service.max_papers}")
        else:
            print("⚠️  arXiv MCP サーバー: 利用不可（Knowledge Baseのみで動作）")
            if arxiv_mcp_service.connection_error:
                print(f"   エラー詳細: {arxiv_mcp_service.connection_error}")
    except Exception as e:
        print(f"⛔Failed during arXiv MCP startup: {e}")
        traceback.print_exc()
    
    # 2. エージェントシステム初期化
    orchestrator.initialize_agents()
    
    print("=== 初期化完了 ===")
    
    yield  # アプリケーション実行
    
    # 終了時処理
    print("=== アプリケーション終了処理開始 ===")
    arxiv_mcp_service.cleanup()
    print("=== 終了処理完了 ===")

# FastAPIアプリケーション作成
app = FastAPI(
    title="Distributed Multi-Agent System with arXiv",
    version="1.0.0",
    description="エージェント主導判定によるarXiv MCP統合分散型マルチエージェントシステム",
    lifespan=lifespan
)

# リクエスト・レスポンスモデル
class DistributedQueryRequest(BaseModel):
    query: str
    include_detailed_results: Optional[bool] = True

class AsyncAnalysisRequest(BaseModel):
    query: str
    include_detailed_results: Optional[bool] = True

class DistributedQueryResponse(BaseModel):
    response: str
    processing_time: float
    agents_executed: List[str]
    status: str
    detailed_results: Optional[Dict[str, Any]] = None

class AsyncAnalysisResponse(BaseModel):
    request_id: str
    status: str
    message: str

class AsyncStatusResponse(BaseModel):
    request_id: str
    status: str
    completed: bool
    started_at: str
    updated_at: str
    processing_time: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# 非同期処理結果保存
async_results = {}

# バックグラウンド処理関数
async def run_distributed_analysis_async(request_id: str, query: str, include_detailed_results: bool):
    """バックグラウンドで分散分析を実行"""
    try:
        print(f"非同期分散分析開始: {query} (ID: {request_id})")
        
        # 分散分析実行
        result = await orchestrator.process_distributed_analysis(query)
        
        # 結果の整理
        analysis_result = {
            "response": result["final_response"],
            "processing_time": result["processing_time"],
            "agents_executed": result.get("agents_executed", []),
            "status": result["status"]
        }
        
        if include_detailed_results:
            analysis_result["detailed_results"] = {
                "analysis_results": result.get("analysis_results", {}),
                "execution_phases": result.get("execution_phases", []),
                "query": result["query"],
                "arxiv_info": result.get("arxiv_info", {})
            }
        
        # 結果保存
        async_results[request_id].update({
            "status": "completed",
            "completed": True,
            "updated_at": datetime.now().isoformat(),
            "processing_time": result["processing_time"],
            "result": analysis_result
        })
        
        print(f"非同期分散分析完了: {request_id}")
        
    except Exception as e:
        print(f"非同期分散分析エラー: {request_id} - {str(e)}")
        
        # エラー情報保存
        async_results[request_id].update({
            "status": "failed",
            "completed": True,
            "updated_at": datetime.now().isoformat(),
            "error": str(e)
        })

@app.get("/")
async def root():
    return {
        "message": "Distributed Multi-Agent System with arXiv MCP",
        "description": "リサーチ、クリエイティブ、批判的、PM エージェントによる分散分析システム（arXiv MCP統合）",
        "version": "1.0.0",
        "endpoints": [
            "/analyze", 
            "/analyze-async", 
            "/status/{request_id}",
            "/arxiv-status",
            "/evaluation-stats"
        ],
        "agents": ["ResearchAgent", "CreativeAgent", "CriticalAgent", "PMAgent"],
        "features": ["Agent-driven arXiv evaluation", "Distributed analysis", "Knowledge Base integration"]
    }

@app.post("/analyze", response_model=DistributedQueryResponse)
async def analyze_distributed(request: DistributedQueryRequest):
    """
    すべてのエージェントで分散分析を実行し、統合結果を返す（同期処理）
    ResearchAgentが自律的にarXiv検索の必要性を判断
    """
    try:
        print(f"分散分析開始: {request.query}")
        
        # 分散分析実行
        result = await orchestrator.process_distributed_analysis(request.query)
        
        response_data = {
            "response": result["final_response"],
            "processing_time": result["processing_time"],
            "agents_executed": result.get("agents_executed", []),
            "status": result["status"]
        }
        
        # 詳細結果を含める場合
        if request.include_detailed_results:
            response_data["detailed_results"] = {
                "analysis_results": result.get("analysis_results", {}),
                "execution_phases": result.get("execution_phases", []),
                "query": result["query"],
                "arxiv_info": result.get("arxiv_info", {})
            }
        
        return DistributedQueryResponse(**response_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分散分析エラー: {str(e)}")

@app.post("/analyze-async", response_model=AsyncAnalysisResponse)
async def analyze_distributed_async(request: AsyncAnalysisRequest, background_tasks: BackgroundTasks):
    """
    分散分析を非同期で実行（バックグラウンド処理）
    """
    # リクエストIDの生成
    request_id = str(uuid.uuid4())
    
    # リクエスト情報の初期化
    async_results[request_id] = {
        "status": "processing",
        "completed": False,
        "started_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "query": request.query,
        "include_detailed_results": request.include_detailed_results
    }
    
    # バックグラウンドで分散分析を実行
    background_tasks.add_task(
        run_distributed_analysis_async, 
        request_id, 
        request.query, 
        request.include_detailed_results
    )
    
    return AsyncAnalysisResponse(
        request_id=request_id,
        status="processing",
        message=f"分散分析を開始しました。/status/{request_id} で進捗を確認できます。"
    )

@app.get("/status/{request_id}", response_model=AsyncStatusResponse)
async def get_analysis_status(request_id: str):
    """
    非同期分散分析の状況確認
    """
    if request_id not in async_results:
        raise HTTPException(status_code=404, detail="Request ID not found")
    
    request_info = async_results[request_id]
    
    return AsyncStatusResponse(
        request_id=request_id,
        status=request_info["status"],
        completed=request_info["completed"],
        started_at=request_info["started_at"],
        updated_at=request_info["updated_at"],
        processing_time=request_info.get("processing_time"),
        result=request_info.get("result"),
        error=request_info.get("error")
    )

@app.get("/requests", response_model=List[str])
async def list_analysis_requests():
    """
    すべての分析リクエストID一覧
    """
    return list(async_results.keys())

@app.delete("/requests/{request_id}")
async def delete_analysis_request(request_id: str):
    """
    特定のリクエスト結果を削除
    """
    if request_id not in async_results:
        raise HTTPException(status_code=404, detail="Request ID not found")
    
    del async_results[request_id]
    return {"message": f"Request {request_id} deleted successfully"}

@app.delete("/requests")
async def clear_all_requests():
    """
    すべてのリクエスト結果をクリア
    """
    cleared_count = len(async_results)
    async_results.clear()
    return {"message": f"Cleared {cleared_count} requests"}

@app.get("/arxiv-status")
async def arxiv_status():
    """arXiv MCP サーバーの状態確認"""
    return {
        "connected": arxiv_mcp_service.is_connected,
        "storage_path": arxiv_mcp_service.storage_path,
        "max_papers": arxiv_mcp_service.max_papers,
        "connection_error": arxiv_mcp_service.connection_error,
        "agent_available": arxiv_mcp_service.agent is not None
    }

@app.get("/evaluation-stats")
async def get_evaluation_stats():
    """ResearchAgentの判定統計"""
    log = orchestrator.evaluation_log
    
    if not log:
        return {"message": "評価ログがありません"}
    
    total = len(log)
    arxiv_used = sum(1 for entry in log if entry['needs_arxiv'])
    
    confidence_stats = {}
    for entry in log:
        confidence = entry['confidence']
        confidence_stats[confidence] = confidence_stats.get(confidence, 0) + 1
    
    # 最近の傾向分析
    recent_log = log[-20:] if len(log) >= 20 else log
    recent_arxiv_used = sum(1 for entry in recent_log if entry['needs_arxiv'])
    
    return {
        "total_evaluations": total,
        "arxiv_searches": arxiv_used,
        "arxiv_usage_rate": f"{(arxiv_used/total*100):.1f}%" if total > 0 else "0%",
        "recent_usage_rate": f"{(recent_arxiv_used/len(recent_log)*100):.1f}%" if recent_log else "0%",
        "confidence_distribution": confidence_stats,
        "recent_evaluations": log[-10:]  # 最新10件
    }

@app.get("/agents")
async def get_agents_info():
    """
    エージェント情報取得
    """
    return {
        "agents": {
            "ResearchAgent": {
                "role": "事実・データに基づく客観的分析（arXiv検索判定を含む）",
                "model": Config.RESEARCH_MODEL,
                "phase": 1,
                "features": ["Knowledge Base search", "arXiv evaluation", "Academic paper integration"]
            },
            "CreativeAgent": {
                "role": "革新的なアイデアや未来シナリオを提案",
                "model": Config.CREATIVE_MODEL,
                "phase": 1
            },
            "CriticalAgent": {
                "role": "問題点やリスクを分析",
                "model": Config.CRITICAL_MODEL,
                "phase": 2
            },
            "PMAgent": {
                "role": "全体調整と最終回答の統合",
                "model": Config.PM_MODEL,
                "phase": 3
            }
        },
        "execution_flow": [
            "Phase 1: ResearchAgent & CreativeAgent (並列実行)",
            "  - ResearchAgent: KB検索 → 自律的arXiv判定 → 必要時arXiv検索実行",
            "  - CreativeAgent: 創造的アイデア生成",
            "Phase 2: CriticalAgent (Phase1の結果を参考)",
            "Phase 3: PMAgent (全エージェントの結果を統合)"
        ],
        "arxiv_integration": {
            "max_papers": Config.ARXIV_MAX_PAPERS,
            "storage_path": arxiv_mcp_service.storage_path,
            "evaluation_method": "Agent-driven autonomous evaluation"
        }
    }

@app.get("/health")
async def health_check():
    """
    ヘルスチェック
    """
    return {
        "status": "healthy",
        "system": "distributed-multi-agent-with-arxiv",
        "active_requests": len(async_results),
        "agents": ["ResearchAgent", "CreativeAgent", "CriticalAgent", "PMAgent"],
        "arxiv_mcp": {
            "connected": arxiv_mcp_service.is_connected,
            "storage_available": arxiv_mcp_service.storage_path is not None
        }
    }

# arXiv論文直接検索エンドポイント（テスト・デバッグ用）
@app.post("/arxiv/direct-search")
async def direct_arxiv_search(request: DistributedQueryRequest):
    """
    arXiv MCP サーバーへの直接検索（テスト用）
    """
    if not arxiv_mcp_service.is_connected:
        raise HTTPException(
            status_code=503, 
            detail=f"arXiv MCP サーバーに接続されていません: {arxiv_mcp_service.connection_error}"
        )
    
    try:
        result = await arxiv_mcp_service.search_and_analyze_papers(request.query)
        return {
            "query": request.query,
            "result": result,
            "storage_path": arxiv_mcp_service.storage_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"arXiv検索エラー: {str(e)}")

if __name__ == "__main__":
    print("🚀 分散型マルチエージェントシステム（arXiv MCP統合）を起動中...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)