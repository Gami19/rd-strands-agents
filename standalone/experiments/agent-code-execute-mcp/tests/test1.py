import asyncio
import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.tools.mcp import MCPClient
from config import create_bedrock_model

async def test_mcp_connection():
    """MCPサーバ接続テスト"""
    print("=== MCPサーバ接続テスト ===")
    
    mcp_client = MCPClient(
        lambda: streamablehttp_client("http://localhost:8000/mcp")
    )
    
    try:
        with mcp_client:
            # 利用可能なツール確認
            tools = mcp_client.list_tools_sync()
            print(f"利用可能なツール数: {len(tools)}")
            
            for tool in tools:
                # ツールオブジェクトの属性を安全にアクセス
                tool_name = getattr(tool, 'name', str(tool))
                tool_description = getattr(tool, 'description', '説明なし')
                print(f"- {tool_name}: {tool_description}")
            
            # デバッグ用：ツールオブジェクトの詳細情報
            if tools:
                print(f"\n最初のツールオブジェクトの詳細:")
                first_tool = tools[0]
                print(f"型: {type(first_tool)}")
                print(f"属性: {dir(first_tool)}")
                print(f"文字列表現: {first_tool}")
            
            return True
    except Exception as e:
        print(f"接続エラー: {e}")
        return False

async def test_basic_tools():
    """基本ツールテスト"""
    print("\n=== 基本ツールテスト ===")
    
    mcp_client = MCPClient(
        lambda: streamablehttp_client("http://localhost:8000/mcp")
    )
    
    try:
        with mcp_client:
            # 直接ツール呼び出しテスト
            print("1. ヘルスチェック")
            result1 = await mcp_client.call_tool_async(
                tool_use_id="test-1",
                name="health_check",
                arguments={}
            )
            print(json.dumps(result1, indent=2, ensure_ascii=False))
            
            print("\n2. エコーテスト")
            result2 = await mcp_client.call_tool_async(
                tool_use_id="test-2",
                name="echo_test",
                arguments={"message": "Hello MCP!"}
            )
            print(json.dumps(result2, indent=2, ensure_ascii=False))
            
            print("\n3. 簡単な計算")
            result3 = await mcp_client.call_tool_async(
                tool_use_id="test-3",
                name="simple_calculation",
                arguments={"expression": "2 + 3 * 4"}
            )
            print(json.dumps(result3, indent=2, ensure_ascii=False))
            
            return True
    except Exception as e:
        print(f"ツールテストエラー: {e}")
        return False

async def test_agent_integration():
    """Strands Agent統合テスト"""
    print("\n=== Strands Agent統合テスト ===")
    
    mcp_client = MCPClient(
        lambda: streamablehttp_client("http://localhost:8000/mcp")
    )
    
    try:
        with mcp_client:
            tools = mcp_client.list_tools_sync()
            
            # カスタムBedrockModelでAgentを作成
            bedrock_model = create_bedrock_model()
            agent = Agent(
                model=bedrock_model,
                tools=tools
            )
            
            # または、シンプルにmodel_id文字列で指定
            # agent = Agent(
            #     model="us.anthropic.claude-3-5-sonnet-20241022-v1:0",
            #     tools=tools
            # )
            
            # テスト1: ヘルスチェック
            print("1. Agentによるヘルスチェック")
            response1 = await agent.invoke_async("サーバーのヘルスチェックを実行して")
            print(f"Response: {response1}")
            
            # テスト2: エコーテスト
            print("\n2. Agentによるエコーテスト")
            response2 = await agent.invoke_async("'Agent Test Message'をエコーして")
            print(f"Response: {response2}")
            
            # テスト3: 計算
            print("\n3. Agentによる計算")
            response3 = await agent.invoke_async("10 + 5 * 3を計算して")
            print(f"Response: {response3}")
            
            # テスト4: サンプルデータ生成
            print("\n4. サンプルデータ生成")
            response4 = await agent.invoke_async("サンプルデータを生成して基本情報を教えて")
            print(f"Response: {response4}")
            
            return True
    except Exception as e:
        print(f"Agent統合テストエラー: {e}")
        return False

async def test_different_agent_configurations():
    """異なるAgent設定のテスト"""
    print("\n=== 異なるAgent設定テスト ===")
    
    mcp_client = MCPClient(
        lambda: streamablehttp_client("http://localhost:8000/mcp")
    )
    
    try:
        with mcp_client:
            tools = mcp_client.list_tools_sync()
            
            # テスト1: デフォルトAgent
            print("1. デフォルトAgent")
            default_agent = Agent(tools=tools)
            response1 = await default_agent.invoke_async("簡単な挨拶をして")
            print(f"Default Agent Response: {response1}")
            
            # テスト2: model_id文字列指定Agent
            print("\n2. Model ID文字列指定Agent")
            string_agent = Agent(
                model="us.anthropic.claude-3-5-sonnet-20241022-v1:0",
                tools=tools
            )
            response2 = await string_agent.invoke_async("あなたのモデル情報を教えて")
            print(f"String Model Agent Response: {response2}")
            
            # テスト3: BedrockModel設定Agent
            print("\n3. BedrockModel設定Agent")
            configured_model = create_bedrock_model()
            configured_agent = Agent(
                model=configured_model,
                tools=tools
            )
            response3 = await configured_agent.invoke_async("設定されたモデルで挨拶して")
            print(f"Configured Model Agent Response: {response3}")
            
            return True
    except Exception as e:
        print(f"Agent設定テストエラー: {e}")
        return False

async def run_all_tests():
    """全テスト実行"""
    print("Phase 1 確認テストを開始します...")
    
    # AWS認証情報の確認
    if not os.getenv('AWS_ACCESS_KEY_ID') and not os.path.exists(os.path.expanduser('~/.aws/credentials')):
        print("⚠️  AWS認証情報が設定されていません。AWSプロファイルまたは環境変数を確認してください。")
    
    # AWSリージョンの確認
    region = os.getenv('AWS_DEFAULT_REGION', os.getenv('AWS_REGION', 'us-east-1'))
    print(f"使用するAWSリージョン: {region}")
    
    # MCPサーバが起動していることを確認
    connection_ok = await test_mcp_connection()
    if not connection_ok:
        print("❌ MCPサーバ接続に失敗しました。サーバが起動していることを確認してください。")
        return False
    
    # 基本ツールテスト
    basic_tools_ok = await test_basic_tools()
    if not basic_tools_ok:
        print("❌ 基本ツールテストに失敗しました。")
        return False
    
    # Agent統合テスト
    agent_ok = await test_agent_integration()
    if not agent_ok:
        print("❌ Agent統合テストに失敗しました。")
        return False
    
    # 異なるAgent設定テスト
    config_ok = await test_different_agent_configurations()
    if not config_ok:
        print("❌ Agent設定テストに失敗しました。")
        return False
    
    print("\n🎉 Phase 1 の全テストが正常に完了しました!")
    print("✅ MCPサーバ接続: OK")
    print("✅ 基本ツール: OK") 
    print("✅ Strands Agent統合: OK")
    print("✅ BedrockModel設定: OK")
    print("✅ タイムアウト設定: 適用済み")
    
    return True

if __name__ == "__main__":
    asyncio.run(run_all_tests())