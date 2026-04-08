import boto3
from dotenv import load_dotenv
import json
import os
load_dotenv()

def check_available_models():
    """利用可能なBedrockモデルを確認"""
    
    try:
        # Bedrockクライアント作成
        session = boto3.Session(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION")
        )
        
        bedrock_client = session.client('bedrock')
        
        print("🔄 利用可能なBedrockモデルを確認中...")
        print("=" * 60)
        
        # Foundation Modelsの一覧取得
        response = bedrock_client.list_foundation_models()
        
        available_models = []
        for model in response['modelSummaries']:
            model_id = model['modelId']
            model_name = model['modelName']
            provider = model['providerName']
            
            # アクセス可能かテスト
            access_status = check_model_access(session, model_id)
            
            model_info = {
                'model_id': model_id,
                'model_name': model_name,
                'provider': provider,
                'access': access_status
            }
            
            available_models.append(model_info)
            
            # 結果表示
            status_icon = "✅" if access_status == "利用可能" else "❌"
            print(f"{status_icon} {provider} - {model_name}")
            print(f"    Model ID: {model_id}")
            print(f"    Status: {access_status}")
            print()
        
        # 利用可能なモデルのみ表示
        available_only = [m for m in available_models if m['access'] == "利用可能"]
        
        print("=" * 60)
        print(f"📊 結果サマリー:")
        print(f"   総モデル数: {len(available_models)}")
        print(f"   利用可能: {len(available_only)}")
        print(f"   利用不可: {len(available_models) - len(available_only)}")
        
        if available_only:
            print(f"\n✅ 利用可能なモデル（.envで設定可能）:")
            for model in available_only:
                print(f"   BEDROCK_MODEL_ID={model['model_id']}")
        else:
            print(f"\n❌ 利用可能なモデルがありません")
            print(f"💡 AWS Bedrockコンソールでモデルアクセスを有効化してください")
            
    except Exception as e:
        print(f"❌ エラー: {e}")

def check_model_access(session, model_id):
    """個別モデルのアクセス確認"""
    try:
        bedrock_runtime = session.client('bedrock-runtime')
        
        # テスト用の最小リクエスト
        if "anthropic.claude" in model_id:
            test_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1,
                "messages": [{"role": "user", "content": "Hi"}]
            }
        elif "amazon.nova" in model_id:
            test_body = {
                "inputText": "Hi",
                "textGenerationConfig": {"maxTokenCount": 1}
            }
        elif "ai21" in model_id:
            test_body = {
                "prompt": "Hi",
                "maxTokens": 1
            }
        elif "cohere" in model_id:
            test_body = {
                "prompt": "Hi",
                "max_tokens": 1
            }
        elif "meta" in model_id:
            test_body = {
                "prompt": "Hi",
                "max_gen_len": 1
            }
        else:
            test_body = {
                "inputText": "Hi",
                "textGenerationConfig": {"maxTokenCount": 1}
            }
        
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(test_body),
            contentType='application/json',
            accept='application/json'
        )
        
        return "利用可能"
        
    except Exception as e:
        error_str = str(e)
        if "AccessDeniedException" in error_str:
            return "アクセス権限なし（要有効化）"
        elif "ValidationException" in error_str:
            if "on-demand throughput" in error_str:
                return "推論プロファイル必要"
            else:
                return "バリデーションエラー"
        elif "ThrottlingException" in error_str:
            return "API制限"
        else:
            return f"エラー: {error_str[:50]}..."

if __name__ == "__main__":
    check_available_models()