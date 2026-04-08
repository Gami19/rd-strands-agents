## グラフ作成MCPサーバ

|tool|機能|
|-----|----|
|create_matplotlib_chart|Matplotlibを使用した静的グラフ作成|
|create_plotly_chart|Plotlyを使用したインタラクティブグラフ作成|

## MCPツールの基本構造

```python
@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """利用可能なツールのリストを返す"""
    return [
        Tool(
            name="ツール名",
            description="ツールの説明",
            inputSchema={
                "type": "object",
                "properties": {
                    "パラメータ名": {"type": "パラメータの型"},
                    # その他のパラメータ...
                },
                "required": ["必須パラメータのリスト"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """ツール実行のハンドラ"""
    if name == "ツール名":
        return await ツール関数(arguments)
    # その他のツール...
```

## ツールの実装パターン
```python
# 1. ツール定義
@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [tool1, tool2, tool3]

# 2. ツール実行
@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    # ツールの振り分けと実行

# 3. 個別ツール関数
async def tool_function(args: dict) -> list[TextContent]:
    # 実際の処理
    return [TextContent(type="text", text="結果")]
```