import sys
import boto3
from config import config, Config

# 専門ツールをインポート
from agents.search_tools import smart_search, find_related_laws, search_by_article_advanced
from agents.analysis_tools import explain_article, summarize_law, analyze_law_structure  
from agents.legal_tools import check_applicability, find_penalties, find_procedures, assess_legal_risk

# Strands Agents のインポート
try:
    from strands import Agent
    from strands.models import BedrockModel
    STRANDS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Strands Agentsライブラリが見つかりません: {e}")
    STRANDS_AVAILABLE = False

def setup_agent():
    """法令検索エージェントのセットアップ"""
    
    if not Config.validate():
        sys.exit(1)
    
    if config.DEBUG:
        Config.print_config()
    
    if not STRANDS_AVAILABLE:
        print("❌ Strands Agentsが利用できないため終了します")
        sys.exit(1)
    
    try:
        session = boto3.Session(
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
            region_name=config.AWS_DEFAULT_REGION
        )
        
        bedrock_model = BedrockModel(
            model_id=config.BEDROCK_MODEL_ID,
            boto_session=session
        )
        
        # 全ての専門ツールを統合
        all_tools = [
            # 🔍 検索系ツール
            smart_search, find_related_laws, search_by_article_advanced,
            # 📖 解析系ツール
            explain_article, summarize_law, analyze_law_structure,
            # 💼 法務系ツール
            check_applicability, find_penalties, find_procedures, assess_legal_risk
        ]
        
        agent = Agent(
            model=bedrock_model,
            tools=all_tools,
            system_prompt="""あなたは3つの専門性を持つ法令AIアシスタントです：

🔍 【検索専門家として】
- smart_search: 賢い法令検索（キーワード最適化付き）
- find_related_laws: 関連法令の自動発見
- search_by_article_advanced: 高度な条文パターン検索

📖 【解析専門家として】  
- explain_article: 条文をわかりやすく解説
- summarize_law: 法令の要点まとめ
- analyze_law_structure: 法令構造の詳細分析

💼 【法務専門家として】
- check_applicability: 状況に適用される法令の判定
- find_penalties: 罰則・制裁措置の検索
- find_procedures: 手続き・届出要件の検索
- assess_legal_risk: 法的リスクの評価

**対応方針**:
1. 質問内容に応じて、適切な専門ツールを選択
2. 複数のツールを組み合わせて包括的な回答を提供
3. 実務的で具体的なアドバイスを心がける
4. 必要に応じて専門家への相談を推奨

質問例：
- 検索系: "民法について", "第*条 目的"
- 解析系: "第1条を詳しく", "デジタル庁設置法の要点"  
- 法務系: "違反したらどうなる?", "この状況で適用される法律は?"
"""
        )
        
        print("✅ 専門ツール統合型法令検索エージェントの初期化完了")
        return agent
        
    except Exception as e:
        print(f"❌ エージェント初期化エラー: {e}")
        sys.exit(1)

def show_usage_examples():
    """使用例を表示"""
    print("""
🔍 検索例:
• '民法について' → 基本的な検索
• '第*条 目的' → ワイルドカード検索
• 'デジタル庁 AND 設置' → 複合検索

📖 解析例:  
• '民法第1条を詳しく' → 条文解説
• 'デジタル庁設置法の要点' → 法令要約
• '法令の構造を分析' → 構造分析

💼 実務例:
• 'この場合どの法律が適用？' → 適用判定  
• '違反したらどうなる？' → 罰則確認
• 'どんな手続きが必要？' → 手続き検索
• '法的リスクは？' → リスク評価
    """)

def main():
    """メインの対話ループ"""
    print("=" * 60)
    print("🏛️  法令検索AIアシスタント（専門ツール統合版）")
    print("=" * 60)
    
    agent = setup_agent()
    show_usage_examples()
    
    print("=" * 60)
    
    while True:
        try:
            user_input = input("\n🔍 質問を入力してください: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '終了', 'q']:
                print("\n👋 法令検索を終了します。お疲れさまでした！")
                break
            
            if not user_input:
                print("❓ 質問を入力してください。")
                continue
            
            print(f"\n🔄 '{user_input}' を処理中...")
            print("-" * 50)
            
            response = agent(user_input)
            
            print(f"\n📋 回答:")
            print("-" * 50)
            print(response)
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\n\n👋 検索を中断しました。")
            break
            
        except Exception as e:
            print(f"\n❌ エラーが発生しました: {e}")
            print("💡 ヒント: 質問を変更するか、再度お試しください。")

if __name__ == "__main__":
    main()