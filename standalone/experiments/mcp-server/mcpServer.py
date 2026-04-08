# aws_documentation_server.py
from mcp.server import FastMCP
import boto3
import sys
import json

# MCPサーバー作成
mcp = FastMCP("mcp server")

# AWSのクライアント初期化
session = boto3.Session()

@mcp.tool(description="Search AWS documentation for information")
def search_aws_docs(query: str) -> str:
    return f"Here is information about {query} from AWS documentation..."

# 標準入出力でMCPサーバーを実行
if __name__ == "__main__":
    mcp.run(transport="stdio")