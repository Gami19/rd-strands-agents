from strands import Agent
from strands.models import BedrockModel
from config import Config
from typing import Dict, Any, List
from services.search import search_service
from services.arxiv_mcp_service import arxiv_mcp_service
import boto3
import json
import re

def create_bedrock_client():
    return boto3.client(
        service_name='bedrock-runtime',
        region_name=Config.AWS_REGION,
        aws_access_key_id=Config.AWS_ACCESS_KEY,
        aws_secret_access_key=Config.AWS_SECRET_KEY,
    )

def create_bedrock_model(client, model_id):
    return BedrockModel(
        model_id=model_id,
        client=client,
        temperature=Config.AGENT_EVALUATION_TEMPERATURE,
        max_tokens=3000,
        streaming=False,
    )

class ResearchAgent(Agent):
    def __init__(self):
        bedrock_client = create_bedrock_client()
        model = create_bedrock_model(bedrock_client, Config.RESEARCH_MODEL)
        
        super().__init__(
            name="ResearchAgent",
            system_prompt="""あなたはリサーチ専門のエージェントです。

あなたの役割：
- データ、統計、事実に基づいた客観的な分析を行う
- 検索結果の質と十分性を自律的に評価する
- 必要に応じてarXiv論文検索の実行を判断する

重要な責任：
1. Knowledge Base検索結果を評価し、質問に対して十分な情報が得られているかを判断
2. 不十分な場合は、arXiv論文検索が必要かどうかを決定
3. 学術的・技術的な質問には最新の研究動向を含める
4. 客観的で信頼性の高い分析を提供する""",
            model=model
        )
    
    async def analyze(self, query: str) -> Dict[str, Any]:
        """リサーチ分析を実行（エージェント主導判定版）"""
        try:
            print(f"ResearchAgent: 分析開始 - {query}")
            
            # 1. Knowledge Base検索
            search_results = await search_service.search(query, max_results=8)
            formatted_results = search_service.format_search_results(search_results)
            
            print(f"ResearchAgent: KB検索完了 - {len(search_results)}件の結果")
            
            # 2. エージェント自身による検索結果の十分性判定
            evaluation_decision = await self._evaluate_search_sufficiency(
                query, formatted_results, len(search_results)
            )
            
            print(f"ResearchAgent: 十分性判定完了 - アーカイブ検索必要: {evaluation_decision.get('needs_arxiv', False)}")
            
            arxiv_data = {}
            # 3. エージェントがarXiv検索が必要と判断した場合
            if evaluation_decision.get('needs_arxiv', False) and arxiv_mcp_service.is_connected:
                print(f"ResearchAgent: arXiv検索実行中...")
                arxiv_query = evaluation_decision.get('arxiv_query', query)
                arxiv_data = arxiv_mcp_service.search_and_analyze_papers(query, arxiv_query)
                print(f"ResearchAgent: arXiv検索完了 - ステータス: {arxiv_data.get('status', 'unknown')}")
            elif evaluation_decision.get('needs_arxiv', False) and not arxiv_mcp_service.is_connected:
                print("⛔ResearchAgent: arXiv検索が必要だが、MCPサーバーに接続されていません")
            
            # 4. 最終分析の実行
            final_result = await self._create_final_analysis(
                query, search_results, arxiv_data, evaluation_decision
            )
            
            print(f"ResearchAgent: 分析完了")
            return final_result
            
        except Exception as e:
            error_msg = f"⛔ResearchAgent分析エラー: {str(e)}"
            print(error_msg)
            return {
                "agent": self.name,
                "analysis": error_msg,
                "status": "error",
                "error": str(e)
            }
    
    async def _evaluate_search_sufficiency(self, query: str, formatted_results: str, result_count: int) -> Dict[str, Any]:
        """エージェント自身が検索結果の十分性を判定"""
        
        evaluation_prompt = f"""
以下の質問に対する検索結果を評価してください。

質問: {query}
検索結果数: {result_count}件

検索結果内容:
{formatted_results}

あなたの評価タスク:
1. この検索結果は質問に対して十分な情報を提供していますか？
2. より深い学術的・技術的な情報が必要ですか？
3. 最新の研究論文からの情報が質問者にとって価値があると思いますか？

以下のJSON形式で回答してください:
{{
    "needs_arxiv": true/false,
    "reason": "判定理由を詳細に説明",
    "arxiv_query": "arXiv検索が必要な場合の最適化された検索クエリ（必要な場合のみ）",
    "confidence": "判定への自信度（high/medium/low）"
}}

判定基準:
- 検索結果が少ない（3件未満）、または関連性が低い場合
- 質問が学術的・技術的で、より専門的な情報が必要な場合
- 最新の研究動向や手法について詳しい情報が質問者に価値をもたらす場合
- 現在の検索結果では質問者に十分価値のある回答ができない場合

慎重に判断し、本当に質問者のためになる場合のみarXiv検索を推奨してください。
"""
        
        try:
            # エージェント自身で判定
            result = self(evaluation_prompt)
            
            # レスポンス抽出
            response_text = ""
            if hasattr(result, 'message') and result.message:
                content = result.message.get('content', [])
                if content and isinstance(content, list) and len(content) > 0:
                    response_text = content[0].get('text', '')
            
            # JSON解析を試行
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                evaluation_result = json.loads(json_match.group())
                
                # 必要なフィールドの検証
                if 'needs_arxiv' not in evaluation_result:
                    evaluation_result['needs_arxiv'] = False
                if 'reason' not in evaluation_result:
                    evaluation_result['reason'] = "判定理由が取得できませんでした"
                if 'confidence' not in evaluation_result:
                    evaluation_result['confidence'] = "medium"
                
                return evaluation_result
            else:
                # JSONが見つからない場合の処理
                return {
                    "needs_arxiv": result_count < 2,  # 基本的な数値判定
                    "reason": "JSON解析失敗のため、基本判定を適用",
                    "confidence": "low"
                }
                
        except Exception as e:
            print(f"検索十分性評価エラー: {e}")
            # エラー時のフォールバック判定
            return {
                "needs_arxiv": result_count < 2,
                "reason": f"評価エラーのため基本判定を適用: {str(e)}",
                "confidence": "low"
            }
    
    async def _create_final_analysis(self, query: str, kb_results: List, arxiv_data: Dict, evaluation: Dict) -> Dict[str, Any]:
        """最終的なリサーチ分析を作成"""
        
        # KB結果のフォーマット
        kb_formatted = search_service.format_search_results(kb_results)
        
        # arXiv結果のフォーマット
        arxiv_info = ""
        arxiv_used = False
        if arxiv_data.get('status') == 'success':
            arxiv_info = f"""

【arXiv論文検索結果】
検索クエリ: {arxiv_data.get('search_query', 'N/A')}
結果: {arxiv_data.get('response', 'レスポンスなし')}
ストレージパス: {arxiv_data.get('storage_path', 'N/A')}
"""
            arxiv_used = True
        elif arxiv_data.get('error'):
            arxiv_info = f"""

【arXiv論文検索エラー】
エラー: {arxiv_data.get('error')}
"""
        
        # 最終分析プロンプト
        final_analysis_prompt = f"""
質問: {query}

【検索結果評価】
arXiv検索実行: {"はい" if evaluation.get('needs_arxiv', False) else "いいえ"}
判定理由: {evaluation.get('reason', '')}
判定信頼度: {evaluation.get('confidence', 'medium')}

【Knowledge Base検索結果】
{kb_formatted}

{arxiv_info}

上記の情報を統合し、以下の形式で包括的なリサーチ分析を提供してください:

## リサーチ結果
[客観的な分析内容]

## 主要データ・統計
[数値データや統計情報]

## 学術的根拠
[論文やエビデンスに基づく情報（arXiv論文を含む）]

## 情報源・根拠
[参考となる情報源や根拠]

## 情報の信頼性評価
[使用した情報源の信頼性と制約について]
"""
        
        # 最終分析実行
        result = self(final_analysis_prompt)
        
        # レスポンス抽出
        response_text = ""
        if hasattr(result, 'message') and result.message:
            content = result.message.get('content', [])
            if content and isinstance(content, list) and len(content) > 0:
                response_text = content[0].get('text', '')
        
        return {
            "agent": self.name,
            "analysis": response_text,
            "search_evaluation": evaluation,
            "kb_results_count": len(kb_results),
            "arxiv_used": arxiv_used,
            "arxiv_status": arxiv_data.get('status', 'not_executed'),
            "status": "success"
        }