import asyncio
import json
import base64
import pandas as pd
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.tools.mcp import MCPClient

def create_test_csv():
    """テスト用CSVデータを作成"""
    # 配列の長さを統一
    num_rows = 20
    data = {
        'id': list(range(1, num_rows + 1)),
        'name': [f'Product_{i}' for i in range(1, num_rows + 1)],
        'price': [100 + i * 10 for i in range(num_rows)],
        'sales': [50 + i * 5 for i in range(num_rows)],
        'category': (['A', 'B', 'C'] * (num_rows // 3 + 1))[:num_rows],  # 長さを調整
        'date': pd.date_range('2024-01-01', periods=num_rows).strftime('%Y-%m-%d').tolist()
    }
    
    # 長さチェック（デバッグ用）
    for key, value in data.items():
        print(f"{key}: {len(value)}")
    
    df = pd.DataFrame(data)
    csv_content = df.to_csv(index=False)
    return base64.b64encode(csv_content.encode()).decode()

async def test_data_loading():
    """データ読み込みテスト"""
    print("=== Phase 2: データ読み込みテスト ===")
    
    mcp_client = MCPClient(
        lambda: streamablehttp_client("http://localhost:8000/mcp")
    )
    
    try:
        with mcp_client:
            tools = mcp_client.list_tools_sync()
            agent = Agent(tools=tools)
            
            # テスト用CSVデータ作成
            print("テスト用CSVデータ作成中...")
            test_csv_data = create_test_csv()
            print(f"CSVデータ作成完了（サイズ: {len(test_csv_data)} 文字）")
            
            # 直接MCPツールを呼び出してテスト
            print("\n1. 直接load_datasetツール呼び出し")
            result = await mcp_client.call_tool_async(
                tool_use_id="test-load-1",
                name="load_dataset",
                arguments={
                    "file_data": test_csv_data,
                    "file_type": "csv",
                    "filename": "test_products.csv",
                    "encoding": "utf-8"
                }
            )
            print("ツール実行結果:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # Agentを使った自然言語でのテスト
            print("\n2. Agent経由でのデータ読み込み")
            response = await agent.invoke_async(
                "load_sample_dataツールを使ってサンプルデータを生成し、その後list_datasetsで一覧を確認してください"
            )
            print(f"Agent Response: {response}")
            
            return True
    except Exception as e:
        print(f"データ読み込みテストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_dataset_info():
    """データセット情報取得テスト"""
    print("\n=== データセット情報取得テスト ===")
    
    mcp_client = MCPClient(
        lambda: streamablehttp_client("http://localhost:8000/mcp")
    )
    
    try:
        with mcp_client:
            tools = mcp_client.list_tools_sync()
            agent = Agent(tools=tools)
            
            # まずサンプルデータを生成
            print("1. サンプルデータ生成")
            response1 = await agent.invoke_async("サンプルデータを生成してください")
            print(f"サンプルデータ生成: {response1}")
            
            # データセット一覧を取得
            print("\n2. データセット一覧取得")
            response2 = await agent.invoke_async("現在読み込まれているデータセットの一覧を表示してください")
            print(f"データセット一覧: {response2}")
            
            return True
    except Exception as e:
        print(f"データセット情報テストエラー: {e}")
        return False

async def test_resume_functionality():
    """Resume機能テスト"""
    print("\n=== Resume機能テスト ===")
    
    mcp_client = MCPClient(
        lambda: streamablehttp_client("http://localhost:8000/mcp")
    )
    
    try:
        with mcp_client:
            tools = mcp_client.list_tools_sync()
            agent = Agent(tools=tools)
            
            # 処理状態保存テスト
            print("1. 処理状態保存テスト")
            
            # 直接ツール呼び出し
            result1 = await mcp_client.call_tool_async(
                tool_use_id="test-save-state",
                name="save_processing_state",
                arguments={
                    "data_id": "test-data-001",
                    "operation": "correlation_analysis",
                    "parameters": json.dumps({"method": "pearson"}),
                    "checkpoint_data": "test checkpoint data"
                }
            )
            print("処理状態保存結果:")
            print(json.dumps(result1, indent=2, ensure_ascii=False))
            
            # 処理状態一覧確認
            print("\n2. 処理状態一覧確認")
            result2 = await mcp_client.call_tool_async(
                tool_use_id="test-list-states",
                name="list_processing_states",
                arguments={}
            )
            print("処理状態一覧:")
            print(json.dumps(result2, indent=2, ensure_ascii=False))
            
            return True
    except Exception as e:
        print(f"Resume機能テストエラー: {e}")
        return False

async def test_available_tools():
    """利用可能ツール確認"""
    print("=== 利用可能ツール確認 ===")
    
    mcp_client = MCPClient(
        lambda: streamablehttp_client("http://localhost:8000/mcp")
    )
    
    try:
        with mcp_client:
            tools = mcp_client.list_tools_sync()
            print(f"利用可能なツール数: {len(tools)}")
            
            # ツールオブジェクトの詳細情報を表示
            for i, tool in enumerate(tools):
                print(f"\nツール {i+1}:")
                print(f"  型: {type(tool)}")
                print(f"  文字列表現: {tool}")
                
                # 安全な属性アクセス
                try:
                    tool_name = getattr(tool, 'name', f'Tool_{i+1}')
                    print(f"  名前: {tool_name}")
                except:
                    print(f"  名前: 取得不可")
                
                try:
                    tool_description = getattr(tool, 'description', '説明なし')
                    print(f"  説明: {tool_description}")
                except:
                    print(f"  説明: 説明なし")
                
                # 利用可能な属性を表示
                try:
                    attrs = [attr for attr in dir(tool) if not attr.startswith('_')]
                    print(f"  利用可能な属性: {attrs[:10]}...")  # 最初の10個のみ表示
                except:
                    print(f"  属性情報: 取得不可")
            
            return True
    except Exception as e:
        print(f"ツール確認エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

async def run_phase2_tests():
    """Phase 2 全テスト実行"""
    print("Phase 2 確認テストを開始します...")
    
    # 利用可能ツール確認
    print("0. 利用可能ツール確認")
    tools_ok = await test_available_tools()
    if not tools_ok:
        print("❌ ツール確認に失敗しました")
        return False
    
    # データ読み込みテスト
    loading_ok = await test_data_loading()
    if not loading_ok:
        print("❌ データ読み込みテストに失敗しました")
        return False
    
    # データセット情報テスト
    info_ok = await test_dataset_info()
    if not info_ok:
        print("❌ データセット情報テストに失敗しました")
        return False
    
    # Resume機能テスト
    resume_ok = await test_resume_functionality()
    if not resume_ok:
        print("❌ Resume機能テストに失敗しました")
        return False
    
    print("\n🎉 Phase 2 の全テストが正常に完了しました!")
    print("✅ ツール確認: OK")
    print("✅ データ読み込み機能: OK")
    print("✅ データセット情報取得: OK")
    print("✅ Resume機能: OK") 
    
    return True

if __name__ == "__main__":
    asyncio.run(run_phase2_tests())