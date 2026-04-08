# agents/faq.py
from strands import Agent
from strands.models import BedrockModel
from config import Config
from services.search import AISearchService
import boto3
import asyncio

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
        max_tokens=3000,
        streaming=False,
    )

class FAQAgent(Agent):
    def __init__(self):
        bedrock_client = create_bedrock_client()
        model = create_bedrock_model(bedrock_client, Config.FAQ_MODEL)
        
        super().__init__(
            name="FAQAgent",
            system_prompt="""あなたはFAQエージェントです。検索結果を基に、よくある質問に対して正確で分かりやすい回答をしてください。

回答のガイドライン:
- 検索結果に基づいて回答してください
- 分かりやすく簡潔に説明してください
- 関連する追加情報があれば提供してください
- 検索結果に答えがない場合は、その旨を伝えてください""",
            model=model
        )
        self.search_service = AISearchService()
    
    async def process_with_search(self, query: str) -> dict:
        """検索結果を含めて処理"""
        try:
            # Knowledge Base検索
            search_results = await self.search_service.search(query)
            formatted_results = self._format_search_results(search_results)
            
            # 検索結果を含めたプロンプト
            search_prompt = f"""
検索結果:
{formatted_results}

ユーザーの質問: {query}

上記の検索結果を参考に回答してください。
"""
            
            # エージェントを実行
            result = self(search_prompt)
            
            # レスポンス抽出
            response_text = ""
            if hasattr(result, 'message') and result.message:
                content = result.message.get('content', [])
                if content and isinstance(content, list) and len(content) > 0:
                    response_text = content[0].get('text', '')
            
            return {
                "agent": self.name,
                "response": response_text,
                "has_search_results": len(search_results) > 0,
                "search_count": len(search_results)
            }
            
        except Exception as e:
            return {
                "agent": self.name,
                "response": f"申し訳ございません。処理中にエラーが発生しました: {str(e)}",
                "has_search_results": False,
                "search_count": 0
            }
    
    def _format_search_results(self, results):
        if not results:
            return "関連する情報が見つかりませんでした。"
        
        formatted = []
        for i, result in enumerate(results[:3], 1):
            content = result.get('content', {}).get('text', '')
            score = result.get('score', 0)
            formatted.append(f"{i}. [関連度: {score:.2f}] {content[:300]}...")
        
        return "\n".join(formatted)