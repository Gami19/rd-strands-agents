# agents/general.py
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
        temperature=0.7,
        max_tokens=2000,
        streaming=False,
    )

class GeneralAgent(Agent):
    def __init__(self):
        bedrock_client = create_bedrock_client()
        model = create_bedrock_model(bedrock_client, Config.GENERAL_MODEL)
        
        super().__init__(
            name="GeneralAgent",
            system_prompt="""あなたは一般的な会話を担当するエージェントです。フレンドリーで親しみやすい対応を心がけてください。

ユーザーとの自然な会話を楽しみ、必要に応じて有用な情報も提供してください。
雑談、挨拶、日常的な話題などに対応します。""",
            model=model
        )
    
    def process_general(self, query: str) -> dict:
        """一般的な会話を処理"""
        try:
            # エージェントを実行
            result = self(query)
            
            # レスポンス抽出
            response_text = ""
            if hasattr(result, 'message') and result.message:
                content = result.message.get('content', [])
                if content and isinstance(content, list) and len(content) > 0:
                    response_text = content[0].get('text', '')
            
            return {
                "agent": self.name,
                "response": response_text,
                "type": "general_conversation"
            }
            
        except Exception as e:
            return {
                "agent": self.name,
                "response": f"申し訳ございません。会話処理中にエラーが発生しました: {str(e)}",
                "type": "general_conversation"
            }