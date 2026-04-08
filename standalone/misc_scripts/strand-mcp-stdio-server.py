# stdioサーバーを直接実行する方法
# /mcp-server/mcpServer.pyを実行する
from mcp import stdio_client, StdioServerParameters
from strands import Agent
from strands.tools.mcp import MCPClient
import os


aws_docs_client = MCPClient(
    lambda: stdio_client(StdioServerParameters(
        command="python",
        args=["./samples/mcp-server/mcpServer.py"] 
    ))
)

# エージェントとツールを作成
with aws_docs_client:
    agent = Agent(tools=aws_docs_client.list_tools_sync())
    response = agent("Tell me about Amazon Bedrock and how to use it with Python")
    print(response)