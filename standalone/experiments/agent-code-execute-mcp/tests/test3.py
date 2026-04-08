import asyncio
import json
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.tools.mcp import MCPClient

async def test_basic_statistics():
    """基本統計量テスト"""
    print("=== Phase 3: 基本統計量テスト ===")
    
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
            print(f"データ生成: 完了")
            
            # 基本統計量計算
            print("\n2. 基本統計量計算")
            response2 = await agent.invoke_async("生成されたサンプルデータの基本統計量を計算してください")
            print(f"基本統計量: {response2}")
            
            return True
    except Exception as e:
        print(f"基本統計量テストエラー: {e}")
        return False

async def test_correlation_analysis():
    """相関分析テスト"""
    print("\n=== 相関分析テスト ===")
    
    mcp_client = MCPClient(
        lambda: streamablehttp_client("http://localhost:8000/mcp")
    )
    
    try:
        with mcp_client:
            tools = mcp_client.list_tools_sync()
            agent = Agent(tools=tools)
            
            print("1. 相関分析実行")
            response = await agent.invoke_async("サンプルデータの数値列間の相関分析を実行してください。pearson法を使用してください。")
            print(f"相関分析結果: {response}")
            
            return True
    except Exception as e:
        print(f"相関分析テストエラー: {e}")
        return False

async def test_outlier_detection():
    """外れ値検出テスト"""
    print("\n=== 外れ値検出テスト ===")
    
    mcp_client = MCPClient(
        lambda: streamablehttp_client("http://localhost:8000/mcp")
    )
    
    try:
        with mcp_client:
            tools = mcp_client.list_tools_sync()
            agent = Agent(tools=tools)
            
            print("1. 外れ値検出実行")
            response = await agent.invoke_async("サンプルデータの外れ値を検出してください。IQR法を使用してください。")
            print(f"外れ値検出結果: {response}")
            
            return True
    except Exception as e:
        print(f"外れ値検出テストエラー: {e}")
        return False

async def test_distribution_analysis():
    """分布分析テスト"""
    print("\n=== 分布分析テスト ===")
    
    mcp_client = MCPClient(
        lambda: streamablehttp_client("http://localhost:8000/mcp")
    )
    
    try:
        with mcp_client:
            tools = mcp_client.list_tools_sync()
            agent = Agent(tools=tools)
            
            print("1. 分布分析実行")
            response = await agent.invoke_async("サンプルデータの'price'カラムの分布分析を実行してください")
            print(f"分布分析結果: {response}")
            
            return True
    except Exception as e:
        print(f"分布分析テストエラー: {e}")
        return False

async def test_statistical_tests():
    """統計的検定テスト"""
    print("\n=== 統計的検定テスト ===")
    
    mcp_client = MCPClient(
        lambda: streamablehttp_client("http://localhost:8000/mcp")
    )
    
    try:
        with mcp_client:
            tools = mcp_client.list_tools_sync()
            agent = Agent(tools=tools)
            
            print("1. t検定実行")
            response = await agent.invoke_async("サンプルデータでcategoryがAとBのグループ間でpriceに有意差があるかt検定を実行してください")
            print(f"t検定結果: {response}")
            
            return True
    except Exception as e:
        print(f"統計的検定テストエラー: {e}")
        return False

async def run_phase3_tests():
    """Phase 3 全テスト実行"""
    print("Phase 3 確認テストを開始します...")
    
    # 基本統計量テスト
    stats_ok = await test_basic_statistics()
    if not stats_ok:
        print("❌ 基本統計量テストに失敗しました")
        return False
    
    # 相関分析テスト
    corr_ok = await test_correlation_analysis()
    if not corr_ok:
        print("❌ 相関分析テストに失敗しました")
        return False
    
    # 外れ値検出テスト
    outlier_ok = await test_outlier_detection()
    if not outlier_ok:
        print("❌ 外れ値検出テストに失敗しました")
        return False
    
    # 分布分析テスト
    dist_ok = await test_distribution_analysis()
    if not dist_ok:
        print("❌ 分布分析テストに失敗しました")
        return False
    
    # 統計的検定テスト
    test_ok = await test_statistical_tests()
    if not test_ok:
        print("❌ 統計的検定テストに失敗しました")
        return False
    
    print("\n🎉 Phase 3 の全テストが正常に完了しました!")
    print("✅ 基本統計量: OK")
    print("✅ 相関分析: OK")
    print("✅ 外れ値検出: OK")
    print("✅ 分布分析: OK")
    print("✅ 統計的検定: OK")
    
    return True

if __name__ == "__main__":
    asyncio.run(run_phase3_tests())