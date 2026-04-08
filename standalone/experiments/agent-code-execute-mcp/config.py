import os
from botocore.config import Config
from strands.models import BedrockModel
from dotenv import load_dotenv

load_dotenv()


# タイムアウト設定
UVICORN_TIMEOUT = 3600  # 1時間
MCP_SERVER_PORT = 8000
MCP_SERVER_HOST = "localhost"

def create_bedrock_model(
    model_id=os.getenv("BEDROCK_MODEL_ID"),
    region_name=os.getenv("AWS_DEFAULT_REGION")
):
    """プロダクション対応のBedrockModelを作成"""
    return BedrockModel(
        model_id=model_id,
        region_name=region_name,
        boto_client_config=Config(
            retries={
                'total_max_attempts': 100,
                'mode': 'standard'
            },
            connect_timeout=10,
            read_timeout=300,  # 5分
        ),
        temperature=0,
        top_p=0,
        streaming=True  # ストリーミング有効
    )

# uvicornタイムアウト設定
def setup_uvicorn_timeouts():
    """uvicornタイムアウト設定"""
    os.environ['UVICORN_TIMEOUT_KEEP_ALIVE'] = str(UVICORN_TIMEOUT)
    os.environ['UVICORN_TIMEOUT_GRACEFUL_SHUTDOWN'] = str(UVICORN_TIMEOUT)