import boto3
import asyncio
from typing import List, Dict, Any
from config import Config

class AISearchService:
    def __init__(self):
        self.bedrock_agent = boto3.client(
            'bedrock-agent-runtime',
            region_name=Config.AWS_REGION,
            aws_access_key_id=Config.AWS_ACCESS_KEY,
            aws_secret_access_key=Config.AWS_SECRET_KEY
        )
    
    async def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Knowledge Base検索"""
        if not Config.BEDROCK_KNOWLEDGE_BASE_ID:
            return []
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self._search_sync,
                query,
                max_results
            )
            return response.get('retrievalResults', [])
        except Exception as e:
            print(f"⛔AI Search error: {e}")
            return []
    
    def _search_sync(self, query: str, max_results: int):
        return self.bedrock_agent.retrieve(
            knowledgeBaseId=Config.BEDROCK_KNOWLEDGE_BASE_ID,
            retrievalQuery={'text': query},
            retrievalConfiguration={
                'vectorSearchConfiguration': {'numberOfResults': max_results}
            }
        )
    
    def format_search_results(self, results: List[Dict[str, Any]], max_items: int = 5) -> str:
        """検索結果をフォーマット"""
        if not results:
            return "関連する情報が見つかりませんでした。"
        
        formatted = []
        for i, result in enumerate(results[:max_items], 1):
            content = result.get('content', {}).get('text', '')
            score = result.get('score', 0)
            formatted.append(f"{i}. [関連度: {score:.2f}] {content[:400]}...")
        
        return "\n".join(formatted)

# シングルトンインスタンス
search_service = AISearchService()