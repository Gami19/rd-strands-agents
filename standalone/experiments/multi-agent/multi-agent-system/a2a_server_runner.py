# a2a_server_runner.py
import asyncio
import uvicorn
from strands.multiagent.a2a import A2AServer
from agents.router import RouterAgent
from agents.faq import FAQAgent
from agents.expert import ExpertAgent
from agents.general import GeneralAgent
from agents.workflow_coordinator import WorkflowCoordinator
from config import Config

async def start_a2a_servers():
    """各エージェントのA2Aサーバーを起動"""
    
    # エージェントのインスタンス作成
    router_agent = RouterAgent()
    faq_agent = FAQAgent()
    expert_agent = ExpertAgent()
    general_agent = GeneralAgent()
    workflow_coordinator = WorkflowCoordinator()
    
    # A2Aサーバーの作成
    router_server = A2AServer(
        agent=router_agent,
        http_url=f"http://localhost:{Config.A2A_ROUTER_PORT}"
    )
    
    faq_server = A2AServer(
        agent=faq_agent,
        http_url=f"http://localhost:{Config.A2A_FAQ_PORT}"
    )
    
    expert_server = A2AServer(
        agent=expert_agent,
        http_url=f"http://localhost:{Config.A2A_EXPERT_PORT}"
    )
    
    general_server = A2AServer(
        agent=general_agent,
        http_url=f"http://localhost:{Config.A2A_GENERAL_PORT}"
    )
    
    workflow_server = A2AServer(
        agent=workflow_coordinator,
        http_url=f"http://localhost:{Config.A2A_WORKFLOW_PORT}"
    )
    
    # FastAPIアプリケーションの取得
    router_app = router_server.to_fastapi_app()
    faq_app = faq_server.to_fastapi_app()
    expert_app = expert_server.to_fastapi_app()
    general_app = general_server.to_fastapi_app()
    workflow_app = workflow_server.to_fastapi_app()
    
    # 各サーバーの起動
    configs = [
        (router_app, Config.A2A_ROUTER_PORT, "Router"),
        (faq_app, Config.A2A_FAQ_PORT, "FAQ"),
        (expert_app, Config.A2A_EXPERT_PORT, "Expert"),
        (general_app, Config.A2A_GENERAL_PORT, "General"),
        (workflow_app, Config.A2A_WORKFLOW_PORT, "Workflow")
    ]
    
    # 並行してサーバーを起動
    tasks = []
    for app, port, name in configs:
        task = asyncio.create_task(
            run_server(app, port, name)
        )
        tasks.append(task)
    
    # すべてのサーバーが起動するまで待機
    await asyncio.gather(*tasks)

async def run_server(app, port: int, name: str):
    """個別のサーバーを起動"""
    try:
        print(f"Starting {name} A2A server on port {port}")
        config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()
    except Exception as e:
        print(f"Error starting {name} server: {e}")

if __name__ == "__main__":
    print("Starting A2A servers...")
    asyncio.run(start_a2a_servers())

