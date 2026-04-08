# agents/creative.py
from strands import Agent
from strands.models import BedrockModel
from config import Config
from services.search import search_service
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
        temperature=0.8,  # 創造性を高めるため高めの温度
        max_tokens=3000,
        streaming=False,
    )

class CreativeAgent(Agent):
    def __init__(self):
        bedrock_client = create_bedrock_client()
        model = create_bedrock_model(bedrock_client, Config.CREATIVE_MODEL)
        
        super().__init__(
            name="CreativeAgent",
            system_prompt="""あなたは創造的なアイデアを提案するエージェントです。

あなたの役割：
- 革新的なアイデアや未来のシナリオを創造する
- 既存の枠組みを超えた発想を提供する
- 可能性を広げる創造的な視点を提案する

やること：
1. 提供された情報に対して創造的な視点や未来のシナリオを提案する
2. 革新的なアイデアや解決策を具体的に提示する
3. 想像力豊かな可能性を探求し、新しい視点を提供する
4. 創造的な応用例や発展可能性を示す

回答形式：
## 創造的アイデア
[革新的なアイデアや提案]

## 未来シナリオ
[可能性のある未来の展開]

## 創造的応用例
[具体的な応用アイデア]""",
            model=model
        )
    
    async def create_ideas(self, query: str, research_context: str = "") -> Dict[str, Any]:
        """創造的アイデアを生成"""
        try:
            # 基本的な情報収集
            search_results = await search_service.search(query, max_results=5)
            formatted_results = search_service.format_search_results(search_results, max_items=3)
            
            # 創造プロンプト
            creative_prompt = f"""
以下の質問について、創造的で革新的なアイデアを提案してください。

質問: {query}

参考情報:
{formatted_results}

リサーチ結果（参考）:
{research_context[:500] if research_context else "未提供"}

既存の枠組みにとらわれず、未来志向で創造的な視点から回答してください。
具体的で実現可能性のあるアイデアを含めてください。
"""
            
            # エージェント実行
            result = self(creative_prompt)
            
            # レスポンス抽出
            response_text = ""
            if hasattr(result, 'message') and result.message:
                content = result.message.get('content', [])
                if content and isinstance(content, list) and len(content) > 0:
                    response_text = content[0].get('text', '')
            
            return {
                "agent": self.name,
                "ideas": response_text,
                "creativity_level": "high",
                "status": "success"
            }
            
        except Exception as e:
            return {
                "agent": self.name,
                "ideas": f"創造的分析中にエラーが発生しました: {str(e)}",
                "creativity_level": "error",
                "status": "error",
                "error": str(e)
            }