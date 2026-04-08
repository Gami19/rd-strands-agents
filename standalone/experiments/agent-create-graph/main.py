import asyncio
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
import base64
import io
from strands import Agent
from strands.tools.mcp import MCPClient

# MCPサーバの初期化
server = Server("graph-visualization")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """利用可能なグラフ作成ツールのリスト"""
    return [
        Tool(
            name="create_matplotlib_chart",
            description="Matplotlibを使用してグラフを作成",
            inputSchema={
                "type": "object",
                "properties": {
                    "chart_type": {"type": "string", "enum": ["line", "bar", "scatter", "histogram"]},
                    "data": {"type": "object"},
                    "title": {"type": "string"},
                    "x_label": {"type": "string"},
                    "y_label": {"type": "string"}
                },
                "required": ["chart_type", "data"]
            }
        ),
        Tool(
            name="create_plotly_chart",
            description="Plotlyを使用してインタラクティブなグラフを作成",
            inputSchema={
                "type": "object", 
                "properties": {
                    "chart_type": {"type": "string", "enum": ["line", "bar", "scatter", "pie"]},
                    "data": {"type": "object"},
                    "title": {"type": "string"}
                },
                "required": ["chart_type", "data"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """ツール実行のハンドラ"""
    if name == "create_matplotlib_chart":
        return await create_matplotlib_chart(arguments)
    elif name == "create_plotly_chart":
        return await create_plotly_chart(arguments)

async def create_matplotlib_chart(args: dict) -> list[TextContent]:
    """Matplotlibでグラフを作成"""
    chart_type = args["chart_type"]
    data = args["data"]
    title = args.get("title", "Chart")
    x_label = args.get("x_label", "X")
    y_label = args.get("y_label", "Y")
    
    plt.figure(figsize=(10, 6))
    
    if chart_type == "line":
        plt.plot(data["x"], data["y"])
    elif chart_type == "bar":
        plt.bar(data["x"], data["y"])
    elif chart_type == "scatter":
        plt.scatter(data["x"], data["y"])
    elif chart_type == "histogram":
        plt.hist(data["values"], bins=data.get("bins", 20))
    
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.grid(True)
    
    # ファイルとして保存
    filename = f"chart_{chart_type}_{title.replace(' ', '_')}.png"
    plt.savefig(filename, format='png', bbox_inches='tight', dpi=300)
    
    # Base64エンコードも保持
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    return [TextContent(
        type="text",
        text=f"グラフが作成されました。\nファイル名: {filename}\ndata:image/png;base64,{image_base64}"
    )]

async def create_plotly_chart(args: dict) -> list[TextContent]:
    """Plotlyでインタラクティブなグラフを作成"""
    chart_type = args["chart_type"]
    data = args["data"]
    title = args.get("title", "Interactive Chart")
    
    if chart_type == "line":
        fig = go.Figure(data=go.Scatter(x=data["x"], y=data["y"], mode='lines'))
    elif chart_type == "bar":
        fig = go.Figure(data=go.Bar(x=data["x"], y=data["y"]))
    elif chart_type == "scatter":
        fig = go.Figure(data=go.Scatter(x=data["x"], y=data["y"], mode='markers'))
    elif chart_type == "pie":
        fig = go.Figure(data=go.Pie(labels=data["labels"], values=data["values"]))
    
    fig.update_layout(title=title)
    
    # HTMLファイルとして保存
    html_filename = f"chart_{chart_type}_{title.replace(' ', '_')}.html"
    fig.write_html(html_filename)
    
    # HTML文字列も保持
    html_str = fig.to_html(include_plotlyjs=True)
    
    return [TextContent(
        type="text", 
        text=f"インタラクティブなグラフが作成されました。\nHTMLファイル: {html_filename}\n{html_str}"
    )]

# テスト用の関数
async def test_server():
    """サーバーの機能をテスト"""
    print("MCPサーバーのテストを開始します...")
    
    # ツールリストの取得
    tools = await handle_list_tools()
    print(f"利用可能なツール数: {len(tools)}")
    for tool in tools:
        print(f"- {tool.name}: {tool.description}")
    
    # サンプルデータでグラフ作成をテスト
    test_data = {
        "chart_type": "bar",
        "data": {"x": ["1月", "2月", "3月", "4月", "5月"], "y": [100, 150, 200, 180, 220]},
        "title": "月別売上",
        "x_label": "月",
        "y_label": "売上"
    }
    
    print("\nMatplotlibチャートのテスト...")
    result = await create_matplotlib_chart(test_data)
    print(f"結果: {result[0].text[:100]}...")
    
    print("\nPlotlyチャートのテスト...")
    result = await create_plotly_chart(test_data)
    print(f"結果: {result[0].text[:100]}...")
    
    print("\nテスト完了！")

# サーバの起動（テストモード）
async def main():
    # テストモードで実行
    await test_server()
    
    print("\nMCPサーバーを起動します...")
    print("Ctrl+Cで終了できます")
    
    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream, 
                InitializationOptions(
                    server_name="graph-visualization",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(tools_changed=True),
                        experimental_capabilities={}
                    )
                )
            )
    except KeyboardInterrupt:
        print("\nサーバーを終了します...")
    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    asyncio.run(main())
