# services/orchestrator.py
import asyncio
from typing import Dict, Any
from datetime import datetime

from agents.research import ResearchAgent
from agents.creative import CreativeAgent
from agents.critical import CriticalAgent
from agents.pm import PMAgent
from services.arxiv_mcp_service import arxiv_mcp_service
from config import Config

class MultiAgentOrchestrator:
    def __init__(self):
        self.research_agent = None
        self.creative_agent = CreativeAgent()
        self.critical_agent = CriticalAgent()
        self.pm_agent = PMAgent()
        self.evaluation_log = []
    
    def initialize_agents(self):
        """エージェントを初期化"""
        self.research_agent = ResearchAgent()
        print("✅ 全エージェント初期化完了")
    
    async def process_distributed_analysis(self, query: str) -> Dict[str, Any]:
        """分散分析を実行し、結果を統合"""
        start_time = datetime.now()
        
        try:
            if not self.research_agent:
                self.initialize_agents()
            
            # Phase 1: 並列でリサーチとクリエイティブ分析を実行
            print(f"Phase 1: 並列分析開始 - {query[:50]}...")
            
            research_task = asyncio.create_task(
                self._run_with_timeout(
                    self.research_agent.analyze(query),
                    Config.PARALLEL_TIMEOUT,
                    "ResearchAgent"
                )
            )
            
            creative_task = asyncio.create_task(
                self._run_with_timeout(
                    self.creative_agent.create_ideas(query),
                    Config.PARALLEL_TIMEOUT,
                    "CreativeAgent"
                )
            )
            
            # 並列実行完了を待機
            research_result, creative_result = await asyncio.gather(
                research_task, creative_task, return_exceptions=True
            )
            
            # エラーハンドリング
            if isinstance(research_result, Exception):
                research_result = {
                    "agent": "ResearchAgent", 
                    "analysis": f"エラー: {str(research_result)}", 
                    "status": "error"
                }
            
            if isinstance(creative_result, Exception):
                creative_result = {
                    "agent": "CreativeAgent", 
                    "ideas": f"エラー: {str(creative_result)}", 
                    "status": "error"
                }
            
            # 評価ログの記録
            if research_result.get('search_evaluation'):
                self.log_evaluation_decision(query, research_result['search_evaluation'])
            
            print(f"Phase 1 完了: Research={research_result.get('status')}, Creative={creative_result.get('status')}")
            
            # Phase 2: 批判的分析（前の結果を参考に）
            print("Phase 2: 批判的分析開始...")
            
            critical_result = await self._run_with_timeout(
                self.critical_agent.analyze_critically(
                    query,
                    research_result.get('analysis', ''),
                    creative_result.get('ideas', '')
                ),
                Config.PARALLEL_TIMEOUT,
                "CriticalAgent"
            )
            
            if isinstance(critical_result, Exception):
                critical_result = {
                    "agent": "CriticalAgent", 
                    "critical_analysis": f"エラー: {str(critical_result)}", 
                    "status": "error"
                }
            
            print(f"Phase 2 完了: Critical={critical_result.get('status')}")
            
            # Phase 3: PM による統合
            print("Phase 3: 統合分析開始...")
            
            integration_result = await self._run_with_timeout(
                self.pm_agent.integrate_analyses(query, research_result, creative_result, critical_result),
                Config.INTEGRATION_TIMEOUT,
                "PMAgent"
            )
            
            if isinstance(integration_result, Exception):
                integration_result = {
                    "agent": "PMAgent", 
                    "integrated_response": f"統合エラー: {str(integration_result)}", 
                    "status": "error"
                }
            
            print(f"Phase 3 完了: Integration={integration_result.get('status')}")
            
            # 処理時間計算
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "query": query,
                "processing_time": processing_time,
                "analysis_results": {
                    "research": research_result,
                    "creative": creative_result,
                    "critical": critical_result,
                    "integration": integration_result
                },
                "final_response": integration_result.get('integrated_response', '統合結果を取得できませんでした'),
                "status": "completed",
                "execution_phases": ["parallel_analysis", "critical_analysis", "integration"],
                "agents_executed": ["ResearchAgent", "CreativeAgent", "CriticalAgent", "PMAgent"],
                "arxiv_info": {
                    "used": research_result.get('arxiv_used', False),
                    "status": research_result.get('arxiv_status', 'not_executed'),
                    "storage_path": arxiv_mcp_service.storage_path if arxiv_mcp_service.is_connected else None
                }
            }
            
        except Exception as e:
            return {
                "query": query,
                "processing_time": (datetime.now() - start_time).total_seconds(),
                "final_response": f"分散処理中に予期しないエラーが発生しました: {str(e)}",
                "status": "error",
                "error": str(e),
                "agents_executed": []
            }
    
    async def _run_with_timeout(self, coro, timeout: float, agent_name: str):
        """タイムアウト付きでコルーチンを実行"""
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            raise Exception(f"{agent_name} タイムアウト ({timeout}秒)")
        except Exception as e:
            raise Exception(f"{agent_name} 実行エラー: {str(e)}")
    
    def log_evaluation_decision(self, query: str, evaluation: Dict[str, Any]):
        """エージェントの判定をログに記録"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query[:100],
            "needs_arxiv": evaluation.get('needs_arxiv', False),
            "reason": evaluation.get('reason', ''),
            "confidence": evaluation.get('confidence', 'unknown')
        }
        self.evaluation_log.append(log_entry)
        
        # 最新100件のみ保持
        if len(self.evaluation_log) > 100:
            self.evaluation_log = self.evaluation_log[-100:]

# シングルトンインスタンス
orchestrator = MultiAgentOrchestrator()