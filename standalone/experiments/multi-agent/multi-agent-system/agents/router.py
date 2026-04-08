# agents/router.py
from strands import Agent
from strands.models import BedrockModel
from config import Config
import boto3

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
        temperature=0.1,
        max_tokens=2048,
        streaming=False,
    )

class RouterAgent(Agent):
    def __init__(self):
        bedrock_client = create_bedrock_client()
        model = create_bedrock_model(bedrock_client, Config.ROUTER_MODEL)
        
        super().__init__(
            name="RouterAgent",
            system_prompt="""あなたはルーティングエージェントです。ユーザーの質問を分析し、適切なエージェントに振り分けてください。

振り分け基準:
- FAQ: よくある質問、基本的な情報、製品・サービスに関する一般的な質問（ナレコムAI Chatbotなど）
- EXPERT: 専門的な技術質問、詳細な分析が必要な質問、複雑な問題解決
- GENERAL: 雑談、挨拶、天気の話など一般的な会話

回答は以下の形式で:
AGENT_TYPE: [FAQ/EXPERT/GENERAL]
REASONING: [振り分けの理由]""",
            model=model
        )
    
    def route_query(self, query: str) -> dict:
        """クエリをルーティングして適切なエージェント情報を返す"""
        try:
            # エージェントを実行してルーティング判定を取得
            result = self(query)
            
            # 結果からエージェントタイプを抽出
            response_text = ""
            if hasattr(result, 'message') and result.message:
                content = result.message.get('content', [])
                if content and isinstance(content, list) and len(content) > 0:
                    response_text = content[0].get('text', '')
            
            # レスポンスを解析
            agent_type = "GENERAL"  # デフォルト
            reasoning = "Default routing"
            
            lines = response_text.split('\n')
            for line in lines:
                if line.startswith('AGENT_TYPE:'):
                    agent_type = line.split(':', 1)[1].strip()
                elif line.startswith('REASONING:'):
                    reasoning = line.split(':', 1)[1].strip()
            
            return {
                "agent_type": agent_type,
                "reasoning": reasoning,
                "original_query": query
            }
            
        except Exception as e:
            print(f"Routing error: {e}")
            return {
                "agent_type": "GENERAL",
                "reasoning": f"エラーのためGENERALに振り分け: {str(e)}",
                "original_query": query
            }