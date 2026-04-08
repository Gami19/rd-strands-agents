from strands import Agent
from strands.tools.mcp import MCPClient
from typing import Dict, Any

class AnalysisAgent:
    """分析エージェントの実装"""
    
    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client
        self.tools = mcp_client.list_tools_sync()
        
        self.agent = Agent(
            tools=self.tools,
            system_prompt="""あなたは分析エージェントです。
            リサーチエージェントから提供された情報を分析し、以下の観点から評価してください：
            
            分析の観点：
            1. 信頼性と正確性の評価
            2. 関連性と重要性の分析
            3. トレンドとパターンの特定
            4. 機会とリスクの評価
            5. 競合状況の分析
            
            分析結果は以下の形式で提供してください：
            - 主要な洞察
            - データの信頼性評価
            - トレンド分析
            - リスク評価
            - 推奨事項
            
            分析は客観的で、データに基づいた内容にしてください。"""
        )
    
    def analyze(self, research_data: str) -> Dict[str, Any]:
        """分析クエリの実行"""
        try:
            analysis_query = f"""
            以下のリサーチデータを分析してください：
            
            {research_data}
            
            上記の情報を包括的に分析し、ビジネス意思決定に有用な洞察を提供してください。
            """
            
            response = self.agent(analysis_query)
            return {
                "status": "success",
                "analysis": str(response),
                "insights": self._extract_insights(str(response)),
                "recommendations": self._extract_recommendations(str(response))
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _extract_insights(self, analysis: str) -> list:
        """分析結果から洞察を抽出"""
        insights = []
        lines = analysis.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['洞察', '発見', '重要な', '注目すべき']):
                insights.append(line.strip())
        return insights
    
    def _extract_recommendations(self, analysis: str) -> list:
        """分析結果から推奨事項を抽出"""
        recommendations = []
        lines = analysis.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['推奨', '提案', 'すべき', '検討']):
                recommendations.append(line.strip())
        return recommendations