import os
from dotenv import load_dotenv

# 環境変数のロード
load_dotenv()

class Config:
    """システム設定クラス"""
    
    # サーバー設定
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8002))
    
    # AWS設定
    AWS_REGION = os.getenv("AWS_REGION", "us-east-2")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_KEY")
    
    # MCP設定
    BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
    ARXIV_STORAGE_PATH = os.getenv("ARXIV_STORAGE_PATH")
    
    # エージェント設定
    AGENT_TIMEOUT = int(os.getenv("AGENT_TIMEOUT", 60))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
    
    # ログ設定
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @classmethod
    def validate(cls):
        """設定の検証"""
        required_vars = []
        
        if not cls.BRAVE_API_KEY:
            print("⚠️ Warning: BRAVE_API_KEY not set. Brave Search will not work.")
        
        if not cls.AWS_ACCESS_KEY_ID or not cls.AWS_SECRET_ACCESS_KEY:
            print("⚠️ Warning: AWS credentials not set. AWS services may not work.")
        
        return True