from strands import Agent
from strands.tools.mcp import MCPClient
from typing import Dict, Any

class ReportAgent:
    """レポートエージェントの実装"""
    
    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client
        self.tools = mcp_client.list_tools_sync()
        
        self.agent = Agent(
            tools=self.tools,
            system_prompt="""あなたはレポートエージェントです。
            リサーチエージェントと分析エージェントからの情報を統合し、以下の要素を含む包括的なレポートを作成してください：
            
            レポート構成：
            1. エグゼクティブサマリー（要約）
            2. 背景と目的
            3. 主要な発見事項
            4. 詳細分析結果
            5. 推奨事項
            6. アクションプラン
            7. リスクと課題
            8. 結論
            
            レポートは以下の特徴を持つようにしてください：
            - 明確で理解しやすい
            - 実用的で実行可能
            - データに基づいた内容
            - ビジネス価値の明確化
            
            必要に応じて、図表やダイアグラムの提案も含めてください。"""
        )
    
    def generate_report(self, research_data: str, analysis_data: str) -> Dict[str, Any]:
        """レポート生成の実行"""
        try:
            report_query = f"""
            以下の情報を統合して、包括的なレポートを作成してください：
            
            === リサーチデータ ===
            {research_data}
            
            === 分析データ ===
            {analysis_data}
            
            上記の情報を基に、ビジネス意思決定者向けの包括的なレポートを作成してください。
            レポートは構造化され、実用的な推奨事項を含むものにしてください。
            """
            
            response = self.agent(report_query)
            return {
                "status": "success",
                "report": str(response),
                "summary": self._extract_summary(str(response)),
                "recommendations": self._extract_report_recommendations(str(response))
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _extract_summary(self, report: str) -> str:
        """レポートからサマリーを抽出"""
        lines = report.split('\n')
        summary_lines = []
        in_summary = False
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['サマリー', '要約', 'executive summary']):
                in_summary = True
            elif in_summary and line.strip().startswith('#'):
                break
            elif in_summary:
                summary_lines.append(line.strip())
        
        return '\n'.join(summary_lines) if summary_lines else "サマリーが見つかりませんでした"
    
    def _extract_report_recommendations(self, report: str) -> list:
        """レポートから推奨事項を抽出"""
        recommendations = []
        lines = report.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['推奨', '提案', 'アクション', '実施']):
                recommendations.append(line.strip())
        return recommendations