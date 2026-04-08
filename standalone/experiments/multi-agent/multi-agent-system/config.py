# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # AWS設定
    AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
    AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
    AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
    
    # Bedrockモデル設定
    ROUTER_MODEL = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    FAQ_MODEL = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    EXPERT_MODEL = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    GENERAL_MODEL = "anthropic.claude-3-haiku-20240307-v1:0"
    
    # Knowledge Base設定
    BEDROCK_KNOWLEDGE_BASE_ID = os.getenv("BEDROCK_KNOWLEDGE_BASE_ID")
    
    # A2Aサーバー設定
    A2A_ROUTER_PORT = 9001
    A2A_FAQ_PORT = 9002
    A2A_EXPERT_PORT = 9003
    A2A_GENERAL_PORT = 9004
    A2A_WORKFLOW_PORT = 9005
    
    # システム設定
    MAX_HANDOFFS = 5
    MAX_ITERATIONS = 8
    EXECUTION_TIMEOUT = 600.0  # 10分
    NODE_TIMEOUT = 120.0       # 2分
    
    # A2A設定
    A2A_ENABLED = True
    A2A_DISCOVERY_ENABLED = True
    A2A_TIMEOUT = 300  # 5分