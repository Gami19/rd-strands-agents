# uvxを使わず、Pythonモジュールを直接実行する方法
from mcp import StdioServerParameters, stdio_client
from strands import Agent
from strands.tools.mcp import MCPClient

stdio_mcp_client = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(
            command="python",
            args=["-m", "awslabs.aws_documentation_mcp_server.server"]
        )
    )
)

# エージェントとツールを作成
with stdio_mcp_client:
    # MCPサーバーからツール一覧を取得
    tools = stdio_mcp_client.list_tools_sync()
    
    # ツールを持つエージェントを作成
    agent = Agent(tools=tools)
    
    # プロンプトを実行
    response = agent("Tell me about Amazon Bedrock and how to use it with Python")
    print(response)