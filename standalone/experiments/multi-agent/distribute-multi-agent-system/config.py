import os
from dotenv import load_dotenv

load_dotenv()

class Config:

    #AWS設定
    AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
    AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
    AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
    BEDROCK_KNOWLEDGE_BASE_ID = os.getenv("BEDROCK_KNOWLEDGE_BASE_ID")
    
    #Bedrockモデル設定
    RESEARCH_MODEL = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    CREATIVE_MODEL = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    CRITICAL_MODEL = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    PM_MODEL = "anthropic.claude-3-5-sonnet-20240620-v1:0"

    # arXiv MCP設定
    ARXIV_STORAGE_PATH = os.getenv("ARXIV_STORAGE_PATH")
    ARXIV_MAX_PAPERS = 3  # 最大3論文
    ARXIV_CONNECTION_RETRIES = 3
    ARXIV_CONNECTION_TIMEOUT = 30.0
    
    # システム設定
    PARALLEL_TIMEOUT = 180.0
    INTEGRATION_TIMEOUT = 120.0
    MAX_RETRIES = 2

    # エージェント判定設定
    AGENT_EVALUATION_TEMPERATURE = 0.2
    AGENT_EVALUATION_MAX_TOKENS = 500