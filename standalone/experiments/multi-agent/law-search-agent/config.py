import os
from typing import Optional
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

class Config:
    """環境変数の管理"""
    
    # AWS設定
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_KEY", "")
    AWS_DEFAULT_REGION: str = os.getenv("AWS_DEFAULT_REGION", "us-east-2")
    
    # Bedrock設定
    BEDROCK_MODEL_ID: str = os.getenv("BEDROCK_MODEL_ID")
    
    # API設定
    LAWS_API_BASE_URL: str = os.getenv("LAWS_API_BASE_URL", "https://laws.e-gov.go.jp/api/2")
    
    # アプリケーション設定
    MAX_SEARCH_RESULTS: int = int(os.getenv("MAX_SEARCH_RESULTS", "5"))
    MAX_LAW_TEXT_LENGTH: int = int(os.getenv("MAX_LAW_TEXT_LENGTH", "3000"))
    
    # デバッグ設定
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls) -> bool:
        """必須環境変数の検証"""
        required_vars = [
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ 以下の環境変数が設定されていません: {', '.join(missing_vars)}")
            print("💡 .envファイルに設定してください")
            return False
        
        return True
    
    @classmethod
    def print_config(cls):
        """設定内容の表示（機密情報は隠す）"""
        print("📋 現在の設定:")
        print(f"   AWS Region: {cls.AWS_DEFAULT_REGION}")
        print(f"   Bedrock Model: {cls.BEDROCK_MODEL_ID}")
        print(f"   Max Results: {cls.MAX_SEARCH_RESULTS}")
        print(f"   Debug Mode: {cls.DEBUG}")
        
        # AWS認証情報は一部のみ表示
        if cls.AWS_ACCESS_KEY_ID:
            masked_key = cls.AWS_ACCESS_KEY_ID[:4] + "*" * (len(cls.AWS_ACCESS_KEY_ID) - 4)
            print(f"   AWS Access Key: {masked_key}")

# 設定インスタンス
config = Config()