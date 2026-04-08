# agents/critical.py
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
        temperature=0.2,  # 批判的思考のため低めの温度
        max_tokens=3000,
        streaming=False,
    )

class CriticalAgent(Agent):
    def __init__(self):
        bedrock_client = create_bedrock_client()
        model = create_bedrock_model(bedrock_client, Config.CRITICAL_MODEL)
        
        super().__init__(
            name="CriticalAgent",
            system_prompt="""あなたは批判的な分析を行うエージェントです。

あなたの役割：
- 客観的な視点から問題点やリスクを分析する
- 論理的な検証と批判的思考を提供する
- 潜在的な課題や制約を特定する

やること：
1. 提供された情報や提案を客観的に検証する
2. 具体的な問題点、リスク、制約を詳細に指摘する
3. 論理的な根拠に基づいた批判的分析を提供する
4. 改善点や注意すべき点を明確に示す

回答形式：
## 問題点・リスク分析
[特定された問題点やリスク]

## 制約・課題
[制約条件や解決すべき課題]

## 改善提案
[具体的な改善案や対策]""",
            model=model
        )
    
    async def analyze_critically(self, query: str, research_context: str = "", creative_context: str = "") -> Dict[str, Any]:
        """批判的分析を実行"""
        try:
            # 批判的分析プロンプト
            critical_prompt = f"""
以下の質問と他エージェントの分析結果について、批判的な観点から分析してください。

質問: {query}

リサーチ結果（参考）:
{research_context[:500] if research_context else "未提供"}

創造的アイデア（参考）:
{creative_context[:500] if creative_context else "未提供"}

上記の内容に対して：
1. 潜在的な問題点やリスクを特定してください
2. 実現性や実用性の観点から課題を分析してください
3. 見落とされがちな制約や注意点を指摘してください
4. 改善や対策が必要な点を具体的に提示してください
"""
            
            # エージェント実行
            result = self(critical_prompt)
            
            # レスポンス抽出
            response_text = ""
            if hasattr(result, 'message') and result.message:
                content = result.message.get('content', [])
                if content and isinstance(content, list) and len(content) > 0:
                    response_text = content[0].get('text', '')
            
            return {
                "agent": self.name,
                "critical_analysis": response_text,
                "analysis_depth": "detailed",
                "status": "success"
            }
            
        except Exception as e:
            return {
                "agent": self.name,
                "critical_analysis": f"批判的分析中にエラーが発生しました: {str(e)}",
                "analysis_depth": "error",
                "status": "error",
                "error": str(e)
            }