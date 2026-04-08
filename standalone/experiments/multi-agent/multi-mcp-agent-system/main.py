from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import os
from dotenv import load_dotenv
from typing import Dict, List, Optional
import asyncio
import traceback

from multi_agent_manager import MultiAgentManager

# 環境変数のロード
load_dotenv()

# Lifespan contextマネージャ
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 起動時の処理
    try:
        await multi_agent_manager.initialize_agents()
        print("🚀 Multi-Agent A2A System initialized successfully")
    except Exception as e:
        print(f"⛔Failed during startup: {e}")
        traceback.print_exc()
    
    yield  # FastAPIアプリケーションの実行中
    
    # シャットダウン時の処理
    await multi_agent_manager.shutdown()

app = FastAPI(
    title="Multi-Agent A2A System", 
    version="1.0.0", 
    description="Strands Agents A2Aを使用したマルチエージェントシステム",
    lifespan=lifespan
)

# マルチエージェントマネージャーのインスタンス
multi_agent_manager = MultiAgentManager()

# リクエストモデル
class QueryRequest(BaseModel):
    query: str
    agent_type: Optional[str] = "all"  # "research", "analysis", "report", "all"

class MultiAgentRequest(BaseModel):
    query: str
    workflow: List[str] = ["research", "analysis", "report"]  # 実行順序

# レスポンスモデル
class QueryResponse(BaseModel):
    response: str
    agent_type: str
    status: str = "success"

class MultiAgentResponse(BaseModel):
    responses: Dict[str, str]
    workflow_result: str
    status: str = "success"

@app.get("/")
async def root():
    return {
        "message": "Multi-Agent A2A System is running",
        "available_agents": ["research", "analysis", "report"],
        "endpoints": {
            "single_agent": "/agent/{agent_type}/query",
            "multi_agent": "/multi-agent/query",
            "workflow": "/workflow/execute",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    agent_status = await multi_agent_manager.get_agent_status()
    return {
        "status": "healthy",
        "agents": agent_status,
        "system": "Multi-Agent A2A System"
    }

# 個別エージェントクエリエンドポイント
@app.post("/agent/{agent_type}/query", response_model=QueryResponse)
async def single_agent_query(agent_type: str, request: QueryRequest):
    try:
        response = await multi_agent_manager.query_agent(agent_type, request.query)
        return QueryResponse(
            response=response,
            agent_type=agent_type,
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

# マルチエージェント連携クエリエンドポイント
@app.post("/multi-agent/query", response_model=MultiAgentResponse)
async def multi_agent_query(request: MultiAgentRequest):
    try:
        responses, workflow_result = await multi_agent_manager.execute_workflow(
            request.query, 
            request.workflow
        )
        return MultiAgentResponse(
            responses=responses,
            workflow_result=workflow_result,
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multi-agent query failed: {str(e)}")

# ワークフロー実行エンドポイント
@app.post("/workflow/execute", response_model=MultiAgentResponse)
async def execute_workflow(request: MultiAgentRequest):
    try:
        responses, workflow_result = await multi_agent_manager.execute_workflow(
            request.query, 
            request.workflow
        )
        return MultiAgentResponse(
            responses=responses,
            workflow_result=workflow_result,
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")

# エージェント設定エンドポイント
@app.post("/agent/{agent_type}/configure")
async def configure_agent(agent_type: str, config: dict):
    try:
        success = await multi_agent_manager.configure_agent(agent_type, config)
        return {
            "status": "success" if success else "failed",
            "message": f"Agent {agent_type} configuration updated"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Configuration failed: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8002))
    print(f"Starting Multi-Agent A2A System on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)