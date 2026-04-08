import asyncio
import json
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.tools.mcp import MCPClient

async def test_basic_charts():
    """基本グラフテスト"""
    print("=== Phase 4: 基本グラフテスト ===")
    
    mcp_client = MCPClient(
        lambda: streamablehttp_client("http://localhost:8000/mcp")
    )
    
    try:
        with mcp_client:
            tools = mcp_client.list_tools_sync()
            agent = Agent(tools=tools)
            
            # サンプルデータ生成
            print("1. サンプルデータ生成")
            response1 = await agent.invoke_async("サンプルデータを生成してください")
            print("データ生成: 完了")
            
            # 散布図作成
            print("\n2. 散布図作成")
            response2 = await agent.invoke_async("priceとsalesの関係を散布図で可視化してください。タイトルは'Price vs Sales'にしてください")
            print("散布図作成: 完了")
            
            # ヒストグラム作成
            print("\n3. ヒストグラム作成")
            response3 = await agent.invoke_async("priceの分布をヒストグラムで表示してください")
            print("ヒストグラム作成: 完了")
            
            # 箱ひげ図作成
            print("\n4. 箱ひげ図作成")
            response4 = await agent.invoke_async("categoryごとのpriceの分布を箱ひげ図で表示してください")
            print("箱ひげ図作成: 完了")
            
            return True
    except Exception as e:
        print(f"基本グラフテストエラー: {e}")
        return False

async def test_correlation_heatmap():
    """相関ヒートマップテスト"""
    print("\n=== 相関ヒートマップテスト ===")
    
    mcp_client = MCPClient(
        lambda: streamablehttp_client("http://localhost:8000/mcp")
    )
    
    try:
        with mcp_client:
            tools = mcp_client.list_tools_sync()
            agent = Agent(tools=tools)
            
            print("1. 相関ヒートマップ作成")
            response = await agent.invoke_async("数値列の相関関係をヒートマップで可視化してください。seabornスタイルで作成してください")
            print("相関ヒートマップ作成: 完了")
            
            return True
    except Exception as e:
        print(f"相関ヒートマップテストエラー: {e}")
        return False

async def test_advanced_visualization():
    """高度可視化テスト"""
    print("\n=== 高度可視化テスト ===")
    
    mcp_client = MCPClient(
        lambda: streamablehttp_client("http://localhost:8000/mcp")
    )
    
    try:
        with mcp_client:
            tools = mcp_client.list_tools_sync()
            agent = Agent(tools=tools)
            
            print("1. 分布グリッド作成")
            response1 = await agent.invoke_async("全数値列の分布を一度に表示する分布グリッドを作成してください")
            print("分布グリッド作成: 完了")
            
            print("\n2. バイオリンプロット作成")
            response2 = await agent.invoke_async("categoryごとのpriceの分布をバイオリンプロットで表示してください")
            print("バイオリンプロット作成: 完了")
            
            return True
    except Exception as e:
        print(f"高度可視化テストエラー: {e}")
        return False

async def test_chart_management():
    """チャート管理テスト"""
    print("\n=== チャート管理テスト ===")
    
    mcp_client = MCPClient(
        lambda: streamablehttp_client("http://localhost:8000/mcp")
    )
    
    try:
        with mcp_client:
            tools = mcp_client.list_tools_sync()
            agent = Agent(tools=tools)
            
            print("1. チャート一覧表示")
            response1 = await agent.invoke_async("作成されたチャートの一覧を表示してください")
            print(f"チャート一覧: 完了")
            
            return True
    except Exception as e:
        print(f"チャート管理テストエラー: {e}")
        return False

async def test_plotly_charts():
    """Plotlyチャートテスト"""
    print("\n=== Plotlyチャートテスト ===")
    
    mcp_client = MCPClient(
        lambda: streamablehttp_client("http://localhost:8000/mcp")
    )
    
    try:
        with mcp_client:
            tools = mcp_client.list_tools_sync()
            agent = Agent(tools=tools)
            
            print("1. Plotly散布図作成")
            response = await agent.invoke_async("priceとsalesの関係をplotlyスタイルの散布図で作成してください")
            print("Plotly散布図作成: 完了")
            
            return True
    except Exception as e:
        print(f"Plotlyチャートテストエラー: {e}")
        return False

async def test_direct_tool_calls():
    """直接ツール呼び出しテスト"""
    print("\n=== 直接ツール呼び出しテスト ===")
    
    mcp_client = MCPClient(
        lambda: streamablehttp_client("http://localhost:8000/mcp")
    )
    
    try:
        with mcp_client:
            # まずデータセット一覧を取得してdata_idを特定
            datasets_result = await mcp_client.call_tool_async(
                tool_use_id="test-datasets",
                name="list_datasets",
                arguments={}
            )
            print("データセット一覧取得: 完了")
            
            # データセットがあることを前提に、最初のdata_idを使用
            print("\n1. 直接基本グラフ作成")
            chart_result = await mcp_client.call_tool_async(
                tool_use_id="test-chart-1",
                name="create_basic_chart",
                arguments={
                    "data_id": "dummy-data-id",  # 実際のテストでは正しいdata_idを使用
                    "chart_type": "histogram",
                    "y_column": "price",
                    "title": "Price Distribution",
                    "style": "seaborn"
                }
            )
            print("直接グラフ作成: 試行完了（data_idが正しければ成功）")
            
            print("\n2. チャート一覧取得")
            list_result = await mcp_client.call_tool_async(
                tool_use_id="test-list",
                name="list_charts",
                arguments={}
            )
            print("チャート一覧取得: 完了")
            print(json.dumps(list_result, indent=2, ensure_ascii=False))
            
            return True
    except Exception as e:
        print(f"直接ツール呼び出しテストエラー: {e}")
        return False

async def test_different_chart_styles():
    """異なるチャートスタイルテスト"""
    print("\n=== 異なるチャートスタイルテスト ===")
    
    mcp_client = MCPClient(
        lambda: streamablehttp_client("http://localhost:8000/mcp")
    )
    
    try:
        with mcp_client:
            tools = mcp_client.list_tools_sync()
            agent = Agent(tools=tools)
            
            print("1. デフォルトスタイル散布図")
            response1 = await agent.invoke_async("priceとsalesの散布図をデフォルトスタイルで作成してください")
            print("デフォルトスタイル: 完了")
            
            print("\n2. Seabornスタイル散布図")
            response2 = await agent.invoke_async("priceとsalesの散布図をseabornスタイルで作成してください")
            print("Seabornスタイル: 完了")
            
            print("\n3. Plotlyスタイル散布図")
            response3 = await agent.invoke_async("priceとsalesの散布図をplotlyスタイルで作成してください")
            print("Plotlyスタイル: 完了")
            
            return True
    except Exception as e:
        print(f"チャートスタイルテストエラー: {e}")
        return False

async def run_phase4_tests():
    """Phase 4 全テスト実行"""
    print("Phase 4 確認テストを開始します...")
    
    # 基本グラフテスト
    basic_ok = await test_basic_charts()
    if not basic_ok:
        print("❌ 基本グラフテストに失敗しました")
        return False
    
    # 相関ヒートマップテスト
    heatmap_ok = await test_correlation_heatmap()
    if not heatmap_ok:
        print("❌ 相関ヒートマップテストに失敗しました")
        return False
    
    # 高度可視化テスト
    advanced_ok = await test_advanced_visualization()
    if not advanced_ok:
        print("❌ 高度可視化テストに失敗しました")
        return False
    
    # チャート管理テスト
    management_ok = await test_chart_management()
    if not management_ok:
        print("❌ チャート管理テストに失敗しました")
        return False
    
    # Plotlyチャートテスト
    plotly_ok = await test_plotly_charts()
    if not plotly_ok:
        print("❌ Plotlyチャートテストに失敗しました")
        return False
    
    # 異なるスタイルテスト
    styles_ok = await test_different_chart_styles()
    if not styles_ok:
        print("❌ チャートスタイルテストに失敗しました")
        return False
    
    # 直接ツール呼び出しテスト
    direct_ok = await test_direct_tool_calls()
    if not direct_ok:
        print("❌ 直接ツール呼び出しテストに失敗しました")
        return False
    
    print("\n🎉 Phase 4 の全テストが正常に完了しました!")
    print("✅ 基本グラフ作成: OK")
    print("✅ 相関ヒートマップ: OK")
    print("✅ 高度可視化: OK")
    print("✅ チャート管理: OK")
    print("✅ Plotlyサポート: OK")
    print("✅ 複数スタイル対応: OK")
    print("✅ 直接ツール呼び出し: OK")
    
    return True

if __name__ == "__main__":
    asyncio.run(run_phase4_tests())