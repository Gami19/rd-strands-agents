# agents/workflow_coordinator.py
from strands import Agent
from strands.models import BedrockModel
from strands.multiagent import Swarm, GraphBuilder
from config import Config
import boto3
import logging

logger = logging.getLogger(__name__)

def create_bedrock_client():
    return boto3.client(
        service_name='bedrock-runtime',
        region_name=Config.AWS_REGION,
        aws_access_key_id=Config.AWS_ACCESS_KEY,
        aws_secret_access_key=Config.AWS_SECRET_KEY,
    )

def create_bedrock_model(client, model_id: str = None):
    if not model_id:
        model_id = Config.EXPERT_MODEL
    
    return BedrockModel(
        model_id=model_id,
        client=client,
        temperature=0.1,
        max_tokens=4096,
        streaming=False,
    )

class WorkflowCoordinator(Agent):
    def __init__(self):
        bedrock_client = create_bedrock_client()
        model = create_bedrock_model(bedrock_client)
        
        super().__init__(
            name="WorkflowCoordinator",
            system_prompt="""あなたはワークフローコーディネーターです。
            複雑なタスクを分析し、最適なワークフローパターン（Swarm、Graph、Sequential）を選択して実行してください。
            
            選択基準:
            - Swarm: 協調的な問題解決、複数の専門家の意見が必要
            - Graph: 構造化されたワークフロー、明確な依存関係
            - Sequential: シンプルな順次処理
            
            常に最適なパターンを選択し、効率的にタスクを完了させてください。""",
            model=model
        )
    
    async def coordinate_workflow(self, query: str) -> dict:
        """クエリを分析し、最適なワークフローを実行"""
        try:
            # ワークフロー選択の分析
            workflow_analysis = self(f"""
            以下のクエリに対して最適なワークフローパターンを分析してください：
            
            クエリ: {query}
            
            分析結果は以下の形式で回答してください：
            WORKFLOW_TYPE: [SWARM/GRAPH/SEQUENTIAL]
            REASONING: [選択理由]
            COMPLEXITY: [HIGH/MEDIUM/LOW]
            """)
            
            # 分析結果の解析
            analysis_text = ""
            if hasattr(workflow_analysis, 'message') and workflow_analysis.message:
                content = workflow_analysis.message.get('content', [])
                if content and isinstance(content, list) and len(content) > 0:
                    analysis_text = content[0].get('text', '')
            
            # ワークフロータイプの決定
            workflow_type = "SEQUENTIAL"  # デフォルト
            reasoning = "Default selection"
            complexity = "MEDIUM"
            
            lines = analysis_text.split('\n')
            for line in lines:
                if line.startswith('WORKFLOW_TYPE:'):
                    workflow_type = line.split(':', 1)[1].strip()
                elif line.startswith('REASONING:'):
                    reasoning = line.split(':', 1)[1].strip()
                elif line.startswith('COMPLEXITY:'):
                    complexity = line.split(':', 1)[1].strip()
            
            # ワークフローの実行
            if workflow_type == "SWARM":
                result = await self._execute_swarm_workflow(query)
            elif workflow_type == "GRAPH":
                result = await self._execute_graph_workflow(query)
            else:  # SEQUENTIAL
                result = await self._execute_sequential_workflow(query)
            
            return {
                "response": result.get("response", "ワークフロー実行完了"),
                "workflow_type": workflow_type,
                "reasoning": reasoning,
                "complexity": complexity,
                "metadata": {
                    "execution_time": result.get("execution_time", 0),
                    "agents_involved": result.get("agents_involved", []),
                    "success": result.get("success", True)
                }
            }
            
        except Exception as e:
            logger.error(f"Workflow coordination error: {e}")
            return {
                "response": f"ワークフロー実行中にエラーが発生しました: {str(e)}",
                "workflow_type": "ERROR",
                "reasoning": "エラーが発生したためデフォルト処理",
                "complexity": "UNKNOWN",
                "metadata": {"success": False, "error": str(e)}
            }
    
    async def _execute_swarm_workflow(self, query: str) -> dict:
        """Swarmワークフローの実行"""
        try:
            bedrock_client = create_bedrock_client()
            model = create_bedrock_model(bedrock_client)
            
            # Swarm用のエージェント作成
            swarm_agents = [
                Agent(
                    name="ResearchAgent",
                    system_prompt="あなたは研究専門家です。与えられたトピックについて詳細な調査を行ってください。",
                    model=model
                ),
                Agent(
                    name="AnalysisAgent",
                    system_prompt="あなたは分析専門家です。研究データを分析し、洞察を抽出してください。",
                    model=model
                ),
                Agent(
                    name="SynthesisAgent",
                    system_prompt="あなたは統合専門家です。複数の分析結果を統合し、包括的な結論を導き出してください。",
                    model=model
                )
            ]
            
            # Swarmの実行
            swarm = Swarm(
                swarm_agents,
                max_handoffs=3,
                max_iterations=5,
                execution_timeout=300.0,
                node_timeout=60.0
            )
            
            result = swarm(query)
            
            # 結果の統合
            final_response = ""
            agents_involved = []
            
            for agent_name, node_result in result.results.items():
                if node_result and node_result.result and node_result.result.message:
                    content = node_result.result.message.get('content', [])
                    if content and isinstance(content, list) and len(content) > 0:
                        final_response += f"\n\n{agent_name}の分析:\n{content[0].get('text', '')}"
                        agents_involved.append(agent_name)
            
            return {
                "response": final_response.strip(),
                "execution_time": result.execution_time,
                "agents_involved": agents_involved,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Swarm workflow error: {e}")
            return {
                "response": f"Swarmワークフロー実行エラー: {str(e)}",
                "success": False,
                "error": str(e)
            }
    
    async def _execute_graph_workflow(self, query: str) -> dict:
        """Graphワークフローの実行"""
        try:
            bedrock_client = create_bedrock_client()
            model = create_bedrock_model(bedrock_client)
            
            # Graph用のエージェント作成
            research_agent = Agent(
                name="researcher",
                system_prompt="あなたは研究専門家です。与えられたトピックについて詳細な調査を行ってください。",
                model=model
            )
            
            analysis_agent = Agent(
                name="analyst",
                system_prompt="あなたは分析専門家です。研究データを分析し、洞察を抽出してください。",
                model=model
            )
            
            report_agent = Agent(
                name="reporter",
                system_prompt="あなたはレポート作成専門家です。分析結果を基に分かりやすいレポートを作成してください。",
                model=model
            )
            
            # グラフの構築
            builder = GraphBuilder()
            builder.add_node(research_agent, "research")
            builder.add_node(analysis_agent, "analysis")
            builder.add_node(report_agent, "report")
            
            builder.add_edge("research", "analysis")
            builder.add_edge("analysis", "report")
            
            # グラフの実行
            graph = builder.build()
            result = graph(query)
            
            # 最終結果の取得
            final_response = ""
            agents_involved = []
            
            if "report" in result.results:
                report_result = result.results["report"]
                if report_result and report_result.result and report_result.result.message:
                    content = report_result.result.message.get('content', [])
                    if content and isinstance(content, list) and len(content) > 0:
                        final_response = content[0].get('text', '')
            
            # 実行順序の取得
            for node in result.execution_order:
                agents_involved.append(node.node_id)
            
            return {
                "response": final_response,
                "execution_time": result.execution_time,
                "agents_involved": agents_involved,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Graph workflow error: {e}")
            return {
                "response": f"Graphワークフロー実行エラー: {str(e)}",
                "success": False,
                "error": str(e)
            }
    
    async def _execute_sequential_workflow(self, query: str) -> dict:
        """Sequentialワークフローの実行"""
        try:
            bedrock_client = create_bedrock_client()
            model = create_bedrock_model(bedrock_client)
            
            # Sequential用のエージェント作成
            research_agent = Agent(
                name="researcher",
                system_prompt="あなたは研究専門家です。与えられたトピックについて詳細な調査を行ってください。",
                model=model
            )
            
            analysis_agent = Agent(
                name="analyst",
                system_prompt="あなたは分析専門家です。研究データを分析し、洞察を抽出してください。",
                model=model
            )
            
            # 順次実行
            research_result = research_agent(query)
            research_text = ""
            if hasattr(research_result, 'message') and research_result.message:
                content = research_result.message.get('content', [])
                if content and isinstance(content, list) and len(content) > 0:
                    research_text = content[0].get('text', '')
            
            analysis_query = f"以下の研究結果を分析してください：\n\n{research_text}"
            analysis_result = analysis_agent(analysis_query)
            
            analysis_text = ""
            if hasattr(analysis_result, 'message') and analysis_result.message:
                content = analysis_result.message.get('content', [])
                if content and isinstance(content, list) and len(content) > 0:
                    analysis_text = content[0].get('text', '')
            
            final_response = f"研究結果:\n{research_text}\n\n分析結果:\n{analysis_text}"
            
            return {
                "response": final_response,
                "execution_time": 0,  # 簡易実装のため
                "agents_involved": ["researcher", "analyst"],
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Sequential workflow error: {e}")
            return {
                "response": f"Sequentialワークフロー実行エラー: {str(e)}",
                "success": False,
                "error": str(e)
            }


