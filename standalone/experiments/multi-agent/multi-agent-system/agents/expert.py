# agents/expert.py
from strands import Agent
from strands.models import BedrockModel
from config import Config
from services.search import AISearchService
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
        max_tokens=4000,
        streaming=False,
    )

class ExpertAgent(Agent):
    def __init__(self):
        bedrock_client = create_bedrock_client()
        model = create_bedrock_model(bedrock_client, Config.EXPERT_MODEL)
        
        super().__init__(
            name="ExpertAgent",
            system_prompt="""あなたは専門家エージェントです。複雑で専門的な質問に対して、検索結果と専門知識を組み合わせて詳細な回答を提供してください。

回答のガイドライン:
- 専門的かつ正確な情報を提供してください
- 複数の観点から分析してください
- 根拠や理由を明確に示してください
- 必要に応じて具体例を提供してください
- 不確実な部分があれば明記してください""",
            model=model
        )
        self.search_service = AISearchService()
    
    async def process_with_search(self, query: str) -> dict:
        """検索結果を含めて処理"""
        try:
            # より詳細な検索を実行
            search_results = await self.search_service.search(query, max_results=8)
            formatted_results = self._format_search_results(search_results)
            
            # 検索結果を含めたプロンプト
            expert_prompt = f"""
検索結果:
{formatted_results}

ユーザーの質問: {query}

上記の検索結果と専門知識を組み合わせて、詳細で専門的な回答を提供してください。
"""
            
            # エージェントを実行
            result = self(expert_prompt)
            
            # レスポンス抽出
            response_text = ""
            if hasattr(result, 'message') and result.message:
                content = result.message.get('content', [])
                if content and isinstance(content, list) and len(content) > 0:
                    response_text = content[0].get('text', '')
            
            return {
                "agent": self.name,
                "response": response_text,
                "analysis_depth": "expert",
                "search_count": len(search_results)
            }
            
        except Exception as e:
            return {
                "agent": self.name,
                "response": f"申し訳ございません。専門的な分析中にエラーが発生しました: {str(e)}",
                "analysis_depth": "expert",
                "search_count": 0
            }
    
    def _format_search_results(self, results):
        if not results:
            return "関連する専門情報が見つかりませんでした。"
        
        formatted = []
        for i, result in enumerate(results, 1):
            content = result.get('content', {}).get('text', '')
            score = result.get('score', 0)
            formatted.append(f"{i}. [信頼度: {score:.2f}] {content}")
        
        return "\n".join(formatted)