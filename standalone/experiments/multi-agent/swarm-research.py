from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import asyncio
import uuid
from datetime import datetime

from strands import Agent
from strands.multiagent import Swarm
from strands.models import BedrockModel
import boto3
import os
from dotenv import load_dotenv

# 環境変数のロード
load_dotenv()

# FastAPIアプリケーションの作成
app = FastAPI(title="Strands Agents Swarm API", version="1.0.0")

# リクエストモデル
class SwarmRequest(BaseModel):
    query: str
    max_handoffs: Optional[int] = 6
    max_iterations: Optional[int] = 8
    execution_timeout: Optional[float] = 600.0
    node_timeout: Optional[float] = 180.0

# レスポンスモデル
class SwarmResponse(BaseModel):
    request_id: str
    status: str
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# 進行状況レスポンスモデル
class SwarmStatusResponse(BaseModel):
    request_id: str
    status: str
    completed: bool
    started_at: str
    updated_at: str
    node_history: Optional[List[str]] = None
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# 進行中のリクエストを保存する辞書
active_requests = {}

# Bedrock Runtimeクライアントを作成する関数
def create_bedrock_client():
    return boto3.client(
        service_name='bedrock-runtime',
        region_name='us-west-2',  # 使用するリージョンに合わせて変更
        aws_access_key_id=os.getenv("ACCESS_KEY"),
        aws_secret_access_key=os.getenv("SECRET_KEY"),
    )

# Bedrockモデルを作成する関数
def create_bedrock_model(client):
    return BedrockModel(
        model_id="anthropic.claude-3-sonnet-20240229-v1:0",  # 使用可能なモデルIDを指定
        client=client,
        temperature=0.1,
        max_tokens=4096,
        streaming=True,
    )

# エージェントを作成する関数
def create_agents(model):
    # リサーチエージェント
    research_agent = Agent(
        name="ResearchAgent", 
        system_prompt=("""あなたはリサーチ専門のエージェントです。

あなたの役割：
- データ、統計、事実に基づいた客観的な分析を行う
- 現状把握と背景情報の整理
- 信頼性の高い情報源からの情報収集と分析

やること：
1. 質問に対する基本的な情報と現状を具体的に分析する
2. データや統計を用いた客観的な現状分析を提供する
3. 事実に基づいた包括的なリサーチ結果を作成する

注意：あなたはリサーチの専門家です。分析が完了したら結果を報告してください。
"""), 
        model=model
    )

    # クリエイティブエージェント
    creative_agent = Agent(
        name="CreativeAgent",
        system_prompt=("""あなたは創造的なアイデアを提案するエージェントです。

あなたの役割：
- 革新的なアイデアや未来のシナリオを創造する
- 既存の枠組みを超えた発想を提供する
- 可能性を広げる創造的な視点を提案する

やること：
1. 提供された情報に対して創造的な視点や未来のシナリオを提案する
2. 革新的なアイデアや解決策を具体的に提示する
3. 想像力豊かな可能性を探求し、新しい視点を提供する

注意：あなたは創造性の専門家です。アイデアを提案したら結果を報告してください。
"""), 
        model=model
    )

    # 批判的エージェント
    critical_agent = Agent(
        name="CriticalAgent",
        system_prompt=("""あなたは批判的な分析を行うエージェントです。

あなたの役割：
- 客観的な視点から問題点やリスクを分析する
- 論理的な検証と批判的思考を提供する
- 潜在的な課題や制約を特定する

やること：
1. 提供された情報や提案を客観的に検証する
2. 具体的な問題点、リスク、制約を詳細に指摘する
3. 論理的な根拠に基づいた批判的分析を提供する

注意：あなたは批判的思考の専門家です。分析が完了したら結果を報告してください。
"""),
        model=model
    )

    # プロジェクトマネージャーエージェント
    pm_agent = Agent(
        name="PMAgent",
        system_prompt=("""あなたはプロジェクトマネージャーエージェントです。

あなたの役割：
- プロジェクト全体の進行管理と調整
- 各専門エージェントの成果物を統合
- 最終的な包括的回答の作成

やること：
1. 各専門エージェント（Research, Creative, Critical）に一度だけ具体的な作業を依頼する
2. 各エージェントからの成果物を収集する
3. 全ての情報を統合して最終的な包括的回答を作成する

重要：
- 各エージェントへの依頼は1回のみ
- 不要な再依頼や循環参照を避ける
- 効率的な協働を促進する

注意：あなたは統合管理の専門家です。全体をまとめて最終回答を提供してください。
"""),
        model=model
    )
    
    return [pm_agent, research_agent, creative_agent, critical_agent]

# スワームを実行する非同期関数
async def run_swarm(request_id: str, query: str, config: dict):
    try:
        # Bedrockクライアントとモデルの作成
        bedrock_client = create_bedrock_client()
        model = create_bedrock_model(bedrock_client)
        
        # エージェントの作成
        agents = create_agents(model)
        
        # Swarmの設定と実行
        swarm = Swarm(
            create_agents(model),
            max_handoffs=config.get('max_handoffs', 6),
            max_iterations=config.get('max_iterations', 8),
            execution_timeout=config.get('execution_timeout', 600.0),
            node_timeout=config.get('node_timeout', 180.0),
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

@app.get("/")
async def root():
    return {"message": "Strands Agents Swarm API", "version": "1.0.0"}

@app.post("/swarm", response_model=SwarmResponse)
async def create_swarm_request(request: SwarmRequest, background_tasks: BackgroundTasks):
    # リクエストIDの生成
    request_id = str(uuid.uuid4())
    
    # リクエスト情報の初期化
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
    
    # バックグラウンドでスワームを実行
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
        "status": "processing"
    }

@app.get("/swarm/{request_id}", response_model=SwarmStatusResponse)
async def get_swarm_status(request_id: str):
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

@app.get("/swarm", response_model=List[str])
async def list_swarm_requests():
    return list(active_requests.keys())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)