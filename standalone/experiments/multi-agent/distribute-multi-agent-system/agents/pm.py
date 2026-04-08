# agents/pm.py
from strands import Agent
from strands.models import BedrockModel
from config import Config
import boto3
from typing import Dict, Any

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
        temperature=0.3,
        max_tokens=4000,
        streaming=False,
    )

class PMAgent(Agent):
    def __init__(self):
        bedrock_client = create_bedrock_client()
        model = create_bedrock_model(bedrock_client, Config.PM_MODEL)
        
        super().__init__(
            name="PMAgent",
            system_prompt="""あなたはプロジェクトマネージャーエージェントです。

あなたの役割：
- 複数の専門エージェントの分析結果を統合する
- 包括的で実用的な最終回答を作成する
- 異なる観点のバランスを取りまとめる

やること：
1. リサーチ、創造的、批判的な各分析を総合的に評価する
2. 重要なポイントを整理し、優先順位を付ける
3. 実行可能で具体的なアクションプランを提示する
4. バランスの取れた最終的な結論を導く

回答形式：
## 統合分析結果
[各エージェントの分析を踏まえた総合的な見解]

## 重要ポイント
[最も重要な要素の整理]

## 推奨アクション
[具体的な実行可能な提案]

## 結論
[最終的な結論と総括]""",
            model=model
        )
    
    async def integrate_analyses(self, query: str, research_result: dict, creative_result: dict, critical_result: dict) -> Dict[str, Any]:
        """各エージェントの分析結果を統合"""
        try:
            # 統合プロンプト
            integration_prompt = f"""
以下の質問に対して、3つの専門エージェントが分析を行いました。
これらの結果を統合し、包括的で実用的な最終回答を作成してください。

質問: {query}

【リサーチエージェントの分析】
{research_result.get('analysis', '分析結果なし')}

【クリエイティブエージェントのアイデア】
{creative_result.get('ideas', 'アイデアなし')}

【批判的エージェントの分析】
{critical_result.get('critical_analysis', '分析結果なし')}

上記の3つの観点を統合し、以下を含む包括的な回答を作成してください：
1. 各分析の重要ポイントの整理
2. 異なる観点のバランスを取った見解
3. 実行可能な具体的提案
4. 総合的な結論

質問者にとって最も価値のある、実用的で行動につながる回答を心がけてください。
"""
            
            # エージェント実行
            result = self(integration_prompt)
            
            # レスポンス抽出
            response_text = ""
            if hasattr(result, 'message') and result.message:
                content = result.message.get('content', [])
                if content and isinstance(content, list) and len(content) > 0:
                    response_text = content[0].get('text', '')
            
            return {
                "agent": self.name,
                "integrated_response": response_text,
                "integration_status": "complete",
                "agents_integrated": ["ResearchAgent", "CreativeAgent", "CriticalAgent"],
                "status": "success"
            }
            
        except Exception as e:
            return {
                "agent": self.name,
                "integrated_response": f"統合分析中にエラーが発生しました: {str(e)}",
                "integration_status": "error",
                "agents_integrated": [],
                "status": "error",
                "error": str(e)
            }