from strands import Agent
from strands_tools import http_request
import asyncio
import os
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# システムプロンプト
SYSTEM_PROMPT = """あなたはHTTPリクエストを通じてWeb APIと対話できるAIアシスタントです。

利用可能なツール:
- http_request: HTTPリクエストを送信してWeb APIからデータを取得

HTTPリクエストの使用方法:
- GET: データの取得
- POST: データの作成・送信
- PUT: データの更新
- DELETE: データの削除

レスポンス形式:
- status_code: HTTPステータスコード
- headers: レスポンスヘッダー
- content: レスポンスボディ
- is_error: エラーが発生したかどうか

適切なHTTPメソッドとURLを使用して、ユーザーの要求を満たしてください。"""

# エージェントの作成
agent = Agent(
    tools=[http_request],
    system_prompt=SYSTEM_PROMPT
)

async def main():
    """メイン関数"""
    print("=== HTTP Request Tool サンプル ===\n")
    
    print(" 天気予報 API（https://weather.tsukumijima.net/api/forecast/ID）から天気情報を取得")
    query3 = "熊本の現在の天気情報を取得してください（https://weather.tsukumijima.net/primary_area.xmlからIDを取得してください）"
    
    try:
        async for event in agent.stream_async(query3):
            if "data" in event:
                chunk = event["data"]
                print(chunk, end="")
    except Exception as e:
        print(f"エラー: {e}")

# 直接実行用のテスト関数
def test_http_request():
    """HTTPリクエストツールの直接テスト"""
    print("=== 直接ツールテスト ===")
    
    # ツールを直接呼び出し
    result = agent.tool.http_request(
        method="GET",
        url="https://jsonplaceholder.typicode.com/posts/1"
    )
    
    print(f"直接呼び出し結果: {result}")

if __name__ == "__main__":
    # 非同期実行
    asyncio.run(main())
    
    # 直接テストも実行
    print("\n")
    test_http_request()